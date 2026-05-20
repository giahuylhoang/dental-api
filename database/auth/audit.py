"""SQLAlchemy event listeners for PHI audit logging."""
from contextvars import ContextVar
from datetime import datetime, date
from typing import Optional, Tuple

from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session as SASession, attributes

from database.connection import Base

# ContextVar populated by audit_context dependency in each request
_audit_ctx: ContextVar[Optional[Tuple[Optional[str], Optional[str], Optional[str]]]] = ContextVar(
    "_audit_ctx", default=None
)


def set_audit_context(user_id: Optional[str], ip: Optional[str], ua: Optional[str]) -> None:
    _audit_ctx.set((user_id, ip, ua))


def get_audit_context() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    ctx = _audit_ctx.get()
    if ctx is None:
        return None, None, None
    return ctx


def _get_clinic_id(target) -> Optional[str]:
    return getattr(target, "clinic_id", None)


def _entity_id(target) -> Optional[str]:
    try:
        pk = inspect(target.__class__).primary_key
        vals = [str(getattr(target, c.name, None)) for c in pk]
        return ",".join(vals)
    except Exception:
        return None


def _serialize(val):
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if hasattr(val, "__tablename__"):
        return None
    return None


def _column_dict(target) -> dict:
    mapper = inspect(target.__class__)
    result = {}
    for col_attr in mapper.column_attrs:
        key = col_attr.key
        try:
            val = getattr(target, key)
            result[key] = _serialize(val)
        except Exception:
            pass
    return result


# PHI table names to audit
_PHI_TABLES = {"patients", "appointments", "leads"}


def _should_audit(target) -> bool:
    return getattr(target, "__tablename__", None) in _PHI_TABLES


def _make_audit_log(action: str, entity_type: str, entity_id: Optional[str],
                    clinic_id: Optional[str], before: Optional[dict], after: Optional[dict]):
    from database.auth.models import AuditLog
    user_id, ip, ua = get_audit_context()
    return AuditLog(
        clinic_id=clinic_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        ip=ip,
        user_agent=ua,
    )


def _fetch_old_row(session, target) -> Optional[dict]:
    """Fetch the committed row from DB using raw SQL (no autoflush)."""
    mapper_insp = inspect(target.__class__)
    table = target.__tablename__
    pk_cols = {c.name: getattr(target, c.name) for c in mapper_insp.primary_key}
    if not pk_cols:
        return None
    where = " AND ".join(f"{k} = :{k}" for k in pk_cols)
    try:
        with session.no_autoflush:
            result = session.execute(text(f"SELECT * FROM {table} WHERE {where}"), pk_cols)
            row = result.mappings().first()
            if row is None:
                return None
            return dict(row)
    except Exception:
        return None


def _before_flush(session, flush_context, instances):
    """Capture audit entries before flush."""
    pending_logs = []

    for target in list(session.new):
        if not _should_audit(target):
            continue
        after = _column_dict(target)
        pending_logs.append(_make_audit_log(
            "insert", target.__tablename__, _entity_id(target),
            _get_clinic_id(target), None, after,
        ))

    for target in list(session.dirty):
        if not _should_audit(target):
            continue
        if not session.is_modified(target, include_collections=False):
            continue

        # Get current (new) values
        new_vals = _column_dict(target)
        # Get old values from DB
        old_row = _fetch_old_row(session, target)
        if old_row is None:
            continue

        before = {}
        after = {}
        for key, new_val in new_vals.items():
            old_val = _serialize(old_row.get(key))
            if old_val != new_val:
                before[key] = old_val
                after[key] = new_val

        if before:
            pending_logs.append(_make_audit_log(
                "update", target.__tablename__, _entity_id(target),
                _get_clinic_id(target), before, after,
            ))

    for target in list(session.deleted):
        if not _should_audit(target):
            continue
        before = _column_dict(target)
        pending_logs.append(_make_audit_log(
            "delete", target.__tablename__, _entity_id(target),
            _get_clinic_id(target), before, None,
        ))

    for log in pending_logs:
        session.add(log)


def register_audit_listeners() -> None:
    """Attach event listeners. Call once at startup."""
    event.listen(SASession, "before_flush", _before_flush)


# v1.1 — read-access audit. Off by default; flip env AUDIT_READS=true to record
# every read access of patient PHI from /api/v2/clinical/* endpoints (PIPEDA).

import os as _os


def audit_reads_enabled() -> bool:
    return _os.getenv("AUDIT_READS", "false").lower() in {"1", "true", "yes"}


def record_read(
    session,
    entity_type: str,
    entity_id: Optional[str],
    clinic_id: Optional[str],
) -> None:
    """Insert a single AuditLog row with action='read' if AUDIT_READS is enabled.

    Caller passes its current request-scoped session; we add the log row to it
    so it's committed with the rest of the request. Caller must ensure the
    audit context (user_id/ip/ua) is set via set_audit_context().

    Action 'export' is reserved for bulk dumps (e.g. CSV downloads) — call this
    function with action='export' via set_action below.
    """
    if not audit_reads_enabled():
        return
    log = _make_audit_log("read", entity_type, entity_id, clinic_id, None, None)
    session.add(log)


def record_export(
    session,
    entity_type: str,
    entity_id: Optional[str],
    clinic_id: Optional[str],
) -> None:
    """Same as record_read but with action='export' for bulk PHI extracts."""
    if not audit_reads_enabled():
        return
    log = _make_audit_log("export", entity_type, entity_id, clinic_id, None, None)
    session.add(log)
