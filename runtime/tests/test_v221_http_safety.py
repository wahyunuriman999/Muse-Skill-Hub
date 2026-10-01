"""GATE 14 — HTTP safety.

The shared HTTP layer's retry/error policy, proven against a
``httpx.MockTransport`` (no real network):
  1. 429 is retried for ANY method and honors Retry-After;
  2. 5xx is retried ONLY for GET/HEAD/OPTIONS — never for mutations;
  3. a mutation 5xx (incl. 502/503/504) raises UpstreamUnavailable
     after exactly one attempt (regression: the old code retried
     502/503/504 for every method, risking duplicate side effects);
  4. retries are bounded (initial + 3) and then surface UpstreamUnavailable;
  5. timeouts raise Timeout; request IDs + User-Agent are sent;
     malformed bodies return {"raw": ...}; 4xx maps to structured errors.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest

from skillhub import http as http_mod
from skillhub.errors import (AuthExpired, Timeout, UpstreamError,
                             UpstreamUnavailable)
from skillhub.http import api_request


class Harness:
    """Swap the HTTP layer's client for a MockTransport + record sleeps."""

    def __init__(self, monkeypatch, handler):
        self.calls: list[httpx.Request] = []
        self.sleeps: list[float] = []

        def _handler(request: httpx.Request) -> httpx.Response:
            self.calls.append(request)
            return handler(request)

        async def _fake_client(timeout: float):
            return httpx.AsyncClient(
                transport=httpx.MockTransport(_handler), timeout=timeout)

        async def _fake_sleep(delay: float):
            self.sleeps.append(delay)

        monkeypatch.setattr(http_mod, "_get_client", _fake_client)
        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)

    @property
    def n_calls(self) -> int:
        return len(self.calls)


def _resp(status: int, body=None, headers=None) -> httpx.Response:
    import json as _json
    content = _json.dumps(body).encode() if body is not None else b""
    return httpx.Response(status, content=content, headers=headers or {})


@pytest.mark.asyncio
async def test_429_retried_for_post_and_honors_retry_after(monkeypatch):
    states = iter([
        _resp(429, headers={"Retry-After": "2"}),
        _resp(429, headers={"Retry-After": "2"}),
        _resp(200, {"ok": True}),
    ])
    h = Harness(monkeypatch, lambda req: next(states))
    out = await api_request("s", "POST", "https://x.test/", json={"a": 1})
    assert out == {"ok": True}
    assert h.n_calls == 3
    assert h.sleeps == [2.0, 2.0]  # Retry-After honored, not the backoff


@pytest.mark.asyncio
async def test_5xx_retried_for_get(monkeypatch):
    states = iter([_resp(500), _resp(200, {"ok": True})])
    h = Harness(monkeypatch, lambda req: next(states))
    out = await api_request("s", "GET", "https://x.test/")
    assert out == {"ok": True}
    assert h.n_calls == 2


@pytest.mark.asyncio
async def test_5xx_never_retried_for_mutations(monkeypatch):
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        h = Harness(monkeypatch, lambda req: _resp(500))
        with pytest.raises(UpstreamUnavailable):
            await api_request("s", method, "https://x.test/", json={"a": 1})
        assert h.n_calls == 1, f"{method} 500 was retried"


@pytest.mark.asyncio
async def test_gateway_5xx_not_retried_for_mutation(monkeypatch):
    # regression: 502/503/504 were retried for every method
    for status in (502, 503, 504):
        h = Harness(monkeypatch, lambda req: _resp(status))
        with pytest.raises(UpstreamUnavailable):
            await api_request("s", "POST", "https://x.test/")
        assert h.n_calls == 1, f"POST {status} was retried"


@pytest.mark.asyncio
async def test_get_retries_bounded(monkeypatch):
    h = Harness(monkeypatch, lambda req: _resp(500))
    with pytest.raises(UpstreamUnavailable):
        await api_request("s", "GET", "https://x.test/")
    assert h.n_calls == 4  # initial + 3 retries
    assert len(h.sleeps) == 3
    assert h.sleeps == sorted(h.sleeps)  # exponential backoff grows


@pytest.mark.asyncio
async def test_timeout_raises_timeout(monkeypatch):
    def _handler(req: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow", request=req)

    h = Harness(monkeypatch, _handler)
    with pytest.raises(Timeout):
        await api_request("s", "GET", "https://x.test/")
    assert h.n_calls == 1  # transport errors are not retried here


@pytest.mark.asyncio
async def test_request_id_and_user_agent_sent(monkeypatch):
    seen = {}

    def _handler(req: httpx.Request) -> httpx.Response:
        seen["rid"] = req.headers.get("X-Request-ID")
        seen["ua"] = req.headers.get("User-Agent")
        return _resp(200, {"ok": True})

    Harness(monkeypatch, _handler)
    await api_request("s", "GET", "https://x.test/", request_id="req-123")
    assert seen["rid"] == "req-123"
    assert seen["ua"].startswith("muse-skill-hub-runtime/")


@pytest.mark.asyncio
async def test_malformed_body_returns_raw(monkeypatch):
    h = Harness(monkeypatch,
                lambda req: httpx.Response(200, content=b"not json{{{"))
    out = await api_request("s", "GET", "https://x.test/")
    assert out == {"raw": "not json{{{"}
    assert h.n_calls == 1


@pytest.mark.asyncio
async def test_4xx_maps_to_structured_errors(monkeypatch):
    h = Harness(monkeypatch, lambda req: _resp(401))
    with pytest.raises(AuthExpired) as ei:
        await api_request("s", "GET", "https://x.test/")
    assert ei.value.code == "auth_expired"
    assert ei.value.retryable is False

    h = Harness(monkeypatch,
                lambda req: _resp(422, {"message": "bad field"}))
    with pytest.raises(UpstreamError) as ei:
        await api_request("s", "POST", "https://x.test/")
    # provider detail stays out of the LLM-visible message (leak safety);
    # it is kept in `internal` for SKILLHUB_DEBUG=1
    assert "bad field" not in str(ei.value)
    assert "bad field" in ei.value.internal
    assert h.n_calls == 1  # 4xx is never retried


@pytest.mark.asyncio
async def test_empty_body_returns_empty_dict(monkeypatch):
    h = Harness(monkeypatch, lambda req: httpx.Response(204))
    assert await api_request("s", "DELETE", "https://x.test/") == {}
    assert h.n_calls == 1
