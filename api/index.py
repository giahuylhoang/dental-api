"""
Vercel serverless function handler for FastAPI.

Vercel automatically detects Python files in the api/ directory
and executes them as serverless functions.
"""

from api.main import app

# Export the app for Vercel
# Vercel will automatically handle FastAPI apps
__all__ = ["app"]
