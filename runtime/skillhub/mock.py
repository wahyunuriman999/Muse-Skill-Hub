"""Provider mock harness — contract tests without network or credentials.

Set ``SKILLHUB_MOCK=1`` (or call :func:`enable`) and register canned
responders per skill::

    from skillhub import mock
    mock.enable()
    mock.register("github", lambda method, url, **kw: {"items": []})

While enabled, :func:`skillhub.http.api_request` routes through the
registered responders instead of the network. Responders receive
``(method, url, **kwargs)`` and return the decoded JSON body (or raise a
``skillhub.errors`` exception to simulate failures).

This is the foundation of the provider contract-test matrix: the same
driver code runs against mock → sandbox → live, proving request shapes
and response parsing without real credentials. ``tests/test_provider_contracts.py``
shows the pattern for github and stripe.
"""
from __future__ import annotations

import os
from typing import Callable

_responders: dict[str, Callable] = {}
_enabled = False


def enable() -> None:
    global _enabled
    _enabled = True


def disable() -> None:
    global _enabled
    _enabled = False


def reset() -> None:
    _responders.clear()
    disable()


def is_enabled() -> bool:
    return _enabled or os.environ.get("SKILLHUB_MOCK") == "1"


def register(skill: str, responder: Callable) -> None:
    """Register a responder for a skill: ``(method, url, **kwargs) -> dict``."""
    _responders[skill] = responder


def responder_for(skill: str) -> Callable | None:
    if not is_enabled():
        return None
    return _responders.get(skill)
