"""Shared async HTTP layer for skill drivers (v2).

- One persistent ``httpx.AsyncClient`` (connection pooling, fewer TLS
  handshakes) instead of a new client per request.
- Retry with exponential backoff + ``Retry-After`` on 429/5xx.
- ``X-Request-ID`` correlation header on every request.
- Provider error mapping: 401/403 → AuthExpired, 404 → NotFound,
  429 → RateLimited (retryable, with retry_after), 5xx → UpstreamUnavailable.
- Per-call timeout, still configurable per driver.

``api_request`` keeps its signature so existing drivers work unchanged.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import httpx

from . import __version__
from .errors import (AuthExpired, NotFound, RateLimited, Timeout,
                     UpstreamError, UpstreamUnavailable)

_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_BASE_BACKOFF = 0.5

_client: httpx.AsyncClient | None = None
_client_loop: asyncio.AbstractEventLoop | None = None


def _proxy() -> str | None:
    return (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )


async def _get_client(timeout: float) -> httpx.AsyncClient:
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client_loop is not loop or _client.is_closed:
        if _client is not None and not _client.is_closed:
            try:
                await _client.aclose()
            except Exception:
                pass
        _client = httpx.AsyncClient(timeout=timeout, proxy=_proxy())
        _client_loop = loop
    return _client


async def aclose_client() -> None:
    global _client, _client_loop
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
        _client = None
        _client_loop = None


def _retryable(method: str, status: int, attempt: int) -> bool:
    if attempt >= _MAX_RETRIES:
        return False
    if status == 429:
        return True
    if status >= 500 and method.upper() in ("GET", "HEAD", "OPTIONS"):
        return True
    if status in (502, 503, 504):  # gateway-ish: safe to retry once
        return True
    return False


def _backoff(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(float(retry_after), 60.0)
        except ValueError:
            pass
    return min(_BASE_BACKOFF * (2 ** attempt), 8.0)


def _raise_for_status(skill: str, resp: httpx.Response, url: str,
                      action: str = "") -> None:
    code = resp.status_code
    if code in (401, 403):
        raise AuthExpired(
            f"Authentication failed for '{skill}' (HTTP {code}). "
            "Check that your API token is valid and has the required scopes.",
            skill=skill, action=action,
            internal=f"HTTP {code} {url} :: {resp.text[:300]}")
    if code == 404:
        raise NotFound(f"Resource not found in '{skill}' (HTTP 404).",
                       skill=skill, action=action, internal=f"404 {url}")
    if code == 429:
        retry_after = resp.headers.get("retry-after")
        try:
            ra = int(float(retry_after)) if retry_after else None
        except ValueError:
            ra = None
        raise RateLimited(skill, retry_after=ra, action=action)
    if code >= 500:
        raise UpstreamUnavailable(
            f"Upstream for '{skill}' is unavailable (HTTP {code}).",
            skill=skill, action=action, internal=resp.text[:300])
    if code >= 400:
        detail = resp.text[:500]
        try:
            body = resp.json()
            if isinstance(body, dict):
                detail = body.get("message") or body.get("error") or detail
        except Exception:
            pass
        raise UpstreamError(skill, f"HTTP {code}: {detail}", action=action)


async def api_request(
    skill: str,
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    action: str = "",
    request_id: str | None = None,
) -> dict | list:
    """Perform an HTTP request and return decoded JSON.

    Retries 429/5xx with backoff. Raises structured errors (never raw
    tracebacks) so LLMs get actionable feedback.

    When the mock harness is enabled (``SKILLHUB_MOCK=1`` or
    ``skillhub.mock.enable()``), a registered responder serves the call
    instead of the network — the basis for provider contract tests.
    """
    from . import mock as mock_harness
    rid = request_id or uuid.uuid4().hex[:12]
    responder = mock_harness.responder_for(skill)
    if responder is not None:
        return await responder(method, url, headers=headers, params=params,
                               json=json, data=data, timeout=timeout,
                               action=action, request_id=rid)
    headers = dict(headers or {})
    headers.setdefault("X-Request-ID", rid)
    headers["User-Agent"] = f"muse-skill-hub-runtime/{__version__}"  # centralized version (overrides stale driver values)

    attempt = 0
    while True:
        client = await _get_client(timeout)
        try:
            resp = await client.request(
                method, url, headers=headers, params=params, json=json, data=data)
        except httpx.TimeoutException as exc:
            raise Timeout(skill, action=action) from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(skill, "network failure", action=action,
                                internal=f"{type(exc).__name__}: {exc}") from exc

        if _retryable(method, resp.status_code, attempt):
            await asyncio.sleep(_backoff(attempt, resp.headers.get("retry-after")))
            attempt += 1
            continue
        _raise_for_status(skill, resp, url, action=action)
        break

    if resp.status_code == 204 or not resp.content:
        return {}
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text[:2000]}


async def raw_request(
    skill: str,
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    action: str = "",
) -> bytes:
    """Same as api_request but returns raw bytes (audio/image payloads)."""
    rid = uuid.uuid4().hex[:12]
    headers = dict(headers or {})
    headers.setdefault("X-Request-ID", rid)
    headers["User-Agent"] = f"muse-skill-hub-runtime/{__version__}"  # centralized version (overrides stale driver values)

    attempt = 0
    while True:
        client = await _get_client(timeout)
        try:
            resp = await client.request(
                method, url, headers=headers, params=params, json=json, data=data)
        except httpx.TimeoutException as exc:
            raise Timeout(skill, action=action) from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(skill, "network failure", action=action,
                                internal=f"{type(exc).__name__}: {exc}") from exc
        if _retryable(method, resp.status_code, attempt):
            await asyncio.sleep(_backoff(attempt, resp.headers.get("retry-after")))
            attempt += 1
            continue
        _raise_for_status(skill, resp, url, action=action)
        break
    return resp.content
