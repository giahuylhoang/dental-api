"""CRUD + tenant isolation + 422 validation tests for /api/v2/scheduling/busy-blocks.

v2 shape: writes accept either `weekdays: [int, ...]` (recurring) OR
`specific_date: YYYY-MM-DD` (one-off). Recurring rules may carry an optional
`recurrence_until: YYYY-MM-DD` bound.
"""
from datetime import date, timedelta

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


def _future_date(days: int = 30) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# Sunny path
# ---------------------------------------------------------------------------

def test_create_single_weekday_block_returns_201(client, provider_id):
    resp = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [2],
              "start_hour": 12, "end_hour": 13, "label": "Lunch"},
        headers=HDR,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["provider_id"] == provider_id
    assert body["weekdays"] == [2]
    assert body["specific_date"] is None
    assert body["recurrence_until"] is None
    assert body["start_hour"] == 12 and body["start_minute"] == 0
    assert body["end_hour"] == 13 and body["end_minute"] == 0
    assert body["label"] == "Lunch"


def test_create_multi_weekday_block(client, provider_id):
    """Owner picks Mon + Wed + Fri in one rule."""
    resp = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [0, 2, 4],
              "start_hour": 12, "end_hour": 13, "label": "Standup"},
        headers=HDR,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["weekdays"] == [0, 2, 4]
    assert body["specific_date"] is None


def test_create_specific_date_block(client, provider_id):
    """One-off block on a particular calendar date."""
    target = _future_date(7)
    resp = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "specific_date": target,
              "start_hour": 14, "end_hour": 16, "label": "Conference"},
        headers=HDR,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["specific_date"] == target
    assert body["weekdays"] is None
    assert body["recurrence_until"] is None


def test_create_with_recurrence_until(client, provider_id):
    until = _future_date(45)
    resp = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [0],
              "recurrence_until": until,
              "start_hour": 9, "end_hour": 10, "label": "Summer"},
        headers=HDR,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["weekdays"] == [0]
    assert body["recurrence_until"] == until


def test_list_returns_blocks_for_clinic(client, provider_id):
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekdays": [0],
                      "start_hour": 9, "end_hour": 10, "label": "AM"}, headers=HDR)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekdays": [4],
                      "start_hour": 17, "end_hour": 18, "label": "PM"}, headers=HDR)
    resp = client.get("/api/v2/scheduling/busy-blocks", headers=HDR)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 2


def test_list_filters_by_provider_id(client, db_session, provider_id):
    other = Provider(name="Jones", title="Dr", clinic_id=DEFAULT_CLINIC_ID, is_active=True)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": provider_id, "weekdays": [1],
                      "start_hour": 12, "end_hour": 13}, headers=HDR)
    client.post("/api/v2/scheduling/busy-blocks",
                json={"provider_id": other.id, "weekdays": [1],
                      "start_hour": 14, "end_hour": 15}, headers=HDR)
    resp = client.get(f"/api/v2/scheduling/busy-blocks?provider_id={provider_id}", headers=HDR)
    assert resp.status_code == 200
    rows = resp.json()
    assert all(r["provider_id"] == provider_id for r in rows)


def test_update_partial_changes_only_supplied_fields(client, provider_id):
    created = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [2],
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
    assert body["weekdays"] == [2]  # unchanged
    assert body["start_hour"] == 12 and body["end_hour"] == 13


def test_update_can_switch_mode_to_specific_date(client, provider_id):
    """Editing a weekday rule to a specific-date one-off clears the recurrence fields."""
    created = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [0],
              "recurrence_until": _future_date(60),
              "start_hour": 12, "end_hour": 13},
        headers=HDR,
    ).json()
    target = _future_date(3)
    resp = client.put(
        f"/api/v2/scheduling/busy-blocks/{created['id']}",
        json={"specific_date": target},
        headers=HDR,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["specific_date"] == target
    assert body["weekdays"] is None
    assert body["recurrence_until"] is None


def test_delete_then_get_404(client, provider_id):
    created = client.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [0],
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
    created = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [3],
              "start_hour": 12, "end_hour": 13, "label": "default-lunch"},
        headers=HDR,
    )
    assert created.status_code == 201

    mm_resp = client_market_mall.get(
        "/api/v2/scheduling/busy-blocks",
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert mm_resp.status_code == 200
    mm_labels = [r.get("label") for r in mm_resp.json()]
    assert "default-lunch" not in mm_labels
    assert len(mm_resp.json()) >= 22  # seeded count

    default_resp = client_market_mall.get("/api/v2/scheduling/busy-blocks", headers=HDR)
    default_labels = [r.get("label") for r in default_resp.json()]
    assert "default-lunch" in default_labels


def test_create_rejects_provider_in_other_clinic(client_market_mall, db_session):
    """Cannot create a busy block targeting a provider that belongs to another clinic."""
    foreign = Provider(name="Foreign", title="Dr",
                       clinic_id=DEFAULT_CLINIC_ID, is_active=True)
    db_session.add(foreign)
    db_session.commit()
    db_session.refresh(foreign)
    resp = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": foreign.id, "weekdays": [0],
              "start_hour": 9, "end_hour": 10},
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert resp.status_code == 404


def test_update_404_when_block_in_other_clinic(client_market_mall, provider_id):
    created = client_market_mall.post(
        "/api/v2/scheduling/busy-blocks",
        json={"provider_id": provider_id, "weekdays": [0],
              "start_hour": 9, "end_hour": 10},
        headers=HDR,
    ).json()
    resp = client_market_mall.put(
        f"/api/v2/scheduling/busy-blocks/{created['id']}",
        json={"label": "stolen"},
        headers={"X-Clinic-Id": "market-mall-denture"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validation (422)
# ---------------------------------------------------------------------------

def test_422_neither_weekdays_nor_date(client, provider_id):
    """Must supply one of weekdays or specific_date."""
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id,
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_both_weekdays_and_date(client, provider_id):
    """Exactly one — can't have both."""
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id,
                             "weekdays": [0],
                             "specific_date": _future_date(7),
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_weekday_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [7],
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_hour_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [2],
                             "start_hour": 24, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_minute_out_of_range(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [2],
                             "start_hour": 12, "start_minute": 60,
                             "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_missing_provider_id(client):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"weekdays": [2], "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_after_end(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [2],
                             "start_hour": 15, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_start_equals_end(client, provider_id):
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [2],
                             "start_hour": 12, "start_minute": 30,
                             "end_hour": 12, "end_minute": 30},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_recurrence_until_with_specific_date(client, provider_id):
    """recurrence_until is meaningless for one-off blocks."""
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id,
                             "specific_date": _future_date(7),
                             "recurrence_until": _future_date(14),
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_recurrence_until_in_past(client, provider_id):
    """recurrence_until must be today or later."""
    past = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [0],
                             "recurrence_until": past,
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422


def test_422_duplicate_weekdays(client, provider_id):
    """Same weekday listed twice is rejected."""
    resp = client.post("/api/v2/scheduling/busy-blocks",
                       json={"provider_id": provider_id, "weekdays": [0, 0],
                             "start_hour": 12, "end_hour": 13},
                       headers=HDR)
    assert resp.status_code == 422
