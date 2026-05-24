"""Tests for services.rag.embeddings — Gemini gemini-embedding-001 wrapper."""
import asyncio
import httpx
import pytest


def test_embed_calls_gemini_with_correct_payload(monkeypatch):
    captured = {}

    async def fake_request(self, method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        captured["headers"] = dict(kwargs.get("headers") or {})
        req = httpx.Request(method, url)
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.1] * 768}},
            request=req,
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-xyz")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    from services.rag.embeddings import embed
    vec = asyncio.run(embed("What's involved in a reline?"))

    assert len(vec) == 768
    assert vec[0] == pytest.approx(0.1)
    assert captured["method"] == "POST"
    assert "gemini-embedding-001" in captured["url"]
    assert "embedContent" in captured["url"]
    body = captured["json"]
    assert body["content"]["parts"][0]["text"] == "What's involved in a reline?"
    assert body["output_dimensionality"] == 768


def test_embed_raises_runtime_error_when_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from services.rag.embeddings import embed, MissingGeminiKey
    with pytest.raises(MissingGeminiKey):
        asyncio.run(embed("anything"))


def test_embed_raises_on_non_200(monkeypatch):
    async def fake_request(self, method, url, **kwargs):
        req = httpx.Request(method, url)
        return httpx.Response(500, json={"error": "boom"}, request=req)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-xyz")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    from services.rag.embeddings import embed, EmbeddingError
    with pytest.raises(EmbeddingError):
        asyncio.run(embed("anything"))
