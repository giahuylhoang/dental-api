"""Tests for the public referral endpoints (run with DENTAL_API_INTERNAL_SECRET unset)."""
import api.dependencies.auth as auth
from database.models import Clinic, Provider, ReferralStatus
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


def _reset(monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()


def test_create_referral_returns_tickets(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
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


def test_create_validation(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
    seed_clinic_via_session(_seed_mm)
    H = {"X-Clinic-Id": "mm"}

    assert client.post("/api/public/referrals", headers=H, json=_create_payload(11)).status_code == 422
    too_big = _create_payload(1); too_big["files"][0]["size"] = 16 * 1024 * 1024
    assert client.post("/api/public/referrals", headers=H, json=too_big).status_code == 422
    bad_mime = _create_payload(1); bad_mime["files"][0]["mime"] = "application/x-msdownload"
    assert client.post("/api/public/referrals", headers=H, json=bad_mime).status_code == 422
    bad_prov = _create_payload(0); bad_prov["provider_id"] = 999
    assert client.post("/api/public/referrals", headers=H, json=bad_prov).status_code == 422
    bad_date = _create_payload(0); bad_date["proposed_extraction_date"] = "soon"
    assert client.post("/api/public/referrals", headers=H, json=bad_date).status_code == 422


def test_complete_records_only_uploaded_and_is_idempotent(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setenv("SEND_CLINIC_BOOKING_EMAIL", "false")
    seed_clinic_via_session(_seed_mm)

    created = client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=_create_payload(2)).json()
    rid = created["referral_id"]
    keys = [u["object_key"] for u in created["uploads"]]

    # Browser uploaded ONLY the first file.
    get_storage_backend().put(keys[0], b"\xff\xd8 jpeg", "image/jpeg")

    body = client.post(f"/api/public/referrals/{rid}/complete", headers={"X-Clinic-Id": "mm"},
                       json={"files": [{"object_key": keys[0], "name": "xray0.jpg", "mime": "image/jpeg"},
                                       {"object_key": keys[1], "name": "xray1.jpg", "mime": "image/jpeg"}]}).json()
    assert body["status"] == "READY"
    assert body["documents"] == 1   # second key never uploaded → not recorded

    # Idempotent: second call no-ops, count unchanged, still READY.
    body2 = client.post(f"/api/public/referrals/{rid}/complete", headers={"X-Clinic-Id": "mm"},
                        json={"files": [{"object_key": keys[0], "name": "x", "mime": "image/jpeg"}]}).json()
    assert body2["status"] == "READY"
    assert body2["documents"] == 1


def test_complete_rejects_foreign_and_bad_mime(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setenv("SEND_CLINIC_BOOKING_EMAIL", "false")
    seed_clinic_via_session(_seed_mm)
    created = client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=_create_payload(1)).json()
    rid = created["referral_id"]
    storage = get_storage_backend()
    # A forged key NOT under this referral's prefix, plus a real upload with a bad mime.
    storage.put("mm/referrals/SOMEONE-ELSE/evil.jpg", b"x", "image/jpeg")
    storage.put(created["uploads"][0]["object_key"], b"x", "image/jpeg")
    body = client.post(f"/api/public/referrals/{rid}/complete", headers={"X-Clinic-Id": "mm"}, json={"files": [
        {"object_key": "mm/referrals/SOMEONE-ELSE/evil.jpg", "name": "evil", "mime": "image/jpeg"},
        {"object_key": created["uploads"][0]["object_key"], "name": "ok", "mime": "application/x-msdownload"},
    ]}).json()
    assert body["status"] == "READY"
    assert body["documents"] == 0  # foreign key rejected; bad-mime file deleted+skipped


def test_complete_unknown_referral_404(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
    seed_clinic_via_session(_seed_mm)
    resp = client.post("/api/public/referrals/nope/complete", headers={"X-Clinic-Id": "mm"}, json={"files": []})
    assert resp.status_code == 404


def test_internal_secret_enforced_when_configured(client, seed_clinic_via_session, monkeypatch):
    _reset(monkeypatch)
    seed_clinic_via_session(_seed_mm)
    monkeypatch.setattr(auth, "INTERNAL_SECRET", "the-secret")
    # No X-Internal-Secret header → 401 (fails closed when a secret is configured).
    resp = client.post("/api/public/referrals", headers={"X-Clinic-Id": "mm"}, json=_create_payload(0))
    assert resp.status_code == 401
    # Correct secret → allowed.
    ok = client.post("/api/public/referrals",
                     headers={"X-Clinic-Id": "mm", "X-Internal-Secret": "the-secret"},
                     json=_create_payload(0))
    assert ok.status_code == 200
