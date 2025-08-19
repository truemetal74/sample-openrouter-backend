"""
Example custom route module for demonstration.

This module shows how to create custom routes that can be loaded dynamically
by the main application based on configuration.

To use this module, add it to your CUSTOM_ROUTES configuration:
- In .env file: CUSTOM_ROUTES=custom_routes_example
- Or in environment: CUSTOM_ROUTES=custom_routes_example
- Or as a list: CUSTOM_ROUTES=["custom_routes_example", "another_module"]
"""

from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
import logging

# Create a router instance
router = APIRouter(
    prefix="/custom",
    tags=["custom"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


def initialize(config):
    """
    Initialize the custom route module.
    
    This method is called automatically when the module is loaded.
    You can use it to set up any configuration, database connections, etc.
    
    Args:
        config: The application settings object
    """
    logger.info(f"Initializing custom routes module: {__name__}")
    # Add any initialization logic here
    # For example: database connections, external service setup, etc.
    
    # Example: Check if required config is available (without logging sensitive data)
    if hasattr(config, 'OPENROUTER_API_KEY') and config.OPENROUTER_API_KEY:
        logger.info("OpenRouter API key is configured")
    else:
        logger.warning("OpenRouter API key is not configured")
    
    if hasattr(config, 'CUSTOM_ROUTES'):
        logger.info(f"Custom routes enabled: {config.CUSTOM_ROUTES}")
    
    # Example: Safe configuration logging (if needed)
    # from app.config import get_safe_config_for_logging
    # safe_config = get_safe_config_for_logging()
    # logger.info(f"Module configuration: {safe_config}")


@router.get("/hello")
async def custom_hello():
    """Example custom endpoint."""
    return {"message": "Hello from custom routes!", "module": "custom_routes_example"}


@router.get("/user-info")
async def get_user_info(current_user: str = Depends(get_current_user)):
    """Example authenticated custom endpoint."""
    return {
        "message": "User info from custom routes",
        "user_id": current_user,
        "module": "custom_routes_example"
    }


@router.post("/custom-action")
async def custom_action(
    action: str,
    current_user: str = Depends(get_current_user)
):
    """Example custom action endpoint."""
    return {
        "message": f"Custom action '{action}' performed",
        "user_id": current_user,
        "module": "custom_routes_example",
        "status": "success"
    }


# You can add more routes here as needed
@router.get("/health")
async def custom_health():
    """Custom health check endpoint."""
    return {
        "status": "healthy",
        "module": "custom_routes_example",
        "endpoints": [
            "/custom/hello",
            "/custom/user-info", 
            "/custom/custom-action",
            "/custom/health"
        ]
    }
