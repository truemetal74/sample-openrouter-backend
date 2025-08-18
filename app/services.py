import uuid
import logging
from typing import Dict, Any, Optional
from app.models import LLMRequest, LLMResponse, PromptName
from app.prompts import PromptManager
from app.openrouter_client import OpenRouterClient
from app.exceptions import PromptError, OpenRouterError
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for handling LLM interactions via OpenRouter."""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
    
    async def process_request(self, request: LLMRequest, user_id: str) -> LLMResponse:
        """
        Process an LLM request and return the response.
        
        Args:
            request: LLM request object
            user_id: ID of the requesting user
            
        Returns:
            LLMResponse object
            
        Raises:
            PromptError: For prompt-related errors
            OpenRouterError: For OpenRouter API errors
        """
        request_id = str(uuid.uuid4())
        logger.info(f"Processing LLM request {request_id} for user {user_id}")
        
        try:
            # Determine the prompt to use
            if request.prompt_name:
                # Use server-stored prompt template
                prompt = self._get_stored_prompt(request.prompt_name, request.data)
            else:
                # Use direct prompt text with variable substitution
                prompt = self._format_direct_prompt(request.prompt_text, request.data)
            
            if not prompt:
                raise PromptError("No prompt available for processing")
            
            # Get model to use
            model = request.model or settings.OPENROUTER_MODELS[0]
            
            # Send request to OpenRouter
            response = await self._call_openrouter(prompt, model, request_id)
            
            # Extract token usage information
            tokens_used = None
            if response.usage:
                tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # Extract response text
            response_text = ""
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                if "message" in choice and "content" in choice["message"]:
                    response_text = choice["message"]["content"]
            
            logger.info(f"Successfully processed request {request_id} using model {model}")
            
            return LLMResponse(
                success=True,
                response=response_text,
                model_used=model,
                tokens_used=tokens_used,
                request_id=request_id
            )
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}")
            
            if isinstance(e, (PromptError, OpenRouterError)):
                raise
            
            # Convert unexpected errors to generic error
            raise OpenRouterError(f"Request processing failed: {str(e)}")
    
    def _get_stored_prompt(self, prompt_name: PromptName, data: Dict[str, Any]) -> str:
        """
        Get and format a stored prompt template.
        
        Args:
            prompt_name: Name of the prompt template
            data: Variables for substitution
            
        Returns:
            Formatted prompt string
            
        Raises:
            PromptError: If prompt processing fails
        """
        try:
            # Validate that all required variables are provided
            self.prompt_manager.validate_prompt_data(prompt_name, data)
            
            # Get the formatted prompt
            return self.prompt_manager.get_prompt(prompt_name, data)
            
        except ValueError as e:
            raise PromptError(str(e))
        except Exception as e:
            raise PromptError(f"Failed to process prompt '{prompt_name}': {str(e)}")
    
    def _format_direct_prompt(self, prompt_text: str, data: Dict[str, Any]) -> str:
        """
        Format direct prompt text with variable substitution.
        
        Args:
            prompt_text: Direct prompt text that may contain variables
            data: Variables for substitution
            
        Returns:
            Formatted prompt string
            
        Raises:
            PromptError: If prompt formatting fails
        """
        try:
            if not data:
                return prompt_text
            
            # Use str.format() for variable substitution
            formatted_prompt = prompt_text.format(**data)
            logger.info(f"Successfully formatted direct prompt with data: {data}")
            return formatted_prompt
            
        except KeyError as e:
            missing_var = str(e).strip("'")
            error_msg = f"Missing required variable '{missing_var}' in direct prompt"
            logger.error(error_msg)
            raise PromptError(error_msg)
        except Exception as e:
            error_msg = f"Error formatting direct prompt: {str(e)}"
            logger.error(error_msg)
            raise PromptError(error_msg)
    
    async def _call_openrouter(self, prompt: str, model: str, request_id: str) -> Any:
        """
        Call OpenRouter API with the given prompt.
        
        Args:
            prompt: Formatted prompt text
            model: Model to use
            request_id: Request identifier for logging
            
        Returns:
            OpenRouter response object
            
        Raises:
            OpenRouterError: If the API call fails
        """
        try:
            async with OpenRouterClient() as client:
                messages = [{"role": "user", "content": prompt}]
                response = await client.chat_completion(messages, model=model)
                return response
                
        except Exception as e:
            logger.error(f"OpenRouter API call failed for request {request_id}: {str(e)}")
            if isinstance(e, OpenRouterError):
                raise
            raise OpenRouterError(f"OpenRouter API call failed: {str(e)}")
    
    def get_available_prompts(self) -> Dict[str, str]:
        """
        Get list of available prompt templates.
        
        Returns:
            Dictionary mapping prompt names to descriptions
        """
        return self.prompt_manager.list_available_prompts()
    
    def get_available_models(self) -> list:
        """
        Get list of available OpenRouter models.
        
        Returns:
            List of model names
        """
        return settings.OPENROUTER_MODELS
