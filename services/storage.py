"""Pluggable object storage for referral (and future) file uploads.

Two backends:

* ``GCSBackend``   — production. Files live in a private Google Cloud Storage
  bucket; the browser uploads directly via v4 signed PUT URLs, and the CRM/email
  later reads via signed GET URLs. Selected when ``GCS_BUCKET`` is set.
* ``LocalBackend`` — dev/tests. Files live under ``var/uploads/``; signed URLs are
  local sentinels and ``put()`` simulates the browser upload. Selected when
  ``GCS_BUCKET`` is unset.

The backend is intentionally small and uniform so callers (services/referrals.py)
never branch on environment. All client-reported sizes are untrusted: callers
re-verify via :meth:`StorageBackend.stat` after upload.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TypedDict


class ObjectStat(TypedDict):
    size: int
    content_type: Optional[str]


# Default signed-URL lifetimes (seconds).
PUT_TTL = int(os.getenv("GCS_PUT_URL_TTL", "900"))        # 15 min to upload
GET_TTL = int(os.getenv("GCS_GET_URL_TTL", "600"))        # 10 min to view
LINK_TTL = int(os.getenv("GCS_LINK_URL_TTL", str(7 * 24 * 3600)))  # 7 days for email links


class StorageBackend(ABC):
    """Uniform object-storage interface. Object keys are POSIX-style paths."""

    @abstractmethod
    def signed_put_url(self, object_key: str, content_type: str, max_bytes: int) -> str:
        """A short-lived URL the browser PUTs a single object to (size-capped)."""

    @abstractmethod
    def signed_get_url(self, object_key: str, ttl_seconds: int = GET_TTL) -> str:
        """A short-lived URL to read the object."""

    @abstractmethod
    def stat(self, object_key: str) -> Optional[ObjectStat]:
        """Return {size, content_type} if the object exists, else None."""

    @abstractmethod
    def read_bytes(self, object_key: str) -> bytes:
        """Read the full object (used to attach files to email)."""

    @abstractmethod
    def delete(self, object_key: str) -> None:
        """Delete the object; no error if missing."""

    # Test/dev helper — production uploads go straight to the signed PUT URL.
    @abstractmethod
    def put(self, object_key: str, data: bytes, content_type: Optional[str] = None) -> None:
        """Write an object directly (simulates the browser upload in dev/tests)."""


class LocalBackend(StorageBackend):
    """Filesystem-backed backend rooted at ``var/uploads`` (dev/tests)."""

    def __init__(self, root: str | os.PathLike = "var/uploads") -> None:
        self.root = Path(root)

    def _path(self, object_key: str) -> Path:
        # Prevent traversal; object keys are server-generated but be defensive:
        # split on "/" and drop empty, ".", and ".." segments so the result can
        # never escape root regardless of input.
        parts = [seg for seg in object_key.split("/") if seg and seg not in (".", "..")]
        return self.root.joinpath(*parts)

    def signed_put_url(self, object_key: str, content_type: str, max_bytes: int) -> str:
        return f"local://{object_key}"

    def signed_get_url(self, object_key: str, ttl_seconds: int = GET_TTL) -> str:
        return f"local://{object_key}"

    def stat(self, object_key: str) -> Optional[ObjectStat]:
        p = self._path(object_key)
        if not p.exists():
            return None
        return ObjectStat(size=p.stat().st_size, content_type=None)

    def read_bytes(self, object_key: str) -> bytes:
        return self._path(object_key).read_bytes()

    def delete(self, object_key: str) -> None:
        p = self._path(object_key)
        if p.exists():
            p.unlink()

    def put(self, object_key: str, data: bytes, content_type: Optional[str] = None) -> None:
        p = self._path(object_key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend (production).

    Uses v4 signed URLs. On Cloud Run, signing works without a key file when the
    service account has ``roles/iam.serviceAccountTokenCreator`` on itself (the
    google-cloud-storage client signs via the IAM SignBlob API automatically when
    no private key is available).
    """

    def __init__(self, bucket: str) -> None:
        self._bucket_name = bucket
        self._client = None  # lazy

    def _bucket(self):
        if self._client is None:
            from google.cloud import storage  # lazy import — keeps tests GCS-free
            self._client = storage.Client()
        return self._client.bucket(self._bucket_name)

    def signed_put_url(self, object_key: str, content_type: str, max_bytes: int) -> str:
        from datetime import timedelta
        blob = self._bucket().blob(object_key)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=PUT_TTL),
            method="PUT",
            content_type=content_type,
            # Cap the upload size at the signing layer (defense-in-depth; the
            # server still re-verifies actual size via stat() on /complete).
            headers={"x-goog-content-length-range": f"0,{max_bytes}"},
        )

    def signed_get_url(self, object_key: str, ttl_seconds: int = GET_TTL) -> str:
        from datetime import timedelta
        blob = self._bucket().blob(object_key)
        return blob.generate_signed_url(
            version="v4", expiration=timedelta(seconds=ttl_seconds), method="GET",
        )

    def stat(self, object_key: str) -> Optional[ObjectStat]:
        blob = self._bucket().get_blob(object_key)  # network HEAD; None if missing
        if blob is None:
            return None
        return ObjectStat(size=blob.size or 0, content_type=blob.content_type)

    def read_bytes(self, object_key: str) -> bytes:
        return self._bucket().blob(object_key).download_as_bytes()

    def delete(self, object_key: str) -> None:
        try:
            self._bucket().blob(object_key).delete()
        except Exception:
            pass  # already gone

    def put(self, object_key: str, data: bytes, content_type: Optional[str] = None) -> None:
        self._bucket().blob(object_key).upload_from_string(data, content_type=content_type)


_BACKEND: Optional[StorageBackend] = None


def get_storage_backend() -> StorageBackend:
    """Return the process-wide backend: GCS when ``GCS_BUCKET`` is set, else local."""
    global _BACKEND
    if _BACKEND is None:
        bucket = os.getenv("GCS_BUCKET", "").strip()
        _BACKEND = GCSBackend(bucket) if bucket else LocalBackend()
    return _BACKEND


def reset_storage_backend_cache() -> None:
    """Test hook to re-evaluate env between cases."""
    global _BACKEND
    _BACKEND = None
