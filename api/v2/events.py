"""Server-Sent Events (SSE) for the CRM frontend.

The CRM needs to surface a popup the moment a new appointment is booked —
whether the booking came from a manual entry in the CRM, from the
dental-agent voice AI calling ``POST /api/appointments``, or from any
other write path. SSE is the cheapest way to push without adding
WebSocket or polling overhead.

Architecture (V1, intentionally minimal):

- An in-process ``EventBus`` keeps a list of subscriber ``asyncio.Queue``s
  per clinic_id. Publishing fans the event out to every subscriber.
- ``GET /api/v2/events/stream`` opens a long-lived SSE response, registers
  a queue, and yields each event as ``event: <type>\\ndata: <json>\\n\\n``.
- A keepalive comment (``:keepalive``) is emitted every 25 s so Cloud
  Run's load balancer doesn't time out the idle connection.
- Disconnection (client closes, server unbinds, etc.) drops the queue.

Scaling caveat — single-process only. If the API ever runs on multiple
Cloud Run instances, the write that fires ``publish_appointment_created``
on instance A is invisible to an SSE subscriber on instance B. For the
first ship we pin Cloud Run to ``--max-instances=1``. When traffic
warrants multi-instance, swap the in-process bus for Redis pub/sub or
Google Cloud Pub/Sub — only this file changes.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
from api.main import get_clinic_id as _get_clinic_id_from_header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/events", tags=["v2-events"])


# ---------------------------------------------------------------------------
# In-process event bus
# ---------------------------------------------------------------------------

class _EventBus:
    """Per-clinic asyncio.Queue fan-out. Subscribers get every event
    published for their clinic, decoupled from the writer's request
    lifecycle. Queue is bounded so a stalled subscriber can't grow
    memory unbounded — old events drop on overflow.
    """

    QUEUE_MAX = 256

    def __init__(self) -> None:
        # clinic_id -> list of subscriber queues
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, clinic_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=self.QUEUE_MAX)
        async with self._lock:
            self._subscribers.setdefault(clinic_id, []).append(q)
        logger.info("SSE subscribe clinic=%s subscribers=%d", clinic_id, len(self._subscribers[clinic_id]))
        return q

    async def unsubscribe(self, clinic_id: str, q: asyncio.Queue) -> None:
        async with self._lock:
            subs = self._subscribers.get(clinic_id, [])
            if q in subs:
                subs.remove(q)
            if not subs and clinic_id in self._subscribers:
                del self._subscribers[clinic_id]
        logger.info("SSE unsubscribe clinic=%s remaining=%d", clinic_id, len(self._subscribers.get(clinic_id, [])))

    def publish(self, clinic_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        """Fire-and-forget. Skips silently if no subscribers for the
        clinic — that's the steady state on a quiet day. Overflowing
        queues drop the event (with a warning) rather than block the
        writer's request thread.
        """
        subs = list(self._subscribers.get(clinic_id, ()))  # snapshot
        if not subs:
            return
        event = {"type": event_type, "data": payload}
        for q in subs:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    "SSE queue full for clinic=%s — dropping event type=%s",
                    clinic_id, event_type,
                )


# Module-level singleton. Importers can call ``publish_appointment_created``
# without thinking about bus lifecycle.
_bus = _EventBus()


def publish_appointment_created(clinic_id: str, payload: Dict[str, Any]) -> None:
    """Publish an ``appointment.created`` event to every SSE subscriber
    of ``clinic_id``. Caller is responsible for assembling a JSON-safe
    payload (datetimes already serialized to ISO strings, etc.) — this
    keeps the bus itself decoupled from ORM types.
    """
    _bus.publish(clinic_id, "appointment.created", payload)


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------

KEEPALIVE_INTERVAL_SECONDS = 25.0


async def _sse_stream(request: Request, clinic_id: str) -> AsyncIterator[bytes]:
    q = await _bus.subscribe(clinic_id)
    # Initial hello — confirms the connection is open and tells the
    # frontend which clinic it's subscribed to (defensive: catches the
    # case where the URL says one clinic but the header sent another).
    yield _format_event("connected", {"clinic_id": clinic_id}).encode()
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(q.get(), timeout=KEEPALIVE_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                yield b":keepalive\n\n"
                continue
            yield _format_event(event["type"], event["data"]).encode()
    finally:
        await _bus.unsubscribe(clinic_id, q)


def _format_event(event_type: str, data: Dict[str, Any]) -> str:
    """SSE wire format: ``event: <type>\\ndata: <json>\\n\\n``.

    JSON serialization with ``default=str`` so we tolerate datetimes,
    Decimals, and other non-primitive values that creep through the
    appointment payload.
    """
    body = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {body}\n\n"


@router.get("/stream")
async def stream(
    request: Request,
    clinic_id: str = Query(
        None,
        description=(
            "Clinic id to subscribe for. Required when the browser "
            "EventSource can't send the X-Clinic-Id header (which is "
            "always — EventSource has no custom-header support). "
            "Falls back to the X-Clinic-Id header for non-browser "
            "callers (curl, server-to-server)."
        ),
    ),
    db: Session = Depends(get_db),
):
    """Open a long-lived SSE connection scoped to the caller's clinic.

    The frontend opens this with ``new EventSource(`${API_BASE}
    /api/v2/events/stream?clinic_id=${clinicId}`)``. EventSource cannot
    set custom headers, so we accept ``clinic_id`` as a query param
    and validate that the Clinic row exists (404 otherwise).

    Each emitted event has a ``type`` (e.g. ``appointment.created``)
    and a JSON ``data`` payload the client can ``JSON.parse``. The
    connection survives until the client disconnects or the load
    balancer times out (Cloud Run idle timeout 15 min — keepalive
    every 25 s prevents that).

    Multi-tenant scoping: a subscriber ONLY sees events for the
    clinic in their query param. The bus segregates per-clinic
    queues, so no cross-tenant leakage is possible.
    """
    # Resolve clinic_id: query param wins, header is the fallback,
    # default is the DEFAULT_CLINIC_ID sentinel.
    resolved = (clinic_id or _get_clinic_id_from_header(request)).strip() or DEFAULT_CLINIC_ID
    clinic = db.query(Clinic).filter(Clinic.id == resolved).first()
    if clinic is None:
        raise HTTPException(status_code=404, detail=f"Clinic not found: {resolved}")
    return StreamingResponse(
        _sse_stream(request, clinic.id),
        media_type="text/event-stream",
        headers={
            # Disable proxy buffering so events flush immediately rather
            # than waiting for a 4 KB buffer fill. Required for nginx,
            # Cloud Run's frontend doesn't buffer SSE but the header is
            # harmless there.
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
