from datetime import datetime
from fastapi import BackgroundTasks
from database.models import Clinic, Provider, Patient, Appointment, AppointmentStatus
from services.notifications import schedule_hold_create_notifications, schedule_hold_confirm_notifications


def _fixtures(db, phone="4035551234"):
    db.add_all([
        Clinic(id="mm", name="MM", timezone="America/Edmonton", booking_notification_email="clinic@mm.com"),
        Provider(clinic_id="mm", name="Soheil", title="Denturist", is_active=True),
    ])
    db.commit()
    prov = db.query(Provider).filter_by(clinic_id="mm").first()
    pat = Patient(id="pat-1", first_name="Jane", last_name="Doe", clinic_id="mm", phone=phone)
    db.add(pat); db.commit()
    appt = Appointment(clinic_id="mm", patient_id="pat-1", provider_id=prov.id,
                       start_time=datetime(2026, 6, 9, 16, 0), end_time=datetime(2026, 6, 9, 17, 0),
                       status=AppointmentStatus.PENDING, source="booking-web-hold")
    db.add(appt); db.commit()
    clinic = db.query(Clinic).get("mm")
    return clinic, prov, pat, appt


def _task_names(bg):
    return [t.func.__name__ for t in bg.tasks]


def test_web_create_schedules_reserved_sms_and_clinic_email(db_session):
    clinic, prov, pat, appt = _fixtures(db_session)
    bg = BackgroundTasks()
    schedule_hold_create_notifications(bg, patient=pat, provider=prov, appointment=appt,
                                       clinic=clinic, service_name="Consultation", source="booking-web-hold")
    names = _task_names(bg)
    assert "send_hold_reserved_sms_delayed" in names
    assert "send_clinic_booking_email_delayed" in names


def test_voice_create_schedules_booked_sms(db_session):
    clinic, prov, pat, appt = _fixtures(db_session)
    appt.source = "voice-hold"
    bg = BackgroundTasks()
    schedule_hold_create_notifications(bg, patient=pat, provider=prov, appointment=appt,
                                       clinic=clinic, service_name="Consultation", source="voice-hold")
    assert "send_booking_sms_delayed" in _task_names(bg)


def test_web_confirm_schedules_booked_sms(db_session):
    clinic, prov, pat, appt = _fixtures(db_session)
    bg = BackgroundTasks()
    schedule_hold_confirm_notifications(bg, patient=pat, provider=prov, appointment=appt,
                                        clinic=clinic, service_name="Consultation", source="booking-web-hold")
    assert "send_booking_sms_delayed" in _task_names(bg)


def test_voice_confirm_is_silent(db_session):
    clinic, prov, pat, appt = _fixtures(db_session)
    bg = BackgroundTasks()
    schedule_hold_confirm_notifications(bg, patient=pat, provider=prov, appointment=appt,
                                        clinic=clinic, service_name="Consultation", source="voice-hold")
    assert _task_names(bg) == []
