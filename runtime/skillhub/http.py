"""Shared async HTTP helpers for skill drivers."""
from __future__ import annotations

import os

import httpx

from .errors import UpstreamError

_DEFAULT_TIMEOUT = 30.0


def _proxy() -> str | None:
    # Passed explicitly: works around an httpx bug parsing IPv6 no_proxy
    # entries, and keeps behavior identical across environments.
    return (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )


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
) -> dict | list:
    """Perform an HTTP request and return decoded JSON.

    Raises UpstreamError with the provider's message on non-2xx responses,
    so LLMs get actionable feedback instead of tracebacks.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, proxy=_proxy()) as client:
            resp = await client.request(
                method, url, headers=headers, params=params, json=json, data=data
            )
    except httpx.HTTPError as exc:
        raise UpstreamError(skill, f"network failure: {exc}") from exc

    if resp.status_code in (401, 403):
        raise UpstreamError(
            skill,
            f"authentication failed (HTTP {resp.status_code}). "
            "Check that your API token is valid and has the required scopes.",
        )
    if resp.status_code == 404:
        raise UpstreamError(skill, f"resource not found (HTTP 404): {url}")
    if resp.status_code == 429:
        raise UpstreamError(
            skill, "rate limited (HTTP 429). Wait before retrying."
        )
    if resp.status_code >= 400:
        detail = resp.text[:500]
        try:
            body = resp.json()
            if isinstance(body, dict):
                detail = body.get("message") or body.get("error") or detail
        except Exception:
            pass
        raise UpstreamError(skill, f"HTTP {resp.status_code}: {detail}")

    if resp.status_code == 204 or not resp.content:
        return {}
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text[:2000]}
