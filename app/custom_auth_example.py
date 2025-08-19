"""
Example custom authentication manager for demonstration.

This module shows how to create a custom authentication manager that can be
configured via the AUTH_MANAGER_CLASS setting.

To use this module, set in your .env file:
AUTH_MANAGER_CLASS=app.custom_auth_example.CustomAuthManager
"""

import logging
from typing import Optional, Dict, Any
from app.auth import BaseAuthManager
from app.config import settings

logger = logging.getLogger(__name__)


class CustomAuthManager(BaseAuthManager):
    """
    Example custom authentication manager.
    
    This is a demonstration of how to implement a custom authentication manager.
    In production, you would implement actual user authentication logic here.
    """
    
    def __init__(self):
        """Initialize the custom auth manager."""
        # Example: Load users from configuration or database
        # In production, this would typically connect to a user database
        self.users = {
            "admin": {
                "password": "admin123",  # In production, use hashed passwords!
                "id": "admin_001",
                "role": "admin",
                "email": "admin@example.com"
            },
            "user": {
                "password": "user123",
                "id": "user_001", 
                "role": "user",
                "email": "user@example.com"
            }
        }
        logger.info("Custom authentication manager initialized")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data dict if authentication succeeds, None otherwise
        """
        logger.info(f"Authenticating user: {username}")
        
        # Check if user exists
        if username not in self.users:
            logger.warning(f"User not found: {username}")
            return None
        
        user_data = self.users[username]
        
        # Check password (in production, use proper password hashing!)
        if user_data["password"] != password:
            logger.warning(f"Invalid password for user: {username}")
            return None
        
        # Authentication successful
        logger.info(f"User {username} authenticated successfully")
        
        # Return user data (excluding password)
        return {
            "id": user_data["id"],
            "username": username,
            "role": user_data["role"],
            "email": user_data["email"]
        }
    
    def create_access_token(self, user_id: str, expires_delta=None):
        """
        Create a new access token for a user.
        
        This method delegates to the JWT token manager for actual token creation.
        You could also implement custom token logic here if needed.
        """
        # Import here to avoid circular imports
        from app.auth import JWTTokenManager
        
        jwt_manager = JWTTokenManager()
        return jwt_manager.create_access_token(user_id, expires_delta)


class DatabaseAuthManager(BaseAuthManager):
    """
    Example authentication manager that would connect to a database.
    
    This is a skeleton showing how you might implement database-based authentication.
    """
    
    def __init__(self):
        """Initialize database connection."""
        # In production, you would establish a database connection here
        # self.db = DatabaseConnection()
        logger.info("Database authentication manager initialized (skeleton)")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user against database.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data dict if authentication succeeds, None otherwise
        """
        logger.info(f"Database authentication for user: {username}")
        
        # Example database query (commented out for demonstration)
        # try:
        #     user = await self.db.users.find_one({"username": username})
        #     if user and verify_password(password, user["hashed_password"]):
        #         return {
        #             "id": str(user["_id"]),
        #             "username": user["username"],
        #             "role": user["role"],
        #             "email": user["email"]
        #         }
        # except Exception as e:
        #     logger.error(f"Database authentication error: {e}")
        
        logger.warning("Database authentication not implemented (skeleton)")
        return None


class LDAPAuthManager(BaseAuthManager):
    """
    Example authentication manager for LDAP integration.
    
    This is a skeleton showing how you might implement LDAP-based authentication.
    """
    
    def __init__(self):
        """Initialize LDAP connection."""
        # In production, you would establish an LDAP connection here
        # self.ldap_client = LDAPClient(settings.LDAP_SERVER, settings.LDAP_BIND_DN)
        logger.info("LDAP authentication manager initialized (skeleton)")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user against LDAP server.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data dict if authentication succeeds, None otherwise
        """
        logger.info(f"LDAP authentication for user: {username}")
        
        # Example LDAP authentication (commented out for demonstration)
        # try:
        #     user_dn = f"uid={username},{settings.LDAP_USER_BASE_DN}"
        #     self.ldap_client.bind(user_dn, password)
        #     
        #     # Search for user attributes
        #     user_attrs = self.ldap_client.search(
        #         settings.LDAP_USER_BASE_DN,
        #         f"(uid={username})",
        #         attributes=["uid", "cn", "mail", "memberOf"]
        #     )
        #     
        #     if user_attrs:
        #         return {
        #             "id": username,
        #             "username": username,
        #             "display_name": user_attrs[0]["cn"],
        #             "email": user_attrs[0].get("mail", ""),
        #             "groups": user_attrs[0].get("memberOf", [])
        #         }
        # except Exception as e:
        #     logger.error(f"LDAP authentication error: {e}")
        
        logger.warning("LDAP authentication not implemented (skeleton)")
        return None
