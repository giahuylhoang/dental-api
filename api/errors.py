"""Standardized error response utilities."""
import uuid

from fastapi.responses import JSONResponse


def error_response(status: int, code: str, message: str, request_id: str) -> JSONResponse:
    """Create a standardized error response with envelope.
    
    Returns JSON: {"error_id": "...", "code": "...", "message": "...", "request_id": "..."}
    """
    return JSONResponse(
        status_code=status,
        content={
            "error_id": str(uuid.uuid4()),
            "code": code,
            "message": message,
            "request_id": request_id,
        },
        headers={"X-Request-Id": request_id},
    )
