from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


class AuthManager:
    """Manages JWT authentication and token generation."""
    
    ALGORITHM = "HS256"
    
    @classmethod
    def create_access_token(cls, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            user_id: User identifier
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        to_encode = {
            "user_id": user_id,
            "exp": expire
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=cls.ALGORITHM)
            logger.info(f"Created access token for user {user_id}, expires at {expire}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise AuthenticationError("Failed to create access token")
    
    @classmethod
    def verify_token(cls, token: str) -> dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])
            user_id: str = payload.get("user_id")
            
            if user_id is None:
                raise AuthenticationError("Invalid token payload")
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None or datetime.now(timezone.utc) > datetime.fromtimestamp(exp):
                raise AuthenticationError("Token has expired")
            
            logger.info(f"Successfully verified token for user {user_id}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            raise AuthenticationError("Token verification failed")
    
    @classmethod
    def get_user_id_from_token(cls, token: str) -> str:
        """
        Extract user ID from a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID string
            
        Raises:
            AuthenticationError: If token is invalid
        """
        payload = cls.verify_token(token)
        return payload["user_id"]


def get_current_user(token: str) -> str:
    """
    Get current user from authentication token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID string
        
    Raises:
        AuthenticationError: If authentication fails
    """
    if not token:
        raise AuthenticationError("No authentication token provided")
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    return AuthManager.get_user_id_from_token(token)


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
