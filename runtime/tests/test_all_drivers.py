"""Full-coverage tests: every skill is either executable or a documented exception.

- test_coverage: 97 skills total; all implemented except the 1 documented
  no-public-API exception (muse-early-access is a Meta-internal program).
  lovable/replit were upgraded to real drivers in v2.3.0 after their public
  APIs were verified (same pattern as the Granola discovery in v1.5.0).
- test_driver_structure: every implemented driver has valid action schemas.
- test_credential_errors: every driver with REQUIRED_ENV raises
  CredentialsMissing (never fake success) when env is cleared.
- Live tests for no-key APIs and local reference drivers.
"""
import asyncio
import json
import os

import pytest

from skillhub.errors import CredentialsMissing, SkillError
from skillhub.registry import dispatch, load_registry

# Skills with no public API and no honest executable implementation.
# muse-early-access: Meta-internal program, no outside access exists.
# (lovable/replit were stubs until v2.3.0, when their public APIs were verified.)
DOCUMENTED_STUBS = {"muse-early-access"}


def _approved(reg, skill, action, params):
    """Run a strict-risk write action through the real approval flow."""
    from skillhub import approval as approval_engine
    from skillhub.policy import risk_for
    entry = reg[skill]
    risk = risk_for(skill, action, entry.actions[action].risk)
    item = approval_engine.request_approval(skill, action, params, risk=risk)
    approval_engine.approve(item["approval_id"])
    return asyncio.run(dispatch(entry, action, params,
                                approval_id=item["approval_id"]))


def test_coverage():
    reg = load_registry()
    assert len(reg) == 97
    stubs = {n for n, e in reg.items() if not e.implemented}
    assert stubs == DOCUMENTED_STUBS, f"unexpected stub set: {stubs}"
    assert len(reg) - len(stubs) == 96


def test_threads_alias_executable():
    reg = load_registry()
    assert reg["threads"].implemented
    assert reg["meta-threads"].implemented


def test_driver_structure():
    reg = load_registry()
    for name, entry in reg.items():
        if not entry.implemented:
            continue
        assert entry.actions, f"{name}: no actions"
        for aname, adef in entry.actions.items():
            assert adef.description, f"{name}.{aname}: no description"
            assert isinstance(adef.parameters, dict), f"{name}.{aname}: params not a dict"
            assert set(adef.required) <= set(adef.parameters), \
                f"{name}.{aname}: required not subset of params"
            assert isinstance(adef.write, bool)


def test_credential_errors_all_drivers(monkeypatch):
    """Clearing a driver's REQUIRED_ENV must raise CredentialsMissing."""
    reg = load_registry()
    checked = 0
    for name, entry in reg.items():
        if not entry.implemented or not entry.required_env:
            continue
        for var in entry.required_env:
            monkeypatch.delenv(var, raising=False)
        # prefer a read action so no confirmation gate interferes
        read_actions = [a for a, d in entry.actions.items() if not d.write]
        if read_actions:
            action, confirm = read_actions[0], False
        else:
            action, confirm = next(iter(entry.actions)), True
        params = {r: "x" for r in entry.actions[action].required}
        # fill required params with type-appropriate dummies (validation runs first)
        for r in entry.actions[action].required:
            t = (entry.actions[action].parameters.get(r) or {}).get("type")
            params[r] = {"array": [], "object": {}, "integer": 1,
                         "number": 1, "boolean": True}.get(t, "x")
        # strict-risk actions need a real approval to reach the credentials check
        from skillhub.policy import STRICT_RISKS, risk_for
        risk = risk_for(name, action, entry.actions[action].risk)
        if risk in STRICT_RISKS:
            from skillhub import approval as approval_engine
            item = approval_engine.request_approval(name, action, params, risk=risk)
            approval_engine.approve(item["approval_id"])
            kwargs = {"approval_id": item["approval_id"]}
        else:
            kwargs = {"confirm": confirm}
        with pytest.raises(CredentialsMissing):
            import asyncio
            asyncio.run(dispatch(entry, action, params, **kwargs))
        checked += 1
    assert checked >= 40, f"only checked {checked} drivers"


def test_booking_router_delegates_without_creds(monkeypatch):
    reg = load_registry()
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)
    import asyncio
    with pytest.raises(CredentialsMissing):
        asyncio.run(
            dispatch(reg["booking"], "search_flights",
                     {"origin": "CGK", "destination": "SIN",
                      "departure_date": "2026-12-01"}, confirm=False))


# ---- live tests: no-key public APIs ----

def test_podcast_search_live():
    import asyncio
    reg = load_registry()
    res = asyncio.run(
        dispatch(reg["podcast"], "search_podcasts", {"query": "python", "limit": 3},
                 confirm=False))
    assert res["status"] == "ok" and len(res["podcasts"]) > 0


def test_opentable_links():
    import asyncio
    reg = load_registry()
    res = asyncio.run(
        dispatch(reg["opentable"], "search_restaurants", {"query": "sushi"},
                 confirm=False))
    assert res["url"].startswith("https://www.opentable.com/s?")


def test_booking_hotel_link():
    import asyncio
    reg = load_registry()
    res = asyncio.run(
        dispatch(reg["booking"], "hotel_search_link",
                 {"destination": "Jakarta"}, confirm=False))
    assert "booking.com" in res["url"]


def test_travel_planning_itinerary():
    import asyncio
    reg = load_registry()
    res = asyncio.run(
        dispatch(reg["travel-planning"], "build_itinerary",
                 {"destination": "Bandung", "days": 2,
                  "interests": ["food", "nature"]}, confirm=False))
    assert len(res["itinerary"]) == 2
    assert all(len(d["slots"]) == 3 for d in res["itinerary"])


# ---- live tests: local reference drivers ----

@pytest.fixture()
def local_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    import asyncio
    return asyncio.run(coro)


def test_secure_vault_roundtrip(local_dir):
    reg = load_registry()
    _run(dispatch(reg["secure-vault"], "store_secret",
                  {"name": "k", "value": "v"}, confirm=True))
    res = _run(dispatch(reg["secure-vault"], "get_secret", {"name": "k"},
                        confirm=False))
    # the VALUE must never come back to the LLM — only a credential_ref
    assert "value" not in res
    assert res["credential_ref"] == "ref:vault:k"
    # explicit reveal needs a real approval (sensitive risk) and is audit-logged
    rev = _approved(reg, "secure-vault", "reveal_secret", {"name": "k"})
    assert rev["value"] == "v"
    names = _run(dispatch(reg["secure-vault"], "list_secrets", {}, confirm=False))
    assert names["secrets"] == ["k"]


def test_permission_model_flow(local_dir):
    reg = load_registry()
    r = _run(dispatch(reg["permission-model"], "request_approval",
                      {"skill": "gmail", "action": "send_message",
                       "params": {"to": "a@b.c"}}, confirm=True))
    aid = r["approval"]["approval_id"]
    assert aid.startswith("apr_")
    pending = _run(dispatch(reg["permission-model"], "list_pending", {},
                            confirm=False))
    assert any(p["approval_id"] == aid for p in pending["pending"])
    ok = _run(dispatch(reg["permission-model"], "approve", {"request_id": aid},
                       confirm=True))
    assert ok["approval"]["status"] == "approved"


def test_goals_flow(local_dir):
    reg = load_registry()
    g = _run(dispatch(reg["goals"], "create_goal", {"title": "Ship v1"},
                      confirm=True))["goal"]
    _run(dispatch(reg["goals"], "log_progress",
                  {"goal_id": g["id"], "note": "halfway"}, confirm=True))
    done = _run(dispatch(reg["goals"], "complete_goal", {"goal_id": g["id"]},
                         confirm=True))
    assert done["goal"]["status"] == "completed"
    assert len(done["goal"]["progress"]) == 1


def test_personal_feed_and_ideas(local_dir):
    reg = load_registry()
    _run(dispatch(reg["personal-feed"], "publish_post", {"title": "Hello"},
                  confirm=True))
    posts = _run(dispatch(reg["personal-feed"], "list_posts", {}, confirm=False))
    assert posts["posts"][0]["title"] == "Hello"
    idea = _run(dispatch(reg["idea-management"], "add_idea", {"title": "X"},
                         confirm=True))["idea"]
    _run(dispatch(reg["idea-management"], "dismiss_idea",
                  {"idea_id": idea["id"]}, confirm=True))
    ideas = _run(dispatch(reg["idea-management"], "list_ideas",
                          {"status": "dismissed"}, confirm=False))
    assert len(ideas["ideas"]) == 1


def test_forget_flow(local_dir):
    reg = load_registry()
    _run(dispatch(reg["forget"], "remember_fact",
                  {"fact": "likes nasi goreng"}, confirm=True))
    out = _approved(reg, "forget", "forget_fact", {"query": "nasi goreng"})
    assert out["removed"] == 1
    assert _run(dispatch(reg["forget"], "list_facts", {},
                         confirm=False))["facts"] == []


def test_muse_db_sqlite(local_dir):
    reg = load_registry()
    # execute_write is destructive-risk: goes through the approval engine
    _approved(reg, "muse_db", "execute_write",
              {"sql": "CREATE TABLE t (id INTEGER, name TEXT)"})
    _approved(reg, "muse_db", "execute_write",
              {"sql": "INSERT INTO t VALUES (1, 'a')"})
    rows = _run(dispatch(reg["muse_db"], "query",
                         {"sql": "SELECT * FROM t"}, confirm=False))
    assert rows["rows"] == [{"id": 1, "name": "a"}]
    tables = _run(dispatch(reg["muse_db"], "list_tables", {}, confirm=False))
    assert "t" in tables["tables"]
    with pytest.raises(SkillError):  # read-only guard
        _run(dispatch(reg["muse_db"], "query",
                      {"sql": "DELETE FROM t"}, confirm=False))


def test_self_awareness_reflects_reality():
    reg = load_registry()
    res = _run(dispatch(reg["self-awareness"], "get_runtime_info", {},
                        confirm=False))
    assert res["total_skills"] == 97
    assert res["executable_drivers"] == 96
    assert set(res["catalog_only"]) == DOCUMENTED_STUBS


def test_function_health():
    reg = load_registry()
    res = _run(dispatch(reg["function-health"], "runtime_health", {},
                        confirm=False))
    assert res["healthy"] is True
    assert res["checks"]["registry"]["executable"] == 96


def test_wallet_and_channels(local_dir):
    reg = load_registry()
    _run(dispatch(reg["wallet"], "connect", {"provider": "manual"}, confirm=True))
    # financial risk: needs a real approval, not bare confirm=true
    _approved(reg, "wallet", "add_payment_method",
              {"label": "BCA debit", "last4": "1234"})
    methods = _run(dispatch(reg["wallet"], "list_payment_methods", {},
                             confirm=False))
    assert methods["methods"][0]["label"] == "BCA debit"
    # messaging channel without webhook -> honest error
    _run(dispatch(reg["messaging-channels"], "register_channel",
                  {"name": "wa", "provider": "whatsapp"}, confirm=True))
    with pytest.raises(SkillError):
        _run(dispatch(reg["messaging-channels"], "send_message",
                      {"channel": "wa", "to": "x", "text": "hi"}, confirm=True))


def test_misc_local_drivers(local_dir):
    reg = load_registry()
    _run(dispatch(reg["agent-library"], "register_agent", {"name": "a1"},
                  confirm=True))
    assert _run(dispatch(reg["agent-library"], "list_agents", {},
                         confirm=False))["agents"][0]["name"] == "a1"
    _run(dispatch(reg["connector-management"], "set_connector",
                  {"provider": "gmail"}, confirm=True))
    assert _run(dispatch(reg["connector-management"], "get_connector",
                         {"provider": "gmail"}, confirm=False))["connector"]["provider"] == "gmail"
    _run(dispatch(reg["paired-devices"], "register_device",
                  {"device_id": "d1"}, confirm=True))
    assert len(_run(dispatch(reg["paired-devices"], "list_devices", {},
                             confirm=False))["devices"]) == 1
    _run(dispatch(reg["device-data"], "import_snapshot",
                  {"contacts": [{"name": "A"}]}, confirm=True))
    assert len(_run(dispatch(reg["device-data"], "get_contacts", {},
                             confirm=False))["contacts"]) == 1
    out = _run(dispatch(reg["share-ideas"], "publish_idea", {"title": "T"},
                        confirm=True))
    assert os.path.exists(out["path"])
    sc = _run(dispatch(reg["skill-creator"], "scaffold_skill", {"name": "demo-x"},
                       confirm=True))
    assert os.path.exists(os.path.join(sc["path"], "SKILL.md"))
    disc = _run(dispatch(reg["wearable-device-skills"], "discover", {},
                         confirm=False))
    assert any(s["skill"] == "withings" for s in disc["wearable_skills"])
    q = _run(dispatch(reg["wearables-comms"], "queue_notification",
                      {"text": "hi"}, confirm=True))
    assert q["queued"]["status"] == "queued"
    fb = _run(dispatch(reg["muse-feedback"], "submit_feedback",
                       {"text": "great"}, confirm=True))
    assert fb["queued"]["transmitted"] is False
    st = _run(dispatch(reg["subscription-status"], "get_status", {},
                       confirm=False))
    assert st["source"] == "local runtime config"
    exp = _run(dispatch(reg["data-control"], "explain_collection", {},
                        confirm=False))
    assert "skillhub-local" in exp["data_collection"]
    assert "local reference implementation" in reg["wallet"].setup_help.lower()


def test_healthkit_honest_error(monkeypatch):
    reg = load_registry()
    monkeypatch.delenv("HEALTHKIT_JSON", raising=False)
    with pytest.raises(SkillError):
        _run(dispatch(reg["apple-healthkit"], "get_daily_metrics", {},
                      confirm=False))
