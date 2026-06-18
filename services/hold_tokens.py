import os, hmac, hashlib, base64


def _key() -> bytes:
    return (os.getenv("DENTAL_API_INTERNAL_SECRET") or "").encode()


def _sign(appointment_id: str) -> str:
    mac = hmac.new(_key(), appointment_id.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")


def make_confirm_token(appointment_id: str) -> str:
    return f"{appointment_id}.{_sign(appointment_id)}"


def verify_confirm_token(token: str) -> str | None:
    try:
        appointment_id, sig = token.rsplit(".", 1)
    except (ValueError, AttributeError):
        return None
    if hmac.compare_digest(sig, _sign(appointment_id)):
        return appointment_id
    return None
