"""Shared notification recipient resolution + referral dispatch (attach vs links)."""
import types

import clients.email_client as ec
import services.notifications as notif
from services.storage import LocalBackend


def _clinic(**kw):
    base = dict(booking_notification_email=None)
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_booking_recipients_add_info_and_dedupe(monkeypatch):
    monkeypatch.delenv("BOOKING_NOTIFICATION_TO", raising=False)
    monkeypatch.setenv("CLINIC_INFO_EMAIL", "info@clinic.com")
    c = _clinic(booking_notification_email="front@clinic.com")
    assert ec.resolve_clinic_recipients(c, kind="booking") == ["front@clinic.com", "info@clinic.com"]

    # Same address in booking field + info env → deduped (case-insensitive).
    c2 = _clinic(booking_notification_email="Info@Clinic.com")
    assert ec.resolve_clinic_recipients(c2, kind="booking") == ["Info@Clinic.com"]


def test_referral_recipients_env_info_and_conditional_fallback(monkeypatch):
    monkeypatch.delenv("REFERRAL_NOTIFICATION_TO", raising=False)
    monkeypatch.setenv("CLINIC_INFO_EMAIL", "info@clinic.com")
    c = _clinic(booking_notification_email="front@clinic.com")
    # info@ configured → ONLY info@; the clinic booking email is NOT cc'd.
    assert ec.resolve_clinic_recipients(c, kind="referral") == ["info@clinic.com"]

    # REFERRAL_NOTIFICATION_TO leads when set.
    monkeypatch.setenv("REFERRAL_NOTIFICATION_TO", "referrals@clinic.com")
    assert ec.resolve_clinic_recipients(c, kind="referral")[0] == "referrals@clinic.com"

    # Nothing configured → fall back to the per-clinic booking email.
    monkeypatch.delenv("REFERRAL_NOTIFICATION_TO", raising=False)
    monkeypatch.delenv("CLINIC_INFO_EMAIL", raising=False)
    assert ec.resolve_clinic_recipients(c, kind="referral") == ["front@clinic.com"]


def _capture_deliver(monkeypatch):
    sent = []
    monkeypatch.setattr(ec, "_deliver_message", lambda msg: (sent.append(msg) or True))
    monkeypatch.setattr(ec, "SEND_CLINIC_BOOKING_EMAIL", True)
    return sent


def test_dispatch_attaches_small_files(tmp_path, monkeypatch):
    sent = _capture_deliver(monkeypatch)
    storage = LocalBackend(root=tmp_path)
    storage.put("c/referrals/r1/a.jpg", b"img-bytes", "image/jpeg")
    files = [{"object_key": "c/referrals/r1/a.jpg", "original_name": "a.jpg",
              "mime": "image/jpeg", "size": len(b"img-bytes")}]
    ok = notif.dispatch_referral_created(
        recipients=["info@clinic.com"], clinic_name="MM",
        referral={"patient_name": "Albert", "referred_by": "Cedarbrae"},
        files=files, storage=storage,
    )
    assert ok is True and len(sent) == 1
    assert sent[0].is_multipart()
    assert [p.get_filename() for p in sent[0].iter_attachments()] == ["a.jpg"]


def test_dispatch_uses_links_when_over_budget(tmp_path, monkeypatch):
    sent = _capture_deliver(monkeypatch)
    monkeypatch.setattr(notif, "_REFERRAL_ATTACH_BUDGET", 1)  # force link mode
    storage = LocalBackend(root=tmp_path)
    storage.put("c/referrals/r1/big.jpg", b"x" * 50, "image/jpeg")
    files = [{"object_key": "c/referrals/r1/big.jpg", "original_name": "big.jpg",
              "mime": "image/jpeg", "size": 50}]
    ok = notif.dispatch_referral_created(
        recipients=["info@clinic.com"], clinic_name="MM",
        referral={"patient_name": "Albert", "referred_by": "Cedarbrae"},
        files=files, storage=storage,
    )
    assert ok is True and len(sent) == 1
    assert not sent[0].is_multipart()  # no attachments
    body = sent[0].get_content()
    assert "secure download links" in body and "big.jpg" in body
