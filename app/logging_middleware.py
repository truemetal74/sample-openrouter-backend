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

                logger.error(f"Validation exception {validation_exc.errors()}")
                return err_response
            except Exception as e:
                logger.error(f"Application error: {e} {traceback.format_exc()}")
                return JSONResponse(
                                        status_code=500,
                                        content=dict(
                                            message = f"Server error: {e}",
                                            trace = traceback.format_exc(),
                                            request_id = request_id
                                        )
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
                            if len(response_text) > 500:
                                response_text = response_text[:500] + "... [truncated]"
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
