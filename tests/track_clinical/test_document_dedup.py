"""Test document deduplication."""
from tests.track_clinical.conftest import make_patient

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}

DOC = {
    "kind": "xray",
    "storage_url": "https://storage.example.com/xray1.jpg",
    "content_sha256": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
    "mime": "image/jpeg",
    "size_bytes": 102400,
}


def test_same_sha_returns_existing(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    r1 = client_market_mall.post(f"/api/v2/clinical/patients/{pid}/documents",
                                 json=DOC, headers=HEADERS)
    assert r1.status_code == 201
    doc_id = r1.json()["id"]

    # Post same sha again
    r2 = client_market_mall.post(f"/api/v2/clinical/patients/{pid}/documents",
                                 json={**DOC, "storage_url": "https://other.example.com/different.jpg"},
                                 headers=HEADERS)
    assert r2.status_code == 201
    assert r2.json()["id"] == doc_id  # same row returned


def test_different_sha_creates_new(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    r1 = client_market_mall.post(f"/api/v2/clinical/patients/{pid}/documents",
                                 json=DOC, headers=HEADERS)
    assert r1.status_code == 201

    r2 = client_market_mall.post(f"/api/v2/clinical/patients/{pid}/documents",
                                 json={**DOC, "content_sha256": "aaaa" * 16},
                                 headers=HEADERS)
    assert r2.status_code == 201
    assert r2.json()["id"] != r1.json()["id"]


def test_list_documents(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    client_market_mall.post(f"/api/v2/clinical/patients/{pid}/documents", json=DOC, headers=HEADERS)
    r = client_market_mall.get(f"/api/v2/clinical/patients/{pid}/documents", headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) >= 1
