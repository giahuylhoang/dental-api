"""CRUD + tenant isolation + 422 validation tests for /api/v2/scheduling/busy-blocks."""
import pytest

from database.models import Provider, ProviderBusyBlock, DEFAULT_CLINIC_ID


HDR = {"X-Clinic-Id": "default"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def provider_id(client, db_session):
    """Seed one provider in the default clinic. Returns its id."""
    p = Provider(name="Smith", title="Dr", specialty="General",
                 clinic_id=DEFAULT_CLINIC_ID, is_active=True)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p.id


# ---------------------------------------------------------------------------
# Sunny path
# ---------------------------------------------------------------------------

def test_create_returns_201_with_id_and_label(client, provider_id):
    resp = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekday": 2,
              "start_hour": 12, "end_hour": 13, "label": "Lunch"},
        headers=HDR,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["provider_id"] == provider_id
    assert body["weekday"] == 2
    assert body["start_hour"] == 12 and body["start_minute"] == 0
    assert body["end_hour"] == 13 and body["end_minute"] == 0
    assert body["label"] == "Lunch"


def test_list_returns_blocks_for_clinic(client, provider_id):
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekday": 0,
                      "start_hour": 9, "end_hour": 10, "label": "AM"}, headers=HDR)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekday": 4,
                      "start_hour": 17, "end_hour": 18, "label": "PM"}, headers=HDR)
    resp = client.get("/api/v2/scheduling/busy-blocks", headers=HDR)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 2
    # Stable order: provider, weekday, start
    weekdays = [r["weekday"] for r in rows]
    assert weekdays == sorted(weekdays)


def test_list_filters_by_provider_id(client, db_session, provider_id):
    other = Provider(name="Jones", title="Dr", clinic_id=DEFAULT_CLINIC_ID, is_active=True)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekday": 1,
                      "start_hour": 12, "end_hour": 13}, headers=HDR)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": other.id, "weekday": 1,
                      "start_hour": 14, "end_hour": 15}, headers=HDR)
    resp = client.get(f"/api/v2/scheduling/busy-blocks?provider_id={provider_id}", headers=HDR)
    assert resp.status_code == 200
    rows = resp.json()
    assert all(r["provider_id"] == provider_id for r in rows)


def test_update_partial_changes_only_supplied_fields(client, provider_id):
    created = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekday": 2,
              "start_hour": 12, "end_hour": 13, "label": "Lunch"},
        headers=HDR,
    ).json()
    resp = client.put(
        f"/api/v2/scheduling/busy-blocks/{created['id']}",
        json={"label": "Lunch break"},
        headers=HDR,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "Lunch break"
    assert body["weekday"] == 2  # unchanged
    assert body["start_hour"] == 12 and body["end_hour"] == 13


def test_delete_then_get_404(client, provider_id):
    created = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekday": 0,
              "start_hour": 9, "end_hour": 10},
        headers=HDR,
    ).json()
    del_resp = client.delete(f"/api/v2/scheduling/busy-blocks/{created['id']}", headers=HDR)
    assert del_resp.status_code == 204
    upd_resp = client.put(f"/api/v2/scheduling/busy-blocks/{created['id']}",
                          json={"label": "X"}, headers=HDR)
    assert upd_resp.status_code == 404


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

def test_list_returns_blocks_for_clinic_only(client_market_mall, provider_id):
    """default-clinic provider blocks must not leak to market-mall clinic and vice versa."""
    # Create a block under default
    created = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekday": 3,
              "start_hour": 12, "end_hour": 13, "label": "default-lunch"},
        headers=HDR,
    )
    assert created.status_code == 201

    # market-mall sees its own seeded blocks (22 rows from seed_market_mall_denture),
    # NOT the default one we just created.
    mm_resp = client_market_mall.get(
        "/api/v2/scheduling/busy-blocks",
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert mm_resp.status_code == 200
    mm_labels = [r.get("label") for r in mm_resp.json()]
    assert "default-lunch" not in mm_labels
    assert len(mm_resp.json()) >= 22  # seeded count

    # default sees its block (and the one v1-contract test seeded if any in this run).
    default_resp = client_market_mall.get("/api/v2/scheduling/busy-blocks", headers=HDR)
    default_labels = [r.get("label") for r in default_resp.json()]
    assert "default-lunch" in default_labels


def test_create_rejects_provider_in_other_clinic(client_market_mall, db_session):
    """Cannot create a busy block targeting a provider that belongs to another clinic."""
    # Seed a provider only in default — caller is market-mall.
    foreign = Provider(name="Foreign", title="Dr",
                       clinic_id=DEFAULT_CLINIC_ID, is_active=True)
    db_session.add(foreign)
    db_session.commit()
    db_session.refresh(foreign)
    resp = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": foreign.id, "weekday": 0,
              "start_hour": 9, "end_hour": 10},
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert resp.status_code == 404


def test_update_404_when_block_in_other_clinic(client_market_mall, provider_id):
    created = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekday": 0,
              "start_hour": 9, "end_hour": 10},
        headers=HDR,
    ).json()
    # market-mall tries to mutate the default-clinic block
    resp = client_market_mall.put(
        f"/api/v2/scheduling/busy-blocks/{created['id']}",
        json={"label": "stolen"},
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validation (422)
# ---------------------------------------------------------------------------

def test_422_weekday_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekday": 7,
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_hour_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekday": 2,
                             "start_hour": 24, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_minute_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekday": 2,
                             "start_hour": 12, "start_minute": 60,
                             "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_missing_provider_id(client):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"weekday": 2, "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_after_end(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekday": 2,
                             "start_hour": 15, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_equals_end(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekday": 2,
                             "start_hour": 12, "start_minute": 30,
                             "end_hour": 12, "end_minute": 30},
                       headers=HDR)
    assert resp.status_code == 422
