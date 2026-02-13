"""
Vercel entrypoint for FastAPI application.

This file exports the FastAPI app instance for Vercel deployment.
Vercel will automatically detect and serve this FastAPI application.
"""

import sys
import os

# Import the FastAPI app from api.main
from api.main import app

# Export the app instance for Vercel
__all__ = ["app"]
