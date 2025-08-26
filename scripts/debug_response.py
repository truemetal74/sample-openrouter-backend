#!/usr/bin/env python3
"""
Debug script to understand response object structure and help fix logging middleware.
"""

import sys
import os
from typing import Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def inspect_response_object(response_obj: Any, label: str = "Response"):
    """Inspect a response object and print its structure."""
    print(f"\n=== {label} ===")
    print(f"Type: {type(response_obj)}")
    print(f"Class name: {response_obj.__class__.__name__}")
    
    # Check for common attributes
    common_attrs = ['body', 'content', 'body_iterator', 'status_code', 'headers']
    for attr in common_attrs:
        if hasattr(response_obj, attr):
            value = getattr(response_obj, attr)
            print(f"Has {attr}: {bool(value)} | Type: {type(value)}")
            if value and attr in ['body', 'content']:
                try:
                    if isinstance(value, bytes):
                        preview = value[:100].decode('utf-8', errors='replace')
                        print(f"  {attr} preview: {repr(preview)}...")
                    else:
                        preview = str(value)[:100]
                        print(f"  {attr} preview: {repr(preview)}...")
                except Exception as e:
                    print(f"  Error reading {attr}: {e}")
        else:
            print(f"Has {attr}: False")
    
    # Check for other potentially useful attributes
    all_attrs = [attr for attr in dir(response_obj) if not attr.startswith('_') and not callable(getattr(response_obj, attr))]
    print(f"Other attributes: {all_attrs}")
    
    # Try to get string representation
    try:
        str_repr = str(response_obj)
        if len(str_repr) > 200:
            str_repr = str_repr[:200] + "..."
        print(f"String representation: {repr(str_repr)}")
    except Exception as e:
        print(f"Error getting string representation: {e}")

def main():
    """Main function to demonstrate response object inspection."""
    print("Response Object Debug Script")
    print("=" * 50)
    
    # Create some example response objects to inspect
    from fastapi.responses import JSONResponse
    from starlette.responses import StreamingResponse
    
    # Example 1: Normal JSONResponse
    json_response = JSONResponse(
        content={"message": "Hello World", "status": "success"},
        status_code=200
    )
    inspect_response_object(json_response, "JSONResponse")
    
    # Example 2: StreamingResponse
    def generate_content():
        yield b"Hello "
        yield b"World"
    
    streaming_response = StreamingResponse(
        content=generate_content(),
        status_code=200
    )
    inspect_response_object(streaming_response, "StreamingResponse")
    
    # Example 3: Mock _StreamingResponse (similar to what we see in logs)
    class MockStreamingResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code
            self.headers = {}
        
        def __str__(self):
            return f"<starlette.middleware.base._StreamingResponse object at 0x12345678>"
    
    mock_response = MockStreamingResponse(
        content={"message": "Mock response", "data": [1, 2, 3]},
        status_code=200
    )
    inspect_response_object(mock_response, "Mock _StreamingResponse")
    
    print("\n" + "=" * 50)
    print("Debug script completed. Use this information to improve the logging middleware.")

if __name__ == "__main__":
    main()
