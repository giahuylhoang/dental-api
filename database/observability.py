"""SQL event logger that correlates queries with the inbound request_id.

Off by default. Enable by setting `OBSERVE_SQL=1`. The audit harness flips this
on for full-stack trace runs; production leaves it off.
"""
import json
import logging
import os
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

from api.middleware.observability import request_id_ctx

logger = logging.getLogger("dental-receptionist")

_registered = False


def _is_enabled() -> bool:
    return os.getenv("OBSERVE_SQL", "").strip() in {"1", "true", "True", "yes"}


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if not _is_enabled():
        return
    context._observe_started_at = time.perf_counter()


def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if not _is_enabled():
        return
    started = getattr(context, "_observe_started_at", None)
    if started is None:
        return
    duration_ms = round((time.perf_counter() - started) * 1000, 2)

    request_id = ""
    try:
        request_id = request_id_ctx.get()
    except LookupError:
        pass

    rowcount = getattr(cursor, "rowcount", None)
    log_entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request_id": request_id,
        "statement": statement[:500],
        "duration_ms": duration_ms,
        "rowcount": rowcount if isinstance(rowcount, int) and rowcount >= 0 else None,
    }
    logger.debug(json.dumps(log_entry))


def register_sql_events(engine: Engine, force: bool = False) -> None:
    """Attach the before/after cursor execute listeners to `engine`.

    Idempotent at the module level via `_registered`. Tests pass `force=True`
    to attach to a per-test in-memory engine. Listeners are always installed
    regardless of OBSERVE_SQL — the env var is checked at emit time so it can
    be flipped without re-registering.
    """
    global _registered
    if _registered and not force:
        return
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)
    _registered = True
