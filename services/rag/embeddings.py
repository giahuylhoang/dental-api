"""Async wrapper around Google's text-embedding-005 model.

One function: `embed(text) -> list[float]`. Reads GEMINI_API_KEY from env.
Raises MissingGeminiKey if absent, EmbeddingError on non-200 from upstream.
"""
import os
import httpx


_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/text-embedding-005:embedContent"
)
_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


class MissingGeminiKey(RuntimeError):
    pass


class EmbeddingError(RuntimeError):
    pass


async def embed(text: str) -> list[float]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise MissingGeminiKey("GEMINI_API_KEY is not set")

    payload = {
        "content": {"parts": [{"text": text}]},
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.request(
            "POST",
            f"{_GEMINI_ENDPOINT}?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
    if resp.status_code != 200:
        raise EmbeddingError(f"Gemini embed failed: HTTP {resp.status_code} — {resp.text[:200]}")
    data = resp.json()
    values = data.get("embedding", {}).get("values")
    if not isinstance(values, list) or len(values) != 768:
        raise EmbeddingError(f"Gemini embed returned unexpected shape: {data!r}")
    return values
