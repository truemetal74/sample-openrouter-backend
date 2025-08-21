import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.exceptions import OpenRouterError, RetryExhaustedError
from app.models import OpenRouterResponse, TokenUsage
import time

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Async HTTP client for OpenRouter API with retry logic and rate limit handling."""
    
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay_base = settings.RETRY_DELAY_BASE
        
        # Persistent HTTP client
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                            "HTTP-Referer": "https://sample-openrouter-backend.app",
        "X-Title": settings.APP_NAME
                }
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make HTTP request with automatic retry logic and exponential backoff.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
            
        Raises:
            RetryExhaustedError: If max retries exceeded
            OpenRouterError: For other API errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                await self._ensure_client()
                response = await self.client.request(method, url, **kwargs)
                
                # Log the full response details for troubleshooting
                logger.info(f"OpenRouter API response - Status: {response.status_code}, "
                          f"Headers: {dict(response.headers)}, Attempt: {attempt + 1}")
                
                # Handle rate limiting (HTTP 429)
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay_base))
                        delay = retry_after * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited (429), retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        
                        # Log full response details for troubleshooting
                        try:
                            response_body = response.json()
                            logger.info(f"Rate limit response details: {response_body}")
                        except Exception:
                            logger.info(f"Rate limit response text: {response.text}")
                        
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Max retries exceeded for rate limiting
                        logger.error("Maximum retries exceeded for rate limiting")
                        raise RetryExhaustedError("Rate limit retries exhausted")
                
                # Handle other HTTP errors
                if response.status_code >= 400:
                    error_msg = f"OpenRouter API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data}"
                        logger.error(f"OpenRouter API error response: {error_data}")
                    except Exception:
                        error_msg += f" - {response.text}"
                        logger.error(f"OpenRouter API error text: {response.text}")
                    
                    raise OpenRouterError(error_msg, response.status_code)
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = OpenRouterError(f"Request timeout: {str(e)}", 408)
                logger.warning(f"Request timeout on attempt {attempt + 1}: {str(e)}")
            except httpx.RequestError as e:
                last_exception = OpenRouterError(f"Request error: {str(e)}", 500)
                logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
            except (OpenRouterError, RetryExhaustedError):
                # Re-raise these exceptions immediately
                raise
            except Exception as e:
                last_exception = OpenRouterError(f"Unexpected error: {str(e)}", 500)
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            
            # If we get here, we need to retry
            if attempt < self.max_retries:
                delay = self.retry_delay_base * (2 ** attempt)
                logger.info(f"Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})")
                await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception or OpenRouterError("All retry attempts failed")
    
    async def chat_completion(self, messages: list, model: Optional[str] = None, **kwargs) -> OpenRouterResponse:
        """
        Send chat completion request to OpenRouter.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (optional, will use first configured model if not specified)
            **kwargs: Additional parameters for the API call
            
        Returns:
            OpenRouterResponse object
            
        Raises:
            OpenRouterError: For API errors
        """
        if not model:
            model = settings.OPENROUTER_MODELS[0]
        
        if model not in settings.OPENROUTER_MODELS:
            raise OpenRouterError(f"Model {model} not in configured models: {settings.OPENROUTER_MODELS}")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        logger.info(f"Sending chat completion request to model {model}")
        
        try:
            response = await self._make_request_with_retry("POST", url, json=payload)
            response_data = response.json()
            
            # Parse and validate response
            openrouter_response = OpenRouterResponse(**response_data)
            
            # Log token usage for monitoring
            if openrouter_response.usage:
                logger.info(f"Token usage - Prompt: {openrouter_response.usage.prompt_tokens}, "
                          f"Completion: {openrouter_response.usage.completion_tokens}, "
                          f"Total: {openrouter_response.usage.total_tokens}")
            
            return openrouter_response
            
        except Exception as e:
            if isinstance(e, (OpenRouterError, RetryExhaustedError)):
                raise
            logger.error(f"Error in chat completion: {str(e)}")
            raise OpenRouterError(f"Chat completion failed: {str(e)}")
    
    async def get_models(self) -> list:
        """
        Get available models from OpenRouter.
        
        Returns:
            List of available models
            
        Raises:
            OpenRouterError: For API errors
        """
        url = f"{self.base_url}/models"
        
        try:
            response = await self._make_request_with_retry("GET", url)
            return response.json()
        except Exception as e:
            if isinstance(e, (OpenRouterError, RetryExhaustedError)):
                raise
            logger.error(f"Error getting models: {str(e)}")
            raise OpenRouterError(f"Failed to get models: {str(e)}")
