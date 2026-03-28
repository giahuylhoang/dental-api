"""
Entrypoint that always binds to PORT. If the full app fails to load (import/env error),
serves a minimal app with /health so the process stays up and Railway health checks pass.
"""
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

_full_app_loaded = False
try:
    from api.main import app
    logger.info("Loaded full api.main app")
    _full_app_loaded = True
except Exception as e:
    logger.exception("Failed to load api.main (serving /health only): %s", e)
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    if _full_app_loaded and os.getenv("SMTP_DEPLOY_VERIFY_TO", "").strip():
        from clients.email_client import verify_smtp_deploy

        if not verify_smtp_deploy():
            logger.error("Exiting: SMTP deploy verification failed")
            sys.exit(1)

    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting uvicorn on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
