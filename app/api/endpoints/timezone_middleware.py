from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ...utils.timezone import utc_to_ist
from datetime import datetime
import json
from typing import Any, Dict, List, Union

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            # Convert to IST and return ISO format string
            return utc_to_ist(obj).isoformat()
        return super().default(obj)

def convert_datetime_to_ist(obj: Any) -> Any:
    """Recursively convert datetime objects in a dict/list to IST datetime objects."""
    if isinstance(obj, dict):
        return {k: convert_datetime_to_ist(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_ist(item) for item in obj]
    elif isinstance(obj, datetime):
        return utc_to_ist(obj)
    return obj

class TimezoneMiddleware(BaseHTTPMiddleware):
    """Middleware to convert datetime values in responses from UTC to IST."""
    
    async def dispatch(self, request: Request, call_next):
        # Process the request normally
        response = await call_next(request)
        
        # Temporarily disable the middleware by returning the response directly
        return response
        
        # Skip processing if:
        # 1. Not a JSON response
        # 2. OpenAPI-related endpoints (docs, openapi.json)
        if (response.headers.get("content-type") != "application/json" or 
            request.url.path in ["/openapi.json", "/docs", "/redoc"]):
            return response
        
        # Get the response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # If no content, return response as is
        if not body:
            return response
        
        try:
            # Parse JSON
            data = json.loads(body)
            
            # Convert datetime values to IST
            converted_data = convert_datetime_to_ist(data)
            
            # Serialize back to JSON
            modified_body = json.dumps(converted_data, cls=DateTimeEncoder).encode()
            
            # Create new response
            return Response(
                content=modified_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
        except Exception as e:
            # In case of any error, return the original response
            print(f"Error in timezone middleware: {e}")
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

# Import the needed Response class
from starlette.responses import Response 