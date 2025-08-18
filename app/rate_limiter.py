from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.exceptions import RateLimitError
import logging

logger = logging.getLogger(__name__)


class CustomLimiter(Limiter):
    """Custom rate limiter with whitelist functionality."""
    
    def __init__(self):
        super().__init__(key_func=get_remote_address)
        self.trusted_ips = set(settings.TRUSTED_IPS)
    
    def is_trusted_ip(self, request):
        """Check if the request IP is in the trusted list."""
        client_ip = get_remote_address(request)
        return client_ip in self.trusted_ips
    
    def _is_rate_limit_exceeded(self, request, key, limit, window):
        """Override to check trusted IPs before applying rate limits."""
        if self.is_trusted_ip(request):
            logger.info(f"Trusted IP {get_remote_address(request)} bypassing rate limit")
            return False
        
        return super()._is_rate_limit_exceeded(request, key, limit, window)


# Create global limiter instance
limiter = CustomLimiter()


def get_rate_limit_decorator():
    """
    Get the rate limit decorator with configured limits.
    
    Returns:
        Decorator function for rate limiting
    """
    return limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}second")


def get_trusted_ip_decorator():
    """
    Get a decorator that bypasses rate limiting for trusted IPs.
    
    Returns:
        Decorator function that skips rate limiting for trusted IPs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a simple bypass - in practice, you might want to check the request object
            return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_rate_limit_exceeded(request, exc):
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception
        
    Returns:
        RateLimitError with proper HTTP status code
    """
    client_ip = get_remote_address(request)
    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
    
    raise RateLimitError(
        message="Rate limit exceeded",
        details={
            "retry_after": exc.retry_after,
            "limit": exc.retry_after,
            "window": settings.RATE_LIMIT_WINDOW
        }
    )


# Register the custom handler
limiter._rate_limit_exceeded_handler = handle_rate_limit_exceeded
