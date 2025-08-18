from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """Base exception class for the application."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAppException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(BaseAppException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(BaseAppException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class RateLimitError(BaseAppException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details)


class OpenRouterError(BaseAppException):
    """Exception for OpenRouter API errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, details)


class PromptError(BaseAppException):
    """Exception for prompt-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class RetryExhaustedError(BaseAppException):
    """Exception for when retry attempts are exhausted."""
    
    def __init__(self, message: str = "Maximum retry attempts exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)
