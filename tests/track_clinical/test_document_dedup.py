"""Test document deduplication via the server-verified upload flow."""
import pytest

from tests.track_clinical.conftest import make_patient
from services.storage import get_storage_backend, reset_storage_backend_cache

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}


@pytest.fixture(autouse=True)
def _local_storage(monkeypatch, tmp_path):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    get_storage_backend().root = tmp_path  # LocalBackend.root
    yield
    reset_storage_backend_cache()


def _upload(client, pid, payload: bytes, *, kind="xray", filename="x.png", mime="image/png"):
    """Drive request-upload -> (simulated browser PUT) -> complete; return the Document id."""
    ticket = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/request-upload",
        json={"filename": filename, "mime": mime, "size_bytes": len(payload), "kind": kind},
        headers=HEADERS,
    ).json()
    get_storage_backend().put(ticket["storage_key"], payload, content_type=mime)
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/documents/complete",
        json={"storage_key": ticket["storage_key"], "kind": kind},
        headers=HEADERS,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_same_sha_returns_existing(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    payload = b"identical-bytes"
    first = _upload(client_market_mall, pid, payload)
    second = _upload(client_market_mall, pid, payload)  # same bytes, same patient
    assert second == first  # dedup returns the same row


def test_different_sha_creates_new(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    first = _upload(client_market_mall, pid, b"bytes-one")
    second = _upload(client_market_mall, pid, b"bytes-two-different")
    assert second != first


def test_list_documents(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    _upload(client_market_mall, pid, b"a-document")
    r = client_market_mall.get(f"/api/v2/clinical/patients/{pid}/documents", headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) >= 1
