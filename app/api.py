import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import LLMRequest, LLMResponse, AccessToken
from app.services import LLMService
from app.auth import AuthManager, get_current_user
from app.logging_middleware import extract_request_id
from app.prompts import PromptManager

from app.exceptions import (
    BaseAppException, ValidationError, AuthenticationError, 
    AuthorizationError, OpenRouterError, PromptError
)
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbose logging from HTTP libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Global service instance
llm_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with proper startup and shutdown."""
    global llm_service
    
    # Startup
    logger.info("Starting Sample OpenRouter Backend...")
    try:
        llm_service = LLMService()
        logger.info("LLM Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sample OpenRouter Backend...")
    try:
        if llm_service:
            # Clean up any resources if needed
            # Close any open HTTP clients
            if hasattr(llm_service, 'openrouter_client') and llm_service.openrouter_client:
                try:
                    await llm_service.openrouter_client.close()
                    logger.info("OpenRouter client closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing OpenRouter client: {e}")
            logger.info("LLM Service cleanup completed")
    except Exception as e:
        logger.error(f"Error during LLM Service cleanup: {e}")
    
    # Graceful shutdown - don't aggressively cancel all tasks
    logger.info("Sample OpenRouter Backend shutdown complete")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Sample OpenRouter Backend",
    description="FastAPI application for LLM interactions via OpenRouter",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Load custom route modules dynamically
def load_custom_routes():
    """Dynamically load custom route modules specified in configuration."""
    import importlib
    
    try:
        # Get routes from config - support both list and comma-separated string
        custom_routes = settings.CUSTOM_ROUTES
        if isinstance(custom_routes, str):
            custom_routes = [route.strip() for route in custom_routes.split(",") if route.strip()]
        
        if not custom_routes:
            logger.info("No custom routes configured")
            return
        
        logger.info(f"Loading custom route modules: {custom_routes}")
        
        loaded_modules = 0
        for route_name in custom_routes:
            route_name = route_name.strip()
            if not route_name:
                continue
                
            try:
                # Import the router module dynamically
                router_module = importlib.import_module(route_name)
                
                # Initialize the module if it has an initialize method
                if hasattr(router_module, "initialize"):
                    try:
                        logger.info(f"Initializing custom route module: {route_name}")
                        
                        # Pass the actual config to the module
                        router_module.initialize(settings)
                        logger.info(f"Initialized custom route module: {route_name}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize module {route_name}: {str(e)}")
                
                # Include the router if it exists
                if hasattr(router_module, 'router'):
                    app.include_router(router_module.router)
                    logger.info(f"Successfully loaded router from {route_name}")
                    loaded_modules += 1
                else:
                    logger.warning(f"Router module {route_name} does not contain a 'router' attribute")
                    
            except ImportError as e:
                logger.error(f"Failed to import router module {route_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error loading router from {route_name}: {str(e)}")
        
        logger.info(f"Custom routes loading completed. Successfully loaded {loaded_modules}/{len(custom_routes)} modules.")
                
    except Exception as e:
        logger.error(f"Unexpected error during custom routes loading: {str(e)}")
        # Don't fail the entire application startup if custom routes fail




# Load custom routes
try:
    load_custom_routes()
except Exception as e:
    logger.error(f"Critical error during custom routes loading: {str(e)}")
    logger.warning("Application will continue without custom routes")

# Log startup completion
logger.info("Application startup completed successfully")
logger.info("Available endpoints:")
logger.info("  - POST /ask-llm (LLM interactions)")
logger.info("  - POST /auth/token (Authentication)")
logger.info("  - GET /prompts (Prompt management)")
logger.info("  - GET /models (Available models)")
logger.info("  - GET /health (Health check)")
logger.info("  - GET / (Service information)")
logger.info("  - GET /docs (API documentation)")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Comprehensive logging middleware for all requests and responses."""
    from app.logging_middleware import extract_request_id
    
    # Extract or generate request ID
    request_id = extract_request_id(request)
    request.state.request_id = request_id
    
    # Log request details
    logger.info(f"[REQUEST] {request.method} {request.url.path} | "
               f"Request ID: {request_id} | "
               f"Client IP: {get_client_ip(request)} | "
               f"Headers: {get_loggable_headers(request)}")
    
    # Log request body if detailed logging is enabled
    if settings.ENABLE_DETAILED_LOGGING:
        try:
            req_body = await request.body()
            if req_body:
                content_type = request.headers.get('content-type', '').lower()
                if 'multipart/form-data' in content_type or 'application/octet-stream' in content_type:
                    req_body_text = "<binary data>"
                else:
                    req_body_text = req_body.decode("utf-8").replace("\n", " ")
                logger.info(f"[REQUEST BODY] {request_id} | {req_body_text}")
            else:
                logger.info(f"[REQUEST BODY] {request_id} | <empty>")
        except Exception as e:
            logger.warning(f"[REQUEST BODY] {request_id} | Error reading body: {e}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Log response details
        if settings.ENABLE_DETAILED_LOGGING:
            try:
                if hasattr(response, 'body'):
                    response_text = response.body.decode("utf-8").replace("\n", " ")
                    if len(response_text) > 500:
                        response_text = response_text[:500] + "... [truncated]"
                    logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | {response_text}")
                else:
                    logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | <no body>")
            except Exception as e:
                logger.warning(f"[RESPONSE] {request_id} | Status: {response.status_code} | Error logging response: {e}")
        else:
            logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code}")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        logger.error(f"[ERROR] {request_id} | Exception: {str(e)}")
        raise

def get_client_ip(request: Request) -> str:
    """Extract client IP from various headers."""
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        return client_ip.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_loggable_headers(request: Request) -> str:
    """Extract and format loggable headers."""
    headers_to_log = ['content-type', 'user-agent', 'accept', 'x-forwarded-for', 'host', 'referer']
    sensitive_headers = ['authorization', 'recaptcha-response']
    
    def obfuscate_string(s: str) -> str:
        if s is None or len(s) <= 13:
            return s
        return s[:10] + '***' + s[-3:]
    
    headers = []
    for header in headers_to_log:
        value = request.headers.get(header)
        if value:
            if header in sensitive_headers:
                value = obfuscate_string(value)
            headers.append(f"{header}: '{value}'")
    
    return " | ".join(headers) if headers else "No relevant headers"

# Security
security = HTTPBearer()










@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions."""
    request_id = extract_request_id(request)
    logger.error(f"Application exception: {exc.message}", extra={
        "request_id": request_id,
        "status_code": exc.status_code,
        "details": exc.details
    })
    
    return {
        "error": exc.message,
        "status_code": exc.status_code,
        "request_id": request_id,
        "details": exc.details
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = extract_request_id(request)
    logger.error(f"Unexpected exception: {str(exc)}", extra={
        "request_id": request_id,
        "exception_type": type(exc).__name__
    })
    
    return {
        "error": "Internal server error",
        "status_code": 500,
        "request_id": request_id
    }


async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user."""
    try:
        return get_current_user(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.post("/ask-llm", response_model=LLMResponse, tags=["llm"])
async def ask_llm(
    request: LLMRequest,
    current_user: str = Depends(get_current_user_dependency)
):
    """
    Main endpoint for LLM interactions.
    
    Accepts either a prompt_name (for server-stored templates) or prompt_text (for direct input).
    Supports variable substitution in prompts via the data parameter.
    """
    try:
        logger.info(f"Processing LLM request for user {current_user}")
        
        # Log full request details if debug level is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"LLM Request details: prompt_name={request.prompt_name}, "
                        f"prompt_text={request.prompt_text}, model={request.model}, "
                        f"data={request.data}")
        
        # Validate request
        if not request.prompt_name and not request.prompt_text:
            raise ValidationError("Either prompt_name or prompt_text must be provided")
        
        # Process the request
        response = await llm_service.process_request(request, current_user)
        
        # Log response details if debug level is enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"LLM Response: success={response.success}, "
                        f"model_used={response.model_used}, "
                        f"tokens_used={response.tokens_used}")
            if response.response:
                logger.debug(f"LLM Response text: {response.response[:500]}{'...' if len(response.response) > 500 else ''}")
        
        return response
        
    except (ValidationError, PromptError) as e:
        logger.warning(f"Validation error for user {current_user}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except OpenRouterError as e:
        logger.error(f"OpenRouter error for user {current_user}: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/auth/token", response_model=AccessToken, tags=["authentication"])
async def create_access_token(user_id: str):
    """
    Create a new access token for a user.
    Note: In production, this should be protected and only allow valid user creation.
    """
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Creating access token for user: {user_id}")
        
        token = AuthManager.create_access_token(user_id)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Token created successfully for user {user_id}, expires in {expires_in} seconds")
        
        return AccessToken(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in
        )
    except Exception as e:
        logger.error(f"Error creating token for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create access token")


@app.get("/prompts", tags=["prompts"])
async def list_prompts(current_user: str = Depends(get_current_user_dependency)):
    """Get list of available prompt templates."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Listing prompts for user: {current_user}")
        
        prompts = llm_service.get_available_prompts()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Available prompts: {prompts}")
        
        return {"prompts": prompts}
    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list prompts")


@app.get("/models", tags=["models"])
async def list_models(current_user: str = Depends(get_current_user_dependency)):
    """Get list of available OpenRouter models."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Listing models for user: {current_user}")
        
        models = llm_service.get_available_models()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Available models: {models}")
        
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@app.post("/prompts/add", tags=["prompts"])
async def add_prompt(
    prompt_name: str,
    prompt_template: str,
    description: str = None,
    current_user: str = Depends(get_current_user_dependency)
):
    """Add a new prompt template."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Adding prompt '{prompt_name}' for user: {current_user}")
        
        success = PromptManager.add_prompt(prompt_name, prompt_template, description)
        
        if success:
            logger.info(f"Prompt '{prompt_name}' added successfully by user: {current_user}")
            return {
                "success": True,
                "message": f"Prompt '{prompt_name}' added successfully",
                "prompt_name": prompt_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add prompt")
            
    except ValueError as e:
        logger.warning(f"Validation error adding prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add prompt")


@app.put("/prompts/update", tags=["prompts"])
async def update_prompt(
    prompt_name: str,
    new_template: str,
    new_description: str = None,
    current_user: str = Depends(get_current_user_dependency)
):
    """Update an existing prompt template."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Updating prompt '{prompt_name}' for user: {current_user}")
        
        success = PromptManager.update_prompt(prompt_name, new_template, new_description)
        
        if success:
            logger.info(f"Prompt '{prompt_name}' updated successfully by user: {current_user}")
            return {
                "success": True,
                "message": f"Prompt '{prompt_name}' updated successfully",
                "prompt_name": prompt_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update prompt")
            
    except ValueError as e:
        logger.warning(f"Validation error updating prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")


@app.delete("/prompts/remove", tags=["prompts"])
async def remove_prompt(
    prompt_name: str,
    current_user: str = Depends(get_current_user_dependency)
):
    """Remove a prompt template."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Removing prompt '{prompt_name}' for user: {current_user}")
        
        success = PromptManager.remove_prompt(prompt_name)
        
        if success:
            logger.info(f"Prompt '{prompt_name}' removed successfully by user: {current_user}")
            return {
                "success": True,
                "message": f"Prompt '{prompt_name}' removed successfully",
                "prompt_name": prompt_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to remove prompt")
            
    except ValueError as e:
        logger.warning(f"Validation error removing prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing prompt for user {current_user}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove prompt")


@app.get("/prompts/{prompt_name}/info", tags=["prompts"])
async def get_prompt_info(
    prompt_name: str,
    current_user: str = Depends(get_current_user_dependency)
):
    """Get detailed information about a specific prompt template."""
    try:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Getting info for prompt '{prompt_name}' for user: {current_user}")
        
        prompt_info = PromptManager.get_prompt_info(prompt_name)
        
        logger.info(f"Prompt info retrieved for '{prompt_name}' by user: {current_user}")
        return prompt_info
        
    except ValueError as e:
        logger.warning(f"Validation error getting prompt info for user {current_user}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting prompt info for user {current_user}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get prompt info")


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Sample OpenRouter Backend"}


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with service information."""
    # Get custom routes info
    custom_routes_info = {}
    if hasattr(settings, 'CUSTOM_ROUTES') and settings.CUSTOM_ROUTES:
        custom_routes = settings.CUSTOM_ROUTES
        if isinstance(custom_routes, str):
            custom_routes = [route.strip() for route in custom_routes.split(",") if route.strip()]
        custom_routes_info = {
            "enabled": True,
            "modules": custom_routes,
            "base_path": "/custom"  # This will vary based on your custom modules
        }
    else:
        custom_routes_info = {"enabled": False}
    
    return {
        "service": "Sample OpenRouter Backend",
        "version": "1.0.0",
        "endpoints": {
            "ask_llm": "/ask-llm",
            "auth": "/auth/token",
            "prompts": "/prompts",
            "prompt_management": {
                "add": "/prompts/add",
                "update": "/prompts/update", 
                "remove": "/prompts/remove",
                "info": "/prompts/{prompt_name}/info"
            },
            "models": "/models",
            "health": "/health"
        },
        "custom_routes": custom_routes_info
    }
