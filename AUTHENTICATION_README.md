# Authentication System

This application provides a flexible, configurable authentication system that supports OAuth2.0 compatible login flows and multiple authentication backends.

## Overview

The authentication system is built around the concept of **Authentication Managers** - classes that handle user authentication and token management. This design allows developers to easily switch between different authentication strategies without modifying the core application code.

## Architecture

### BaseAuthManager

All authentication managers inherit from `BaseAuthManager`, which defines the interface:

```python
class BaseAuthManager:
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password. Returns user data or None."""
        pass
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token for authenticated user. Raises AuthenticationError if not supported."""
        pass
```

### Available Managers

#### 1. DefaultAuthManager (Default)
- **Purpose**: Development/testing - no actual authentication
- **Behavior**: Always rejects login attempts
- **Use Case**: When you want to disable authentication temporarily

#### 2. JWTTokenManager
- **Purpose**: Production-ready JWT token management
- **Features**: 
  - JWT token creation and validation
  - Configurable expiration times
  - Secure token handling
- **Use Case**: Standard JWT-based authentication

#### 3. Custom Managers
- **Purpose**: Implement your own authentication logic
- **Examples**: Database, LDAP, OAuth providers, etc.
- **Use Case**: Integration with existing user systems

## Configuration

### Environment Variables

Set `AUTH_MANAGER_CLASS` in your `.env` file:

```bash
# Built-in managers
AUTH_MANAGER_CLASS=DefaultAuthManager
AUTH_MANAGER_CLASS=JWTTokenManager

# Custom managers
AUTH_MANAGER_CLASS=app.custom_auth_example.CustomAuthManager
AUTH_MANAGER_CLASS=app.custom_auth_example.DatabaseAuthManager
AUTH_MANAGER_CLASS=app.custom_auth_example.LDAPAuthManager
```

### Configuration Options

```python
# In app/config.py
AUTH_MANAGER_CLASS: str = Field(
    default="DefaultAuthManager",
    description="Authentication manager class to use"
)
```

## Usage

### OAuth2.0 Compatible Login

The `/auth/token` endpoint accepts username and password via form data:

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "admin_001",
  "user_data": {
    "id": "admin_001",
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com"
  }
}
```

### Using Access Tokens

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  "http://localhost:8000/prompts"
```

## Implementing Custom Authentication

### Step 1: Create Your Manager

```python
# app/my_auth_manager.py
from app.auth import BaseAuthManager
from typing import Optional, Dict, Any

class MyAuthManager(BaseAuthManager):
    def __init__(self):
        # Initialize your authentication system
        self.db_connection = connect_to_database()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        # Implement your authentication logic
        user = self.db_connection.users.find_one({"username": username})
        if user and verify_password(password, user["hashed_password"]):
            return {
                "id": str(user["_id"]),
                "username": user["username"],
                "role": user["role"]
            }
        return None
    
    def create_access_token(self, user_id: str, expires_delta=None):
        # Delegate to JWT manager or implement custom logic
        from app.auth import JWTTokenManager
        jwt_manager = JWTTokenManager()
        return jwt_manager.create_access_token(user_id, expires_delta)
```

### Step 2: Configure

```bash
# .env
AUTH_MANAGER_CLASS=app.my_auth_manager.MyAuthManager
```

### Step 3: Test

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=mypassword"
```

## Security Considerations

### Password Handling
- **Never store plain text passwords**
- Use secure hashing (bcrypt, Argon2, etc.)
- Implement password complexity requirements
- Use secure random salt generation

### Token Security
- **Use HTTPS in production**
- Implement token expiration
- Consider refresh token rotation
- Log authentication attempts

### Rate Limiting
- Implement login attempt throttling
- Monitor for brute force attacks
- Consider CAPTCHA for repeated failures

## Examples

### Database Authentication

See `app/custom_auth_example.py` for a complete database authentication example.

### LDAP Integration

See `app/custom_auth_example.py` for LDAP authentication skeleton.

### OAuth Provider Integration

```python
class OAuthProviderManager(BaseAuthManager):
    def __init__(self):
        self.oauth_client = OAuth2Client(
            client_id=settings.OAUTH_CLIENT_ID,
            client_secret=settings.OAUTH_CLIENT_SECRET
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        # Implement OAuth provider authentication
        # This is a simplified example
        pass
```

## Troubleshooting

### Common Issues

1. **"Token creation not supported"**
   - Your auth manager doesn't implement `create_access_token`
   - Use `JWTTokenManager` or implement the method

2. **"Authentication manager doesn't support token validation"**
   - Your auth manager doesn't implement `get_user_id_from_token`
   - Use `JWTTokenManager` or implement the method

3. **Import errors**
   - Check the module path in `AUTH_MANAGER_CLASS`
   - Ensure the class exists in the specified module

### Debug Mode

Enable debug logging to see authentication details:

```bash
LOG_LEVEL=DEBUG
ENABLE_DETAILED_LOGGING=True
```

## Migration Guide

### From Old System

If you were using the old `AuthManager.create_access_token()` directly:

1. **Update imports**: Use `get_auth_manager()` instead
2. **Configure manager**: Set `AUTH_MANAGER_CLASS=JWTTokenManager`
3. **Update calls**: Replace direct calls with manager instances

```python
# Old way
from app.auth import AuthManager
token = AuthManager.create_access_token(user_id)

# New way
from app.auth import get_auth_manager
auth_manager = get_auth_manager()
token = auth_manager.create_access_token(user_id)
```

## Best Practices

1. **Use environment-specific managers**: Different managers for dev/staging/prod
2. **Implement proper error handling**: Don't expose sensitive information
3. **Add monitoring**: Log authentication attempts and failures
4. **Regular security reviews**: Audit authentication logic regularly
5. **Follow OAuth2.0 standards**: Use proper token types and flows

