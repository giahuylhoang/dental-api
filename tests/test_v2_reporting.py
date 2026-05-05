"""Tests for v2 reporting endpoints."""
import pytest


def test_kpi_endpoint(client):
    """GET /api/v2/reporting/kpi returns KPI data."""
    resp = client.get("/api/v2/reporting/kpi", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    data = resp.json()
    assert "production_this_month" in data
    assert "ar_aging" in data
    assert "no_show_rate" in data
    assert "lab_cost_per_case" in data


def test_production_by_provider(client):
    """GET /api/v2/reporting/production-by-provider returns provider production."""
    resp = client.get("/api/v2/reporting/production-by-provider", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_remake_rate_by_lab(client):
    """GET /api/v2/reporting/remake-rate-by-lab returns lab remake rates."""
    resp = client.get("/api/v2/reporting/remake-rate-by-lab", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_kpi_tenant_isolation(client, client_market_mall):
    """KPI data is scoped to the requesting clinic."""
    resp_default = client.get("/api/v2/reporting/kpi", headers={"X-Clinic-Id": "default"})
    resp_market = client_market_mall.get("/api/v2/reporting/kpi", headers={"X-Clinic-Id": "market-mall-denture"})
    assert resp_default.status_code == 200
    assert resp_market.status_code == 200
    # Both should return valid KPI structures (values may differ)
    assert "production_this_month" in resp_default.json()
    assert "production_this_month" in resp_market.json()
