"""Tests for the pluggable storage backend (LocalBackend path)."""
import os

from services.storage import (
    LocalBackend,
    GCSBackend,
    get_storage_backend,
    reset_storage_backend_cache,
)


def test_local_backend_put_stat_read_delete(tmp_path):
    be = LocalBackend(root=tmp_path)
    key = "market-mall-denture/referrals/r1/abc.jpg"

    assert be.stat(key) is None  # missing

    be.put(key, b"hello-xray", content_type="image/jpeg")
    st = be.stat(key)
    assert st is not None and st["size"] == len(b"hello-xray")
    assert be.read_bytes(key) == b"hello-xray"

    be.delete(key)
    assert be.stat(key) is None  # gone


def test_local_backend_signed_urls_are_sentinels(tmp_path):
    be = LocalBackend(root=tmp_path)
    assert be.signed_put_url("k", "image/jpeg", 1000).startswith("local://")
    assert be.signed_get_url("k").startswith("local://")


def test_local_backend_rejects_path_traversal(tmp_path):
    be = LocalBackend(root=tmp_path)
    be.put("../../etc/evil", b"x")
    # ".." stripped → stays under root, never escapes
    assert (tmp_path).exists()
    assert not (tmp_path.parent / "etc" / "evil").exists()


def test_get_storage_backend_selects_by_env(monkeypatch):
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
    assert isinstance(get_storage_backend(), LocalBackend)

    monkeypatch.setenv("GCS_BUCKET", "some-bucket")
    reset_storage_backend_cache()
    assert isinstance(get_storage_backend(), GCSBackend)

    monkeypatch.delenv("GCS_BUCKET", raising=False)
    reset_storage_backend_cache()
