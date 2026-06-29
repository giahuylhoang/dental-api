"""Invoice GET detail (lines+payments) and patient-ownership on create."""


def _make_patient(client, phone="5870006666"):
    return client.post("/api/patients", json={
        "first_name": "Ivy", "last_name": "Invoice", "phone": phone,
    }).json()["id"]


def test_get_invoice_includes_lines_and_payments(client):
    pid = _make_patient(client)
    inv = client.post("/api/v2/billing/invoices", json={
        "patient_id": pid,
        "lines": [
            {"procedure_code": "E04", "description": "Exam", "qty": 1, "unit_price": 100},
            {"procedure_code": "X01", "description": "X-ray", "qty": 2, "unit_price": 50},
        ],
    }).json()
    client.post(f"/api/v2/billing/invoices/{inv['id']}/issue")
    client.post(f"/api/v2/billing/invoices/{inv['id']}/payments",
                json={"method": "cash", "amount": 30})

    r = client.get(f"/api/v2/billing/invoices/{inv['id']}")
    assert r.status_code == 200, r.text
    detail = r.json()
    assert [l["sequence"] for l in detail["lines"]] == [1, 2]
    assert detail["lines"][0]["procedure_code"] == "E04"
    assert len(detail["payments"]) == 1
    assert detail["payments"][0]["method"] == "cash"
    assert float(detail["payments"][0]["amount"]) == 30.0


def test_create_invoice_rejects_foreign_patient(client, client_market_mall):
    pid = _make_patient(client)  # belongs to default clinic
    # market-mall clinic must not be able to invoice a default-clinic patient
    r = client_market_mall.post("/api/v2/billing/invoices", json={
        "patient_id": pid,
        "lines": [{"procedure_code": "E04", "qty": 1, "unit_price": 10}],
    }, headers={"X-Clinic-Id": "market-mall-denture"})
    assert r.status_code == 404


def test_create_invoice_accepts_own_patient(client):
    pid = _make_patient(client, phone="5870007777")
    r = client.post("/api/v2/billing/invoices", json={
        "patient_id": pid,
        "lines": [{"procedure_code": "E04", "qty": 1, "unit_price": 10}],
    })
    assert r.status_code == 201, r.text


def test_list_endpoint_stays_summary_only(client):
    pid = _make_patient(client, phone="5870009999")
    client.post("/api/v2/billing/invoices", json={
        "patient_id": pid,
        "lines": [{"procedure_code": "E04", "qty": 1, "unit_price": 10}],
    })
    r = client.get("/api/v2/billing/invoices", params={"patient_id": pid})
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) >= 1
    # list rows are summary-only — no lines/payments embedded
    assert "lines" not in rows[0]
    assert "payments" not in rows[0]


def test_payments_sorted_by_received_at(client):
    pid = _make_patient(client, phone="5870010000")
    inv = client.post("/api/v2/billing/invoices", json={
        "patient_id": pid,
        "lines": [{"procedure_code": "E04", "qty": 1, "unit_price": 100}],
    }).json()
    client.post(f"/api/v2/billing/invoices/{inv['id']}/issue")
    # two payments; assert the detail returns them in received_at order
    client.post(f"/api/v2/billing/invoices/{inv['id']}/payments", json={"method": "cash", "amount": 10})
    client.post(f"/api/v2/billing/invoices/{inv['id']}/payments", json={"method": "card", "amount": 20})
    detail = client.get(f"/api/v2/billing/invoices/{inv['id']}").json()
    times = [p["received_at"] for p in detail["payments"]]
    assert times == sorted(times)
    assert len(detail["payments"]) == 2


def test_from_plan_rejects_foreign_patient(client, client_market_mall):
    pid = _make_patient(client, phone="5870011111")  # default clinic
    r = client_market_mall.post("/api/v2/billing/invoices/from-plan", json={
        "treatment_plan_id": "any-plan-id", "patient_id": pid,
    }, headers={"X-Clinic-Id": "market-mall-denture"})
    assert r.status_code == 404  # patient-ownership check fires before plan lookup
