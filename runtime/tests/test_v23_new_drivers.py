"""Tests for the v2.3.0 upgraded drivers: lovable, replit.

Both were honest stubs (catalog-only) until research on 2026-10-02 verified
real public APIs — the same pattern as the Granola discovery in v1.5.0.

Drivers are verified by (1) honest credential errors when env vars are missing,
(2) mocked api_request proving each driver builds the correct real API request
and parses the response, and (3) plan/Enterprise-gate error translation.
No real credentials or network needed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub import registry
from skillhub.errors import AuthExpired, CredentialsMissing, PermissionDenied, UpstreamError


def _mock_api(monkeypatch, module_name, fake):
    """Replace skillhub.skills.<module>.api_request with a fake; return captured calls."""
    calls = []

    async def _fake(skill, method, url, **kwargs):
        calls.append({"skill": skill, "method": method, "url": url, **kwargs})
        return fake(url, method, kwargs)

    monkeypatch.setattr(f"skillhub.skills.{module_name}.api_request", _fake)
    return calls


def _no_env(monkeypatch, *names):
    for n in names:
        monkeypatch.delenv(n, raising=False)


async def _approved(skill, action, params):
    """Run a write action through the real approval flow."""
    from skillhub import approval as approval_engine
    from skillhub.policy import risk_for
    entry = registry.load_registry()[skill]
    risk = risk_for(skill, action, entry.actions[action].risk)
    item = approval_engine.request_approval(skill, action, params, risk=risk)
    approval_engine.approve(item["approval_id"])
    return await registry.dispatch(entry, action, params,
                                   approval_id=item["approval_id"])


def test_upgraded_drivers_are_implemented():
    reg = registry.load_registry()
    for name in ("lovable", "replit"):
        assert reg[name].implemented, f"{name} has no executable driver"
        assert len(reg[name].actions) >= 1, f"{name} has no actions"
    assert len(reg["lovable"].actions) == 6
    assert len(reg["replit"].actions) == 6


def test_upgraded_drivers_require_env(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "LOVABLE_API_KEY", "REPLIT_API_KEY")
    import asyncio
    with pytest.raises(CredentialsMissing):
        asyncio.run(registry.dispatch(reg["lovable"], "list_workspaces", {}, confirm=False))
    with pytest.raises(CredentialsMissing):
        asyncio.run(registry.dispatch(reg["replit"], "list_workspaces", {}, confirm=False))


def test_lovable_headers_and_version(monkeypatch):
    import asyncio
    monkeypatch.setenv("LOVABLE_API_KEY", "lov_test123")
    calls = _mock_api(monkeypatch, "lovable",
                       lambda url, method, kw: {"workspaces": []})
    reg = registry.load_registry()
    out = asyncio.run(registry.dispatch(reg["lovable"], "list_workspaces", {}, confirm=False))
    assert out["status"] == "ok"
    assert len(calls) == 1
    c = calls[0]
    assert c["method"] == "GET"
    assert c["url"] == "https://api.lovable.dev/v1/workspaces"
    assert c["headers"]["Lovable-API-Key"] == "lov_test123"
    assert c["headers"]["Lovable-Version"] == "2026-09-11"


def test_lovable_publish_project(monkeypatch):
    import asyncio
    monkeypatch.setenv("LOVABLE_API_KEY", "lov_test123")

    def fake(url, method, kw):
        assert method == "POST"
        assert url.endswith("/v1/projects/p1/deployments")
        return {"deployment": {"deployment_id": "d9", "status": "pending",
                               "url": "https://p1.lovable.app"}}

    _mock_api(monkeypatch, "lovable", fake)
    out = asyncio.run(_approved("lovable", "publish_project", {"project_id": "p1"}))
    assert out["status"] == "ok"
    assert out["deployment"]["deployment_id"] == "d9"
    assert out["deployment"]["status"] == "pending"


def test_lovable_plan_gate_translated(monkeypatch):
    """402 payment_required becomes a clear plan message, not a raw HTTP error."""
    import asyncio
    monkeypatch.setenv("LOVABLE_API_KEY", "lov_test123")

    async def _raise402(skill, method, url, **kwargs):
        raise UpstreamError(skill, "HTTP 402: payment_required")

    monkeypatch.setattr("skillhub.skills.lovable.api_request", _raise402)
    with pytest.raises(PermissionDenied, match="Business or Enterprise"):
        asyncio.run(_approved("lovable", "publish_project", {"project_id": "p1"}))


def test_replit_bearer_auth_and_paths(monkeypatch):
    import asyncio
    monkeypatch.setenv("REPLIT_API_KEY", "rpl_test123")

    def fake(url, method, kw):
        assert kw["headers"]["Authorization"] == "Bearer rpl_test123"
        if url.endswith("/workspaces"):
            return {"workspaces": [{"id": "w1", "name": "Acme"}]}
        if url.endswith("/projects"):
            assert kw["params"]["workspaceId"] == "w1"
            return {"projects": []}
        raise AssertionError(f"unexpected {url}")

    calls = _mock_api(monkeypatch, "replit", fake)
    reg = registry.load_registry()
    out = asyncio.run(registry.dispatch(reg["replit"], "list_workspaces", {}, confirm=False))
    assert out["workspaces"] == [{"id": "w1", "name": "Acme", "slug": None}]
    out2 = asyncio.run(registry.dispatch(
        reg["replit"], "list_projects", {"workspace_id": "w1"}, confirm=False))
    assert out2["status"] == "ok"
    assert any(c["url"] == "https://api.replit.com/workspaces" for c in calls)


def test_replit_set_budget_write_action(monkeypatch):
    import asyncio
    monkeypatch.setenv("REPLIT_API_KEY", "rpl_test123")

    def fake(url, method, kw):
        assert method == "POST"
        assert url.endswith("/budgets")
        assert kw["json"]["amount"] == 500
        return {"budget": {"name": "q4", "amount": 500}}

    _mock_api(monkeypatch, "replit", fake)
    assert registry.load_registry()["replit"].actions["set_budget"].write is True
    out = asyncio.run(_approved(
        "replit", "set_budget",
        {"name": "q4", "amount": 500, "period": "quarterly"}))
    assert out["budget"]["amount"] == 500


def test_replit_enterprise_gate_translated(monkeypatch):
    """Auth failure becomes a clear Enterprise-gate message."""
    import asyncio
    monkeypatch.setenv("REPLIT_API_KEY", "rpl_bad")

    async def _raise_auth(skill, method, url, **kwargs):
        raise AuthExpired(skill, "HTTP 401")

    monkeypatch.setattr("skillhub.skills.replit.api_request", _raise_auth)
    with pytest.raises(PermissionDenied, match="Enterprise"):
        asyncio.run(_approved("replit", "set_budget", {"name": "q4"}))
