from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from app.config import settings
from app.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class BaseAuthManager:
    """Base authentication manager that doesn't issue tokens by default."""
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data dict if authentication succeeds, None otherwise
        """
        logger.warning("Base authentication manager - no actual authentication performed")
        return None
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new access token for a user.
        
        Args:
            user_id: User identifier
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        raise AuthenticationError("Token creation not supported by this authentication manager")


class DefaultAuthManager(BaseAuthManager):
    """Default authentication manager that doesn't issue tokens."""
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Default authentication - always fails.
        Override this in production with actual authentication logic.
        """
        logger.warning(f"Default auth manager rejecting login attempt for user: {username}")
        return None


class JWTTokenManager(BaseAuthManager):
    """JWT-based token manager for issuing and validating tokens."""
    
    ALGORITHM = "HS256"
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
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
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=self.ALGORITHM)
            logger.info(f"Created access token for user {user_id}, expires at {expire}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise AuthenticationError("Failed to create access token")
    
    def verify_token(self, token: str) -> dict:
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
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.ALGORITHM])
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
    
    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID from a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID string
            
        Raises:
            AuthenticationError: If token is invalid
        """
        payload = self.verify_token(token)
        return payload["user_id"]


# Factory function to get the configured authentication manager
def get_auth_manager() -> BaseAuthManager:
    """Get the configured authentication manager from settings."""
    auth_manager_class = getattr(settings, 'AUTH_MANAGER_CLASS', 'DefaultAuthManager')
    
    if auth_manager_class == 'JWTTokenManager':
        return JWTTokenManager()
    elif auth_manager_class == 'DefaultAuthManager':
        return DefaultAuthManager()
    else:
        # Try to import and instantiate a custom auth manager
        try:
            import importlib
            module_name, class_name = auth_manager_class.rsplit('.', 1)
            module = importlib.import_module(module_name)
            auth_class = getattr(module, class_name)
            return auth_class()
        except Exception as e:
            logger.warning(f"Failed to load custom auth manager {auth_manager_class}: {e}")
            logger.info("Falling back to DefaultAuthManager")
            return DefaultAuthManager()


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
    
    auth_manager = get_auth_manager()
    if not hasattr(auth_manager, 'get_user_id_from_token'):
        raise AuthenticationError("Current authentication manager doesn't support token validation")
    
    return auth_manager.get_user_id_from_token(token)


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


async def authenticate_user_oauth2(username: str = Form(...), password: str = Form(...)):
    """
    OAuth2.0 compatible user authentication.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        User data if authentication succeeds
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_manager = get_auth_manager()
    
    # Authenticate user
    user_data = auth_manager.authenticate_user(username, password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if token creation is supported
    if not hasattr(auth_manager, 'create_access_token'):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Token creation not supported by current authentication manager"
        )
    
    # Create access token
    try:
        user_id = user_data.get('id') or user_data.get('user_id') or username
        access_token = auth_manager.create_access_token(user_id)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        logger.info(f"User {username} authenticated successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user_id": user_id,
            "user_data": user_data
        }
        
    except Exception as e:
        logger.error(f"Error creating token for user {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access token"
        )
