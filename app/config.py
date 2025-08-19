from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = Field(..., description="OpenRouter API key")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter API base URL")
    OPENROUTER_MODELS: List[str] = Field(
        default=["openai/gpt-4", "openai/gpt-3.5-turbo", "anthropic/claude-3-opus"],
        description="List of available OpenRouter models"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=10, description="Number of requests allowed per time window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Time window in seconds for rate limiting")
    MAX_RETRIES: int = Field(default=3, description="Maximum number of retries for failed requests")
    RETRY_DELAY_BASE: float = Field(default=1.0, description="Base delay for exponential backoff in seconds")
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration time in minutes")
    
    # HTTP Client
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_DETAILED_LOGGING: bool = Field(default=True, description="Enable detailed request/response logging")
    LOG_TEXT_TRUNCATE_LENGTH: int = Field(default=500, description="Maximum length of text to log before truncating with '...'")
    
    # Trusted IPs for rate limiting whitelist
    TRUSTED_IPS: List[str] = Field(default=[], description="List of trusted IP addresses to bypass rate limiting")
    
    # CORS Configuration
    CORS_ALLOW_ORIGINS: List[str] = Field(
        default=["*"], 
        description="List of allowed origins for CORS (use ['*'] for all origins)"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True, 
        description="Whether to allow credentials in CORS requests"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["*"], 
        description="List of allowed HTTP methods for CORS (use ['*'] for all methods)"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"], 
        description="List of allowed headers for CORS (use ['*'] for all headers)"
    )
    
    # Custom Routes Configuration
    CUSTOM_ROUTES: List[str] = Field(
        default=[], 
        description="List of additional route modules to load dynamically"
    )
    
    # Authentication Manager Configuration
    AUTH_MANAGER_CLASS: str = Field(
        default="DefaultAuthManager",
        description="Authentication manager class to use. Options: DefaultAuthManager, JWTTokenManager, or custom.module.ClassName"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_safe_config_for_logging():
    """
    Get a sanitized version of configuration for logging purposes.
    
    Returns:
        dict: Configuration with sensitive values masked
    """
    # Define sensitive fields that should be masked
    sensitive_fields = {
        'OPENROUTER_API_KEY', 'SECRET_KEY', 'API_KEY', 'PASSWORD', 
        'TOKEN', 'SECRET', 'PRIVATE_KEY', 'CREDENTIALS'
    }
    
    safe_config = {}
    
    # Get all config attributes
    for attr_name in dir(settings):
        # Skip private attributes and methods
        if attr_name.startswith('_') or callable(getattr(settings, attr_name)):
            continue
            
        attr_value = getattr(settings, attr_name)
        
        # Check if this field contains sensitive data
        is_sensitive = any(sensitive_field in attr_name.upper() for sensitive_field in sensitive_fields)
        
        if is_sensitive and attr_value:
            # Mask sensitive values
            if isinstance(attr_value, str):
                if len(attr_value) <= 8:
                    safe_config[attr_name] = '***'
                else:
                    safe_config[attr_name] = attr_value[:4] + '***' + attr_value[-4:]
            else:
                safe_config[attr_name] = '***'
        else:
            # Keep non-sensitive values as-is
            safe_config[attr_name] = attr_value
    
    return safe_config
