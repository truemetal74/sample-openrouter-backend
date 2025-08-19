# Custom Routes Feature

This application supports dynamically loading custom route modules at startup based on configuration. This allows you to extend the API with additional endpoints without modifying the core application code.

## How It Works

The application automatically scans for custom route modules specified in the `CUSTOM_ROUTES` configuration and loads them during startup. Each custom module should:

1. Define a `router` attribute (FastAPI APIRouter instance)
2. Optionally implement an `initialize(config)` method for setup
3. Be importable by Python

## Configuration

### Environment Variables

Add custom routes to your `.env` file:

```bash
# Single module
CUSTOM_ROUTES=custom_routes_example

# Multiple modules (comma-separated)
CUSTOM_ROUTES=custom_routes_example,another_module,third_module

# Or as a list in Python format
CUSTOM_ROUTES=["custom_routes_example", "another_module"]
```

### Configuration File

You can also set this in your configuration:

```python
CUSTOM_ROUTES = ["custom_routes_example", "user_management", "analytics"]
```

## Creating Custom Route Modules

### Basic Structure

```python
from fastapi import APIRouter, Depends
from app.auth import get_current_user

# Create router instance
router = APIRouter(
    prefix="/custom",  # URL prefix for all routes in this module
    tags=["custom"],   # OpenAPI tags for grouping
    dependencies=[],   # Global dependencies
    responses={404: {"description": "Not found"}},
)

def initialize(config):
    """Optional initialization method called when module is loaded."""
    # Setup database connections, external services, etc.
    pass

@router.get("/hello")
async def custom_hello():
    """Your custom endpoint."""
    return {"message": "Hello from custom routes!"}

@router.get("/user-info")
async def get_user_info(current_user: str = Depends(get_current_user)):
    """Authenticated endpoint example."""
    return {"user_id": current_user, "module": "custom_routes"}
```

### Required Components

1. **Router Instance**: Must have a `router` attribute that is a FastAPI `APIRouter`
2. **Importable**: The module must be importable by Python (proper `__init__.py` files, etc.)
3. **Error Handling**: Implement proper error handling in your routes

### Optional Components

1. **Initialize Method**: If present, will be called with the app config during startup
2. **Dependencies**: Can use the same dependencies as the main app (auth, etc.)
3. **Models**: Can import and use the same models as the main app

## Example Module

See `app/custom_routes_example.py` for a complete working example.

## Loading Process

1. Application starts up
2. CORS middleware is configured
3. Custom routes are loaded dynamically:
   - Each module is imported
   - `initialize(config)` is called if present
   - Router is included in the main app
4. Main application routes are defined
5. Application is ready to serve requests

## Error Handling

- **Import Errors**: Logged as errors, application continues
- **Missing Router**: Logged as warnings, module is skipped
- **Initialization Errors**: Logged as warnings, module continues loading
- **Runtime Errors**: Handled by FastAPI's standard error handling

## Best Practices

1. **Prefix Your Routes**: Use unique prefixes to avoid conflicts
2. **Handle Errors Gracefully**: Implement proper error handling
3. **Use Authentication**: Leverage the existing auth system
4. **Log Appropriately**: Use the existing logging infrastructure
5. **Test Thoroughly**: Ensure your custom routes work correctly
6. **Document**: Provide clear documentation for your custom endpoints
7. **Safe Logging**: Never log sensitive configuration data or user credentials
8. **Use Safe Config Logging**: Use `config.get_safe_config_for_logging()` if you need to log configuration information

## Troubleshooting

### Module Not Loading

1. Check the module name in `CUSTOM_ROUTES` configuration
2. Ensure the module is importable (check `__init__.py` files)
3. Check application logs for import errors
4. Verify the module has a `router` attribute

### Routes Not Accessible

1. Check the router prefix configuration
2. Ensure the module was loaded successfully
3. Check application logs for any errors
4. Verify the routes are properly defined

### Initialization Issues

1. Check the `initialize` method for errors
2. Ensure the config parameter is used correctly
3. Check application logs for initialization warnings

## Security Considerations

- Custom routes inherit the same security context as the main application
- Use the existing authentication system (`get_current_user`)
- Implement proper authorization checks in your custom routes
- Be careful with user input validation
- **Sensitive Data Protection**: The application automatically masks sensitive configuration data (API keys, secrets, etc.) in logs
- Never log full configuration objects that may contain sensitive information

## Performance Notes

- Modules are loaded once at startup
- No runtime performance impact
- Large numbers of custom modules may increase startup time
- Consider lazy loading for very large modules if needed
