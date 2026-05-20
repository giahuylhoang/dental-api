"""PMS Track P0 — backend gap-fill tests."""
import io


CLINIC_HEADERS = {"X-Clinic-Id": "default"}


def _create_patient(client):
    r = client.post("/api/patients", json={
        "first_name": "Test",
        "last_name": "Patient",
        "phone": "5550001111",
        "email": "test@example.com",
        "date_of_birth": "1990-01-01",
    }, headers=CLINIC_HEADERS)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_documents_upload_and_dedup(client):
    patient_id = _create_patient(client)
    content = b"fake-xray-bytes"

    r1 = client.post(
        "/api/v2/clinical/documents/upload",
        data={"kind": "xray", "patient_id": patient_id},
        files={"file": ("xray.jpg", io.BytesIO(content), "image/jpeg")},
        headers=CLINIC_HEADERS,
    )
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["deduped"] is False
    assert d1["kind"] == "xray"
    assert d1["patient_id"] == patient_id

    # Upload same bytes again — should dedup
    r2 = client.post(
        "/api/v2/clinical/documents/upload",
        data={"kind": "xray", "patient_id": patient_id},
        files={"file": ("xray2.jpg", io.BytesIO(content), "image/jpeg")},
        headers=CLINIC_HEADERS,
    )
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["deduped"] is True
    assert d2["id"] == d1["id"]


def test_tooth_chart_get_returns_32_entries(client):
    patient_id = _create_patient(client)
    r = client.get(
        f"/api/v2/clinical/patients/{patient_id}/tooth-chart",
        headers=CLINIC_HEADERS,
    )
    assert r.status_code == 200, r.text
    entries = r.json()
    assert len(entries) == 32
    for e in entries:
        assert e["status"] == "present"
        assert e["surface_notes"] is None


def test_tooth_chart_post_upserts(client):
    patient_id = _create_patient(client)

    r = client.post(
        f"/api/v2/clinical/patients/{patient_id}/tooth-chart",
        json=[{"tooth_number": 14, "status": "missing"}],
        headers=CLINIC_HEADERS,
    )
    assert r.status_code == 200, r.text
    entries = r.json()
    assert len(entries) == 32

    by_tooth = {e["tooth_number"]: e for e in entries}
    assert by_tooth[14]["status"] == "missing"
    assert by_tooth[1]["status"] == "present"


def test_insurance_put_and_delete(client):
    patient_id = _create_patient(client)

    # POST insurance
    r = client.post(
        f"/api/v2/clinical/patients/{patient_id}/insurance",
        json={"carrier": "Sun Life", "is_primary": True},
        headers=CLINIC_HEADERS,
    )
    assert r.status_code == 201, r.text
    ins_id = r.json()["id"]

    # PUT to update carrier
    r2 = client.put(
        f"/api/v2/clinical/patients/{patient_id}/insurance/{ins_id}",
        json={"carrier": "Manulife", "is_primary": True},
        headers=CLINIC_HEADERS,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["carrier"] == "Manulife"

    # DELETE
    r3 = client.delete(
        f"/api/v2/clinical/patients/{patient_id}/insurance/{ins_id}",
        headers=CLINIC_HEADERS,
    )
    assert r3.status_code == 204, r3.text

    # GET returns empty
    r4 = client.get(
        f"/api/v2/clinical/patients/{patient_id}/insurance",
        headers=CLINIC_HEADERS,
    )
    assert r4.status_code == 200, r4.text
    assert r4.json() == []


def test_denture_case_implants_create_and_list(client):
    patient_id = _create_patient(client)

    # Create denture case
    r = client.post(
        "/api/v2/clinical/denture-cases",
        json={"patient_id": patient_id, "arch": "upper", "case_type": "implant_retained"},
        headers=CLINIC_HEADERS,
    )
    assert r.status_code == 201, r.text
    case_id = r.json()["id"]

    # POST implant
    r2 = client.post(
        f"/api/v2/clinical/denture-cases/{case_id}/implants",
        json={
            "tooth_position": 14,
            "vendor": "Nobel Biocare",
            "lot_number": "LOT-001",
        },
        headers=CLINIC_HEADERS,
    )
    assert r2.status_code == 201, r2.text
    imp = r2.json()
    assert imp["vendor"] == "Nobel Biocare"
    assert imp["tooth_position"] == 14

    # GET list
    r3 = client.get(
        f"/api/v2/clinical/denture-cases/{case_id}/implants",
        headers=CLINIC_HEADERS,
    )
    assert r3.status_code == 200, r3.text
    assert len(r3.json()) == 1


def test_invoice_from_plan(client):
    patient_id = _create_patient(client)

    # Create treatment plan with items
    r = client.post(
        "/api/v2/treatment-plans",
        json={
            "patient_id": patient_id,
            "items": [
                {"procedure_code": "01101", "description": "Exam", "fee": 100.0},
                {"procedure_code": "02141", "description": "Filling", "fee": 200.0},
            ],
        },
        headers=CLINIC_HEADERS,
    )
    assert r.status_code in (200, 201), r.text
    plan_id = r.json()["id"]

    # POST from-plan
    r2 = client.post(
        "/api/v2/billing/invoices/from-plan",
        json={"treatment_plan_id": plan_id, "patient_id": patient_id, "gst_rate": 0.05},
        headers=CLINIC_HEADERS,
    )
    assert r2.status_code == 201, r2.text
    inv = r2.json()
    assert inv["status"] == "draft"
    assert inv["patient_id"] == patient_id
    # subtotal = 300, gst = 15, total = 315
    assert abs(inv["subtotal"] - 300.0) < 0.01
    assert abs(inv["total"] - 315.0) < 0.01
