"""Test clinical note locking and amendment chain."""
from tests.track_clinical.conftest import make_patient

CLINIC = "market-mall-denture"
HEADERS = {"X-Clinic-Id": CLINIC}


def _create_note(client, patient_id):
    r = client.post("/api/v2/clinical/notes",
                    json={"patient_id": patient_id, "soap_subjective": "Patient reports pain"},
                    headers=HEADERS)
    assert r.status_code == 201
    return r.json()


def test_patch_unlocked_note(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    note = _create_note(client_market_mall, pid)
    r = client_market_mall.patch(f"/api/v2/clinical/notes/{note['id']}",
                                 json={"soap_objective": "Swelling observed"},
                                 headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["soap_objective"] == "Swelling observed"


def test_patch_locked_note_returns_409(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    note = _create_note(client_market_mall, pid)
    client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/lock", headers=HEADERS)
    r = client_market_mall.patch(f"/api/v2/clinical/notes/{note['id']}",
                                 json={"soap_objective": "Should fail"},
                                 headers=HEADERS)
    assert r.status_code == 409


def test_lock_sets_locked_at(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    note = _create_note(client_market_mall, pid)
    r = client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/lock", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["locked_at"] is not None


def test_amend_creates_supersedes_chain(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    note = _create_note(client_market_mall, pid)
    # Lock original
    client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/lock", headers=HEADERS)

    # Amend
    r = client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/amend",
                                json={"soap_plan": "Updated plan"},
                                headers=HEADERS)
    assert r.status_code == 201
    amendment = r.json()
    assert amendment["supersedes_id"] == note["id"]
    assert amendment["soap_plan"] == "Updated plan"
    assert amendment["id"] != note["id"]


def test_both_notes_readable_after_amend(client_market_mall):
    pid = make_patient(client_market_mall, CLINIC)
    note = _create_note(client_market_mall, pid)
    client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/lock", headers=HEADERS)
    client_market_mall.post(f"/api/v2/clinical/notes/{note['id']}/amend",
                            json={"soap_plan": "Amendment"},
                            headers=HEADERS)

    r = client_market_mall.get("/api/v2/clinical/notes",
                               params={"patient_id": pid}, headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) == 2
