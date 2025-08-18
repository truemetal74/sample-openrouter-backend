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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
