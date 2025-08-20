import logging
import uuid
import traceback
from typing import Callable
from fastapi import Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse, Response
from app.config import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def extract_request_id(request: Request):
    """Extract request ID from request headers"""
    for id in [
        request.headers.get('X-Request-ID', None),
        request.headers.get('X-Cloud-Trace-Context', None),
    ]:
        if id is not None:
            return id
    return 'WT-'+str(uuid.uuid4())

def get_client_ip(request: Request) -> str:
    """Extract client IP from various headers."""
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        return client_ip.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_loggable_headers(request: Request) -> str:
    """Extract and format loggable headers."""
    headers_to_log = ['content-type', 'user-agent', 'accept', 'x-forwarded-for', 'host', 'referer']
    sensitive_headers = ['authorization', 'recaptcha-response']
    
    def obfuscate_string(s: str) -> str:
        if s is None or len(s) <= 13:
            return s
        return s[:10] + '***' + s[-3:]
    
    headers = []
    for header in headers_to_log:
        value = request.headers.get(header)
        if value:
            if header in sensitive_headers:
                value = obfuscate_string(value)
            headers.append(f"{header}: '{value}'")
    
    return " | ".join(headers) if headers else "No relevant headers"

async def logging_middleware(request: Request, call_next):
    """Comprehensive logging middleware for all requests and responses."""
    # Extract or generate request ID
    request_id = extract_request_id(request)
    request.state.request_id = request_id
    
    # Log request details
    logger.info(f"[REQUEST] {request.method} {request.url.path} | "
               f"Request ID: {request_id} | "
               f"Client IP: {get_client_ip(request)} | "
               f"Headers: {get_loggable_headers(request)}")
    
    # Log request body if detailed logging is enabled
    if settings.ENABLE_DETAILED_LOGGING:
        try:
            req_body = await request.body()
            if req_body:
                content_type = request.headers.get('content-type', '').lower()
                if 'multipart/form-data' in content_type or 'application/octet-stream' in content_type:
                    req_body_text = "<binary data>"
                else:
                    req_body_text = req_body.decode("utf-8").replace("\n", " ")
                logger.info(f"[REQUEST BODY] {request_id} | {req_body_text}")
            else:
                logger.info(f"[REQUEST BODY] {request_id} | <empty>")
        except Exception as e:
            logger.warning(f"[REQUEST BODY] {request_id} | Error reading body: {e}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Debug: Log response type and attributes for troubleshooting
        if settings.ENABLE_RESPONSE_DEBUG:
            logger.debug(f"[RESPONSE DEBUG] {request_id} | Response type: {type(response)} | Status: {getattr(response, 'status_code', 'N/A')}")
            if hasattr(response, 'body'):
                logger.debug(f"[RESPONSE DEBUG] {request_id} | Has body: {bool(response.body)} | Body type: {type(response.body)} | Body length: {len(response.body) if response.body else 0}")
            if hasattr(response, 'content'):
                logger.debug(f"[RESPONSE DEBUG] {request_id} | Has content: {bool(response.content)} | Content type: {type(response.content)} | Content length: {len(response.content) if response.content else 0}")
            # Log all available attributes for debugging
            logger.debug(f"[RESPONSE DEBUG] {request_id} | Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Log response details
        if settings.ENABLE_DETAILED_LOGGING:
            try:
                # Try multiple ways to get response body
                response_text = None
                
                # Method 1: Check if response has a body attribute
                if hasattr(response, 'body') and response.body:
                    try:
                        if isinstance(response.body, bytes):
                            response_text = response.body.decode("utf-8").replace("\n", " ")
                        else:
                            response_text = str(response.body)
                    except (AttributeError, UnicodeDecodeError):
                        response_text = str(response.body)
                
                # Method 2: Check if response has content attribute
                elif hasattr(response, 'content') and response.content:
                    try:
                        if isinstance(response.content, bytes):
                            response_text = response.content.decode("utf-8").replace("\n", " ")
                        else:
                            response_text = str(response.content)
                    except (AttributeError, UnicodeDecodeError):
                        response_text = str(response.content)
                
                # Method 3: Try to get response as string
                elif hasattr(response, '__str__'):
                    response_text = str(response)
                
                # Method 4: Try to access response data directly (for FastAPI responses)
                elif hasattr(response, 'body_iterator') and response.body_iterator:
                    try:
                        # This is for streaming responses
                        response_text = "<streaming response>"
                    except Exception:
                        pass
                
                # Log the response
                if response_text and response_text.strip():
                    if len(response_text) > settings.LOG_TEXT_TRUNCATE_LENGTH:
                        response_text = response_text[:settings.LOG_TEXT_TRUNCATE_LENGTH] + "... [truncated]"
                    logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | {response_text}")
                else:
                    logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | <no body>")
                    
            except Exception as e:
                logger.warning(f"[RESPONSE] {request_id} | Status: {response.status_code} | Error logging response: {e}")
                # Fallback: log response type and attributes for debugging
                logger.debug(f"[RESPONSE DEBUG] {request_id} | Response type: {type(response)} | Attributes: {dir(response)}")
        else:
            logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code}")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except HTTPException as http_exc:
        # Log HTTP exceptions with full details
        error_detail = getattr(http_exc, 'detail', 'No detail provided')
        logger.error(f"[HTTP ERROR] {request_id} | Status: {http_exc.status_code} | Detail: {error_detail}")
        
        # If the detail is a dict/JSON, log it in a more readable format
        if isinstance(error_detail, dict):
            import json
            try:
                error_json = json.dumps(error_detail, indent=2)
                logger.error(f"[HTTP ERROR DETAIL] {request_id} | {error_json}")
            except Exception as json_e:
                logger.error(f"[HTTP ERROR DETAIL] {request_id} | Failed to format JSON: {json_e} | Raw: {error_detail}")
        elif isinstance(error_detail, str):
            logger.error(f"[HTTP ERROR DETAIL] {request_id} | {error_detail}")
        
        # Re-raise HTTP exceptions as they should be handled by FastAPI
        raise
    except Exception as e:
        # Log the error with traceback for debugging
        logger.error(f"[ERROR] {request_id} | Exception: {str(e)}")
        logger.error(f"[ERROR TRACEBACK] {request_id} | {traceback.format_exc()}")
        
        # Return a proper error response instead of re-raising
        # This prevents the error from propagating to uvicorn
        error_content = {
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
        
        # Add detailed error info only if configured (development only)
        if settings.SHOW_DETAILED_ERRORS:
            error_content.update({
                "exception_type": type(e).__name__,
                "exception_message": str(e)
            })
        
        return JSONResponse(
            status_code=500,
            content=error_content
        )

def log_formatted_json(label: str, text):
    """Take JSON (as byte-string) and pretty-print it to the log"""
    if len(text) == 0:
        logger.info(f"{label}: Empty")
        return
    logger.info(f"{label}: {text}")
    return

def log_info(req_body, res_body):
    log_formatted_json("Request body", req_body)
    log_formatted_json("Reply body", res_body)

def log_with_label(label: str, data):
    log_formatted_json(label, data)

class RouteWithLogging(APIRoute):
    """Custom route class that logs request and response bodies"""
    
    def add_headers_to_log(self, request: Request):
        """Add headers to log with sensitive header obfuscation"""
        def obfuscate_string(s: str) -> str:
            """
            Obfuscates the contents of sensitive headers, specifically
            'Authorization' - but leaves a few characters so one can understand
            whether it is a correct one or not. 
            Keeps the first 8 characters and the last 3, replaces the middle
            characters with a single '*'.
            """
            if s is None or len(s) <= 13:  # If the string is too short to obfuscate
                return s
            
            return s[:10] + '***' + s[-3:]

        # Define headers to log and sensitive ones to obfuscate
        HEADER_LIST = ['content-type', 'user-agent', 'accept', 'x-forwarded-for', 'host', 'referer']
        SENSITIVE_HEADERS = ['authorization', 'recaptcha-response']
        
        headers = []
        for header in HEADER_LIST:
            value = request.headers.get(header)
            if header in SENSITIVE_HEADERS:
                value = obfuscate_string(value)
            if value:  # Only log headers that have values
                headers.append(f"{header}: '{value}'")
        
        if headers:
            return " | ".join(headers)
        else:
            return "No relevant headers"

    def get_ip(self, request: Request):
        """Extract client IP from various headers"""
        client_ip = None
        gcp_ip = request.headers.get("x-forwarded-for")
        if gcp_ip:
            client_ip = gcp_ip.split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        return client_ip

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # Set request ID from header
            request_id = extract_request_id(request)
            request.state.request_id = request_id
            
            # Log request details
            req_body = await request.body()
            
            # Check if the request is multipart/form-data or contains binary content
            content_type = request.headers.get('content-type', '').lower()
            if 'multipart/form-data' in content_type or 'application/octet-stream' in content_type:
                req_body = "<binary data>"
            else:
                try:
                    req_body = req_body.decode("utf-8").replace("\n", " ")
                except UnicodeDecodeError:
                    req_body = "<binary data>"

            if len(req_body) == 0:
                req_body = "<empty>"
                
            # Log request details with clear structure
            logger.info(f"[REQUEST] {request.method} {request.url.path} | "
                       f"Request ID: {request_id} | "
                       f"Client IP: {self.get_ip(request)} | "
                       f"{self.add_headers_to_log(request)}")
            
            # Log request body separately for better readability
            if settings.ENABLE_DETAILED_LOGGING:
                if req_body and req_body != "<empty>" and req_body != "<binary data>":
                    logger.info(f"[REQUEST BODY] {request_id} | {req_body}")
                else:
                    logger.info(f"[REQUEST BODY] {request_id} | {req_body}")
            
            try:
                response = await original_route_handler(request)
            except HTTPException as http_exc:
                # Handle HTTP exceptions with detailed logging
                error_detail = getattr(http_exc, 'detail', 'No detail provided')
                logger.error(f"[HTTP ERROR] {request_id} | Status: {http_exc.status_code} | Detail: {error_detail}")
                
                # If the detail is a dict/JSON, log it in a more readable format
                if isinstance(error_detail, dict):
                    import json
                    try:
                        error_json = json.dumps(error_detail, indent=2)
                        logger.error(f"[HTTP ERROR DETAIL] {request_id} | {error_json}")
                    except Exception as json_e:
                        logger.error(f"[HTTP ERROR DETAIL] {request_id} | Failed to format JSON: {json_e} | Raw: {error_detail}")
                elif isinstance(error_detail, str):
                    logger.error(f"[HTTP ERROR DETAIL] {request_id} | {error_detail}")
                
                # Re-raise the HTTP exception
                raise
            except RequestValidationError as validation_exc:
                # Handle validation errors
                err_response = JSONResponse(status_code=422,
                                            content=dict(
                                                        error_message = "Input data validation error: " + 
                                                            str(validation_exc.errors()),
                                                        path = request.url.path,
                                                        request_id = request_id
                                                        )
                )

                logger.error(f"[VALIDATION ERROR] {request_id} | {validation_exc.errors()}")
                return err_response
            except Exception as e:
                # Log the error with traceback for debugging
                logger.error(f"[APPLICATION ERROR] {request_id} | {e}")
                logger.error(f"[ERROR TRACEBACK] {request_id} | {traceback.format_exc()}")
                
                # Return a clean error response without exposing internal details
                error_content = {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
                
                # Add detailed error info only if configured (development only)
                if settings.SHOW_DETAILED_ERRORS:
                    error_content.update({
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    })
                
                return JSONResponse(
                    status_code=500,
                    content=error_content
                )
            
            if isinstance(response, StreamingResponse):
                res_body = b""
                async for item in response.body_iterator:
                    res_body += item

                # Log streaming response
                logger.info(f"[RESPONSE] {request_id} | Streaming response | Status: {response.status_code}")
                
                task = BackgroundTask(log_info, req_body, b"<streaming content>")
                return Response(
                    content=res_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                    background=task,
                )
            else:
                res_body = response.body
                
                # Log response details
                if settings.ENABLE_DETAILED_LOGGING:
                    try:
                        if res_body:
                            response_text = res_body.decode("utf-8").replace("\n", " ")
                            # Truncate long responses for readability
                            if len(response_text) > settings.LOG_TEXT_TRUNCATE_LENGTH:
                                response_text = response_text[:settings.LOG_TEXT_TRUNCATE_LENGTH] + "... [truncated]"
                            logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | {response_text}")
                        else:
                            logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code} | Empty response")
                    except Exception as e:
                        logger.warning(f"[RESPONSE] {request_id} | Status: {response.status_code} | Error logging response: {e}")
                else:
                    # Just log basic response info
                    logger.info(f"[RESPONSE] {request_id} | Status: {response.status_code}")
                
                return response

        return custom_route_handler

    def log_detailed_debug(self, message: str, data: any):
        """Helper method for detailed debug logging"""
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.debug(f"[DETAILED DEBUG] {message}: {data}")
