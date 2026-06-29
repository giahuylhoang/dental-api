"""Server-verified patient document upload flow."""
import hashlib

import pytest

from services.storage import get_storage_backend, reset_storage_backend_cache


@pytest.fixture(autouse=True)
def _local_storage(monkeypatch, tmp_path):
    # Force the LocalBackend rooted in a temp dir for each test.
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    backend = get_storage_backend()
    backend.root = tmp_path  # LocalBackend.root
    yield
    reset_storage_backend_cache()


def _make_patient(client, phone="5870002222"):
    r = client.post("/api/patients", json={
        "first_name": "Dana", "last_name": "Doc", "phone": phone,
    })
    return r.json()["id"]


def test_request_upload_returns_ticket(client):
    pid = _make_patient(client)
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "xray.png", "mime": "image/png", "size_bytes": 1024, "kind": "xray"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["upload_url"]
    assert data["storage_key"].startswith(f"default/patients/{pid}/")
    assert data["storage_key"].endswith(".png")
    assert data["storage_backend"] == "local"


def test_request_upload_rejects_bad_mime_and_oversize(client):
    pid = _make_patient(client)
    bad_mime = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "x.exe", "mime": "application/x-msdownload", "size_bytes": 10, "kind": "other"},
    )
    assert bad_mime.status_code == 400
    oversize = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "x.png", "mime": "image/png", "size_bytes": 10**9, "kind": "xray"},
    )
    assert oversize.status_code == 400


def test_complete_records_document_with_server_derived_values(client):
    pid = _make_patient(client)
    ticket = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "scan.pdf", "mime": "application/pdf", "size_bytes": 5, "kind": "other"},
    ).json()
    payload = b"hello"
    get_storage_backend().put(ticket["storage_key"], payload, content_type="application/pdf")

    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": ticket["storage_key"], "kind": "other", "original_name": "scan.pdf"},
    )
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["content_sha256"] == hashlib.sha256(payload).hexdigest()
    assert doc["size_bytes"] == len(payload)
    assert doc["original_name"] == "scan.pdf"
    assert doc["storage_backend"] == "local"

    listed = client.get(f"/api/v2/clinical/patients/{pid}/documents").json()
    assert any(d["id"] == doc["id"] for d in listed)


def test_complete_missing_object_400(client):
    pid = _make_patient(client)
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": f"default/patients/{pid}/ghost.png", "kind": "xray"},
    )
    assert r.status_code == 400


def test_complete_rejects_key_outside_patient_prefix(client):
    pid = _make_patient(client)
    other = _make_patient(client, phone="5870003333")
    key = f"default/patients/{other}/sneaky.png"
    get_storage_backend().put(key, b"x", content_type="image/png")
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": key, "kind": "xray"},
    )
    assert r.status_code in (400, 403)


def test_same_file_dedups_per_patient_but_not_across_patients(client):
    p1 = _make_patient(client, phone="5870004444")
    p2 = _make_patient(client, phone="5870005555")
    payload = b"shared-bytes"

    def attach(pid):
        t = client.post(
            f"/api/v2/clinical/patients/{pid}/documents/request-upload",
            json={"filename": "a.png", "mime": "image/png", "size_bytes": len(payload), "kind": "xray"},
        ).json()
        get_storage_backend().put(t["storage_key"], payload, content_type="image/png")
        return client.post(
            f"/api/v2/clinical/patients/{pid}/documents/complete",
            json={"storage_key": t["storage_key"], "kind": "xray"},
        ).json()["id"]

    p1_doc_a = attach(p1)
    p1_doc_b = attach(p1)  # same bytes, same patient → dedup
    assert p1_doc_a == p1_doc_b
    p2_doc = attach(p2)    # same bytes, different patient → separate row
    assert p2_doc != p1_doc_a


def test_download_url_scoped_to_clinic(client, client_market_mall):
    pid = _make_patient(client)
    t = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "a.png", "mime": "image/png", "size_bytes": 3, "kind": "xray"},
    ).json()
    get_storage_backend().put(t["storage_key"], b"abc", content_type="image/png")
    doc_id = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": t["storage_key"], "kind": "xray"},
    ).json()["id"]

    ok = client.get(f"/api/v2/clinical/documents/{doc_id}/download")
    assert ok.status_code == 200 and ok.json()["download_url"]
    # other clinic cannot resolve it (explicit header — client_market_mall shares the same DB)
    assert client_market_mall.get(
        f"/api/v2/clinical/documents/{doc_id}/download",
        headers={"X-Clinic-Id": "market-mall-denture"},
    ).status_code == 404


def test_complete_rejects_oversize_object(client, monkeypatch):
    import api.v2.clinical.router as clinical_router
    pid = _make_patient(client, phone="5870008888")
    t = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": "a.png", "mime": "image/png", "size_bytes": 10, "kind": "xray"},
    ).json()
    get_storage_backend().put(t["storage_key"], b"x" * 50, content_type="image/png")
    # Shrink the server-side cap so the already-stored object is now "too large".
    monkeypatch.setattr(clinical_router, "MAX_DOC_BYTES", 10)
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": t["storage_key"], "kind": "xray"},
    )
    assert r.status_code == 400
    # the oversize object was deleted (no orphan)
    assert get_storage_backend().stat(t["storage_key"]) is None
