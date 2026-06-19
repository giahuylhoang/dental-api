"""Email client: multipart message building + multi-recipient delivery."""
import clients.email_client as ec


def test_build_message_with_attachments(monkeypatch):
    monkeypatch.setenv("EMAIL_FROM", "notify@example.com")
    monkeypatch.delenv("EMAIL_FROM_NAME", raising=False)

    msg = ec.build_email_message(
        to_emails=["info@clinic.com", "owner@clinic.com", "  "],
        subject="New referral",
        body="A referral was submitted.",
        attachments=[
            {"filename": "xray.jpg", "content": b"\xff\xd8jpegbytes", "mime": "image/jpeg"},
            {"filename": "plan.pdf", "content": b"%PDF-1.4 bytes", "mime": "application/pdf"},
        ],
    )

    assert msg["To"] == "info@clinic.com, owner@clinic.com"   # blank dropped
    assert msg["From"] == "notify@example.com"
    assert msg.is_multipart()
    filenames = [p.get_filename() for p in msg.iter_attachments()]
    assert filenames == ["xray.jpg", "plan.pdf"]
    # Encoded size exceeds raw bytes (base64 + MIME overhead) — the size guard relies on this.
    assert len(msg.as_bytes()) > len(b"\xff\xd8jpegbytes") + len(b"%PDF-1.4 bytes")


def test_deliver_message_skips_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("EMAIL_FROM", "notify@example.com")
    msg = ec.build_email_message(to_emails=["a@b.com"], subject="s", body="b")
    assert ec._deliver_message(msg) is False  # no SMTP_HOST → graceful skip


def test_send_email_with_attachments_disabled(monkeypatch):
    monkeypatch.setattr(ec, "SEND_CLINIC_BOOKING_EMAIL", False)
    import asyncio
    ok = asyncio.run(ec.send_email_with_attachments(["a@b.com"], "s", "b"))
    assert ok is True  # disabled → treated as success, no send attempt
