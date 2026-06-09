"""PUT /api/appointments/{id}/{cancel,status,reschedule} accepts and records source.

Task B2 of the SMS reminder + Telnyx migration plan. The
AppointmentMutationSource enum lets the Task B8 SMS-reply pipeline call
PUT /cancel with {"source": "outbound_sms_reply"} so we can distinguish
that mutation from inbound-call-driven ones (logged for now; persisted
in a follow-up).
"""
from datetime import time as _time

from database.models import (
    DEFAULT_CLINIC_ID,
    Patient,
    Provider,
    Service,
)
from database.v1_1.models import ClinicOperatingHours


def _seed_default(db_session):
    """Seed providers, a service, and Mon-Fri 9-5 operating hours on the default clinic."""
    p1 = Provider(
        id=1,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Johnson",
        title="Dr",
        specialty="General",
        is_active=True,
    )
    p2 = Provider(
        id=2,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Smith",
        title="Mr",
        specialty="Dental Assistant",
        is_active=True,
    )
    svc = Service(
        id=1,
        clinic_id=DEFAULT_CLINIC_ID,
        name="Routine Cleaning",
        description="Test service",
        duration_min=60,
        base_price=150.0,
    )
    db_session.add_all([p1, p2, svc])
    for dow in (0, 1, 2, 3, 4):
        if not db_session.query(ClinicOperatingHours).filter_by(
            clinic_id=DEFAULT_CLINIC_ID, day_of_week=dow
        ).first():
            db_session.add(
                ClinicOperatingHours(
                    clinic_id=DEFAULT_CLINIC_ID,
                    day_of_week=dow,
                    open_at=_time(9, 0),
                    close_at=_time(17, 0),
                    is_closed=False,
                )
            )
    db_session.commit()
    return p1, p2, svc


def _create_patient(client):
    resp = client.post(
        "/api/patients",
        json={"first_name": "Alice", "last_name": "Example", "consent_approved": True},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _create_appointment(client, *, patient_id, provider_id, service_id, service_name,
                       start="2026-03-10T10:00:00-06:00", end="2026-03-10T11:00:00-06:00"):
    resp = client.post(
        "/api/appointments",
        json={
            "start_time": start,
            "end_time": end,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "service_id": service_id,
            "patient_name": "Alice Example",
            "service_name": service_name,
            "reason": "Checkup",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["appointment_id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cancel_with_source_outbound_sms_reply_returns_200(client, db_session):
    """Endpoint accepts the source field; status updates succeed."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
    )

    resp = client.put(
        f"/api/appointments/{appt_id}/cancel",
        json={"source": "outbound_sms_reply"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "CANCELLED"


def test_cancel_without_source_defaults_to_inbound_call_returns_200(client, db_session):
    """Back-compat: existing callers that don't send source still work."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
    )

    # No body at all — body is optional and source defaults to inbound_call.
    resp = client.put(f"/api/appointments/{appt_id}/cancel")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "CANCELLED"

    # Sanity: empty body works the same.
    appt_id_2 = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
        start="2026-03-11T10:00:00-06:00",
        end="2026-03-11T11:00:00-06:00",
    )
    resp2 = client.put(f"/api/appointments/{appt_id_2}/cancel", json={})
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["status"] == "CANCELLED"


def test_cancel_with_bogus_source_returns_422(client, db_session):
    """Pydantic validates against the enum and rejects unknown values."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
    )

    resp = client.put(
        f"/api/appointments/{appt_id}/cancel",
        json={"source": "definitely_not_a_real_source"},
    )
    assert resp.status_code == 422, resp.text


def test_status_update_with_source_returns_200(client, db_session):
    """Status update endpoint also accepts source."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
    )

    resp = client.put(
        f"/api/appointments/{appt_id}/status",
        json={"status": "CONFIRMED", "source": "outbound_sms_reply"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "CONFIRMED"


def test_status_update_with_bogus_source_returns_422(client, db_session):
    """Status update also rejects unknown source values."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
    )

    resp = client.put(
        f"/api/appointments/{appt_id}/status",
        json={"status": "CONFIRMED", "source": "not_a_source"},
    )
    assert resp.status_code == 422, resp.text


def test_reschedule_with_source_returns_200(client, db_session):
    """Reschedule endpoint also accepts source (carried on AppointmentCreateRequest)."""
    p1, _, svc = _seed_default(db_session)
    patient_id = _create_patient(client)
    appt_id = _create_appointment(
        client,
        patient_id=patient_id,
        provider_id=p1.id,
        service_id=svc.id,
        service_name=svc.name,
        start="2026-03-12T10:00:00-06:00",
        end="2026-03-12T11:00:00-06:00",
    )

    resp = client.put(
        f"/api/appointments/{appt_id}/reschedule",
        json={
            "start_time": "2026-03-12T13:00:00-06:00",
            "end_time": "2026-03-12T14:00:00-06:00",
            "patient_id": patient_id,
            "provider_id": p1.id,
            "service_id": svc.id,
            "patient_name": "Alice Example",
            "service_name": svc.name,
            "reason": "Rescheduled via SMS reply",
            "source": "outbound_sms_reply",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "RESCHEDULED"
    assert "new_appointment_id" in body
