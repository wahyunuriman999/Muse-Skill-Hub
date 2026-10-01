"""Provider contract tests — mock → sandbox → live matrix, step 1: mock.

These tests prove the *contract-test pattern*: the real driver code runs
unmodified against a canned provider responder (SKILLHUB_MOCK), asserting
request shapes (URL, method, auth header, payload) and response parsing.
No network, no credentials. The same driver code later runs against
sandbox/live providers without changes.
"""
import os

import pytest

from skillhub import mock as mock_harness
from skillhub.registry import dispatch, load_registry

REG = load_registry()


@pytest.fixture(autouse=True)
def _mock_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    mock_harness.reset()
    mock_harness.enable()
    # drivers resolve credentials via the manager: env is the first source
    os.environ["GITHUB_TOKEN"] = "mock-github-token"
    os.environ["STRIPE_SECRET_KEY"] = "mock-stripe-key"
    yield
    mock_harness.reset()
    os.environ.pop("GITHUB_TOKEN", None)
    os.environ.pop("STRIPE_SECRET_KEY", None)


@pytest.mark.asyncio
async def test_github_search_contract():
    """Mock GitHub: assert request shape + response parsing."""
    seen = {}

    async def responder(method, url, **kw):
        seen["method"] = method
        seen["url"] = url
        seen["params"] = kw.get("params")
        seen["auth"] = (kw.get("headers") or {}).get("Authorization")
        return {"items": [
            {"full_name": "octo/hello", "stargazers_count": 42,
             "description": "hi", "html_url": "https://github.com/octo/hello"},
        ]}

    mock_harness.register("github", responder)
    result = await dispatch(REG["github"], "search_repositories",
                            {"query": "mcp server", "per_page": 5})

    assert seen["method"] == "GET"
    assert seen["url"].endswith("/search/repositories")
    assert seen["params"]["q"] == "mcp server"
    assert seen["auth"] == "Bearer mock-github-token"  # credential flowed, never logged
    assert result["repositories"][0]["full_name"] == "octo/hello"
    assert result["repositories"][0]["stars"] == 42


@pytest.mark.asyncio
async def test_stripe_payment_link_contract():
    """Mock Stripe: assert form-encoded mutation payload + parsing."""
    seen = {}

    async def responder(method, url, **kw):
        seen["method"] = method
        seen["url"] = url
        seen["data"] = kw.get("data")
        seen["auth"] = (kw.get("headers") or {}).get("Authorization", "")
        return {"id": "plink_mock123", "url": "https://buy.stripe.com/mock123"}

    mock_harness.register("stripe", responder)
    # financial risk → real approval flow (request → approve → consume)
    from skillhub import approval as approval_mod
    pending = approval_mod.request_approval(
        "stripe", "create_payment_link",
        {"product_name": "Test", "amount_cents": 5000}, risk="financial")
    approval_mod.approve(pending["approval_id"])
    result = await dispatch(
        REG["stripe"], "create_payment_link",
        {"product_name": "Test", "amount_cents": 5000},
        approval_id=pending["approval_id"],
        idempotency_key="contract-test-key-1")

    assert seen["method"] == "POST"
    assert seen["url"].endswith("/payment_links")
    assert seen["data"]["line_items[0][price_data][unit_amount]"] == "5000"
    # Stripe uses Basic auth with the secret key (base64 "key:") — the
    # credential flowed from the manager into the header, never into logs
    import base64
    assert seen["auth"] == "Basic " + base64.b64encode(b"mock-stripe-key:").decode()
    assert result["url"] == "https://buy.stripe.com/mock123"
    assert result["id"] == "plink_mock123"


@pytest.mark.asyncio
async def test_mock_can_simulate_provider_failure():
    """Responders can raise structured errors — drivers must surface them cleanly."""
    from skillhub.errors import UpstreamError

    async def responder(method, url, **kw):
        from skillhub.errors import RateLimited
        raise RateLimited("github", "rate limited in mock")

    mock_harness.register("github", responder)
    with pytest.raises(UpstreamError):
        await dispatch(REG["github"], "search_repositories", {"query": "x"})


def test_mock_disabled_without_registration():
    assert mock_harness.responder_for("unregistered-skill") is None
