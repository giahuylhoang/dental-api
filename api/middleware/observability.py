"""Observability middleware for request tracing and structured logging."""
import json
import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("dental-receptionist")

# Context variable for request ID - accessible from SQL event logger
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing, structured logging, and error handling."""

    async def dispatch(self, request: Request, call_next):
        # Read or generate request ID
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request_id_ctx.set(request_id)

        clinic_id = request.headers.get("X-Clinic-Id", "default")
        start_time = time.perf_counter()
        exc_type = None
        status = 500

        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-Id"] = request_id
            return response
        except Exception as e:
            exc_type = type(e).__name__
            from api.errors import error_response
            return error_response(
                500,
                "INTERNAL_ERROR",
                "Internal server error",
                request_id,
            )
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "duration_ms": round(duration_ms, 2),
                "clinic_id": clinic_id,
                "exc_type": exc_type,
            }
            logger.info(json.dumps(log_entry))
