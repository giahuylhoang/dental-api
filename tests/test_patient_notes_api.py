"""Patient CRM notes CRUD + clinic scoping."""

MM = {"X-Clinic-Id": "market-mall-denture"}  # client_market_mall is the same


def _make_patient(client):
    r = client.post("/api/patients", json={
        "first_name": "Nina", "last_name": "Note", "phone": "5870001111",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_create_and_list_notes_newest_first(client):
    pid = _make_patient(client)
    client.post(f"/api/v2/clinical/patients/{pid}/notes", json={"body": "first"})
    client.post(f"/api/v2/clinical/patients/{pid}/notes", json={"body": "second"})

    r = client.get(f"/api/v2/clinical/patients/{pid}/notes")
    assert r.status_code == 200, r.text
    bodies = [n["body"] for n in r.json()]
    assert bodies == ["second", "first"]  # newest-first


def test_create_note_returns_201_and_fields(client):
    pid = _make_patient(client)
    r = client.post(
        f"/api/v2/clinical/patients/{pid}/notes",
        json={"body": "hello", "author_id": "u-1"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["body"] == "hello"
    assert data["author_id"] == "u-1"
    assert data["patient_id"] == pid
    assert data["id"]


def test_patch_note_edits_body(client):
    pid = _make_patient(client)
    note_id = client.post(
        f"/api/v2/clinical/patients/{pid}/notes", json={"body": "typo"}
    ).json()["id"]

    r = client.patch(f"/api/v2/clinical/patient-notes/{note_id}", json={"body": "fixed"})
    assert r.status_code == 200, r.text
    assert r.json()["body"] == "fixed"


def test_delete_note_then_missing(client):
    pid = _make_patient(client)
    note_id = client.post(
        f"/api/v2/clinical/patients/{pid}/notes", json={"body": "bye"}
    ).json()["id"]

    assert client.delete(f"/api/v2/clinical/patient-notes/{note_id}").status_code == 204
    remaining = client.get(f"/api/v2/clinical/patients/{pid}/notes").json()
    assert all(n["id"] != note_id for n in remaining)
    assert client.patch(
        f"/api/v2/clinical/patient-notes/{note_id}", json={"body": "x"}
    ).status_code == 404


def test_notes_are_clinic_scoped(client, client_market_mall):
    pid = _make_patient(client)
    note_id = client.post(
        f"/api/v2/clinical/patients/{pid}/notes", json={"body": "secret"}
    ).json()["id"]
    assert client_market_mall.patch(
        f"/api/v2/clinical/patient-notes/{note_id}", json={"body": "x"}, headers=MM
    ).status_code == 404
    assert client_market_mall.delete(
        f"/api/v2/clinical/patient-notes/{note_id}", headers=MM
    ).status_code == 404
