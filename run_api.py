"""
Entrypoint that always binds to PORT. If the full app fails to load (import/env error),
serves a minimal app with /health so the process stays up and Railway health checks pass.
"""
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

try:
    from api.main import app
    logger.info("Loaded full api.main app")
except Exception as e:
    logger.exception("Failed to load api.main (serving /health only): %s", e)
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting uvicorn on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
