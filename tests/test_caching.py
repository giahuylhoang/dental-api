"""Tests for read-side caching with ETag and Cache-Control."""
import pytest


def test_clinic_config_has_cache_headers(client):
    """GET /api/v2/settings/clinic returns ETag and Cache-Control headers."""
    resp = client.get("/api/v2/settings/clinic", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    assert "ETag" in resp.headers
    assert "Cache-Control" in resp.headers
    assert "private" in resp.headers["Cache-Control"]


def test_clinic_config_304_on_matching_etag(client):
    """GET /api/v2/settings/clinic returns 304 when If-None-Match matches."""
    # First request to get ETag
    resp1 = client.get("/api/v2/settings/clinic", headers={"X-Clinic-Id": "default"})
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    
    # Second request with If-None-Match
    resp2 = client.get(
        "/api/v2/settings/clinic",
        headers={"X-Clinic-Id": "default", "If-None-Match": etag},
    )
    assert resp2.status_code == 304


def test_voice_config_has_cache_headers(client):
    """GET /api/v2/settings/ai/voice returns ETag and Cache-Control headers."""
    resp = client.get("/api/v2/settings/ai/voice", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    assert "ETag" in resp.headers
    assert "Cache-Control" in resp.headers


def test_voice_config_304_on_matching_etag(client):
    """GET /api/v2/settings/ai/voice returns 304 when If-None-Match matches."""
    # First request to get ETag
    resp1 = client.get("/api/v2/settings/ai/voice", headers={"X-Clinic-Id": "default"})
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    
    # Second request with If-None-Match
    resp2 = client.get(
        "/api/v2/settings/ai/voice",
        headers={"X-Clinic-Id": "default", "If-None-Match": etag},
    )
    assert resp2.status_code == 304


def test_integrations_has_cache_headers(client):
    """GET /api/v2/settings/integrations returns ETag and Cache-Control headers."""
    resp = client.get("/api/v2/settings/integrations", headers={"X-Clinic-Id": "default"})
    assert resp.status_code == 200
    assert "ETag" in resp.headers
    assert "Cache-Control" in resp.headers
