"""Tests for the public referral endpoints (run with DENTAL_API_INTERNAL_SECRET unset)."""
from database.models import Clinic, Provider, Referral, ReferralDocument
from services.storage import get_storage_backend, reset_storage_backend_cache


def _seed_mm(db):
    db.add(Clinic(id="mm", name="Market Mall", timezone="America/Edmonton",
                  info_email="info@marketmalldentureclinic.com"))
    db.add(Provider(id=1, clinic_id="mm", name="Souheil Khalil", title="Denturist", is_active=True))
    db.commit()


def _create_payload(n_files=2):
    return {
        "patient_name": "Albert Nasser",
        "patient_phone": "825-747-5308",
        "referred_by": "Cedarbrae Family Dental",
        "referrer_contact": "front@cedarbrae.example",
        "proposed_extraction_date": "2026-07-01",
        "tx_plan": "Consultation please! Thanks!",
        "provider_id": None,
        "files": [{"name": f"xray{i}.jpg", "mime": "image/jpeg", "size": 1000} for i in range(n_files)],
        "recaptcha_token": "x",
    }


def test_create_referral_returns_tickets(client, seed_clinic_via_session, monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    seed_clinic_via_session(_seed_mm)

    resp = client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=_create_payload(2))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "NEW"
    assert len(body["uploads"]) == 2
    for i, up in enumerate(body["uploads"]):
        assert up["file_index"] == i
        assert up["object_key"].startswith("mm/referrals/")
        assert up["put_url"]


def test_create_rejects_too_many_and_too_big(client, seed_clinic_via_session, monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    seed_clinic_via_session(_seed_mm)

    too_many = _create_payload(11)
    assert client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=too_many).status_code == 422

    too_big = _create_payload(1)
    too_big["files"][0]["size"] = 16 * 1024 * 1024
    assert client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=too_big).status_code == 422

    bad_mime = _create_payload(1)
    bad_mime["files"][0]["mime"] = "application/x-msdownload"
    assert client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=bad_mime).status_code == 422


def test_complete_records_uploaded_files_only(client, seed_clinic_via_session, monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    monkeypatch.setenv("SEND_CLINIC_BOOKING_EMAIL", "false")  # don't attempt SMTP in test
    seed_clinic_via_session(_seed_mm)

    create = client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=_create_payload(2)).json()
    rid = create["referral_id"]
    keys = [u["object_key"] for u in create["uploads"]]

    # Simulate the browser uploading ONLY the first file directly to storage.
    storage = get_storage_backend()
    storage.put(keys[0], b"\xff\xd8 pretend-jpeg", "image/jpeg")

    resp = client.post(f"/api/public/referrals/{rid}/complete",
                       headers={"X-Clinic-Id": "mm"}, json={"files": [{"object_key": keys[0]}]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "READY"
    assert body["documents"] == 1   # the un-uploaded file's pending row was dropped


def test_complete_unknown_referral_404(client, seed_clinic_via_session, monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    seed_clinic_via_session(_seed_mm)
    resp = client.post("/api/public/referrals/nope/complete", headers={"X-Clinic-Id": "mm"}, json={"files": []})
    assert resp.status_code == 404
