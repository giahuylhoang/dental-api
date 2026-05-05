"""Caching utilities for read-side endpoints."""
import hashlib
import json
from fastapi import Request, Response


def add_cache_headers(response: Response, data: dict | list, max_age: int = 10):
    """Add ETag and Cache-Control headers to response."""
    # Generate ETag from data
    data_str = json.dumps(data, sort_keys=True, default=str)
    etag = hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = f"private, max-age={max_age}"
    return etag


def check_etag(request: Request, etag: str) -> bool:
    """Check if client's If-None-Match matches our ETag."""
    if_none_match = request.headers.get("If-None-Match", "")
    return if_none_match == f'"{etag}"' or if_none_match == etag
