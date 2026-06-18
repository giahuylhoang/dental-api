"""Internal holds router — POST /api/internal/holds.

Internal-secret gated; hard-codes source='voice-hold'.
Not proxied by the BFF, so it is never exposed to the public internet.
"""
