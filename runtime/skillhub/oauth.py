"""OAuth lifecycle manager — automatic access-token refresh.

A credential stored via :mod:`skillhub.credentials` may carry OAuth
metadata::

    credentials.save_oauth(
        "GOOGLE_OAUTH_TOKEN",
        access_token="ya29.…",
        refresh_token="1//…",
        client_id="….apps.googleusercontent.com",
        client_secret="ref:vault:google-client-secret",  # or raw (encrypted at rest)
        token_url="https://oauth2.googleapis.com/token",
        expires_at=<epoch seconds>,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )

``credentials.cred("GOOGLE_OAUTH_TOKEN")`` then transparently refreshes
the token when it is expired or expiring within 60 seconds, persists the
new access token (and rotated refresh token, if any), and returns a valid
token. Providers without stored OAuth metadata keep their existing
behavior (manual tokens) — the manager is opt-in per credential, not a
flag day.

This implements the *manager*; per-provider client registration is
configuration (your own OAuth client), which no library can do for you.
"""
from __future__ import annotations

import time

from .errors import AuthExpired, CredentialsMissing

REFRESH_SKEW_S = 60


def save_oauth(name: str, access_token: str, refresh_token: str,
               client_id: str, client_secret: str, token_url: str,
               expires_at: int | None = None,
               scopes: list[str] | None = None) -> None:
    """Store an OAuth credential with refresh metadata (encrypted at rest)."""
    from . import credentials
    data = credentials._read_store()
    data[name] = {
        "value": access_token,
        "scopes": list(scopes) if scopes else None,
        "oauth": {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "token_url": token_url,
            "expires_at": expires_at,
        },
        "updated_at": int(time.time()),
    }
    credentials._write_store(data)


def _is_expiring(rec: dict) -> bool:
    oauth = rec.get("oauth") or {}
    expires_at = oauth.get("expires_at")
    if not expires_at:
        return False  # unknown expiry → assume valid (can't do better)
    try:
        return int(expires_at) - REFRESH_SKEW_S <= int(time.time())
    except (TypeError, ValueError):
        return False


def get_valid_token(name: str, rec: dict, skill: str = "unknown") -> str:
    """Return a valid access token, refreshing first when needed."""
    if not _is_expiring(rec):
        return rec.get("value")
    oauth = rec.get("oauth") or {}
    refresh_token = oauth.get("refresh_token")
    if not refresh_token:
        raise AuthExpired(skill,
                          f"OAuth token '{name}' expired and no refresh_token "
                          f"is stored.")
    new_token = _refresh(oauth, skill)
    # persist the rotated credentials atomically
    from . import credentials
    with _locked_store() as data:
        cur = data.get(name) or {}
        cur["value"] = new_token["access_token"]
        cur_oauth = cur.get("oauth") or {}
        cur_oauth["expires_at"] = new_token.get("expires_at")
        if new_token.get("refresh_token"):
            cur_oauth["refresh_token"] = new_token["refresh_token"]
        cur["oauth"] = cur_oauth
        cur["updated_at"] = int(time.time())
        data[name] = cur
    return new_token["access_token"]


def _locked_store():
    from . import credentials, localstore
    # read-modify-write under the same lock discipline as the store itself
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        data = credentials._read_store()
        yield data
        credentials._write_store(data)
    return _ctx()


def _refresh(oauth: dict, skill: str) -> dict:
    """Perform the RFC 6749 refresh_token grant. Returns the token response."""
    import httpx

    from . import credentials as creds_mod

    client_secret = oauth.get("client_secret") or ""
    if client_secret.startswith(creds_mod.VAULT_REF_PREFIX):
        client_secret = creds_mod.resolve_vault_ref(
            client_secret[len(creds_mod.VAULT_REF_PREFIX):], skill=skill)
    try:
        r = httpx.post(
            oauth["token_url"],
            data={"grant_type": "refresh_token",
                  "refresh_token": oauth["refresh_token"],
                  "client_id": oauth.get("client_id", ""),
                  "client_secret": client_secret},
            timeout=20,
        )
    except Exception as exc:
        raise AuthExpired(skill, f"OAuth refresh request failed: {exc}") from exc
    if r.status_code != 200:
        raise AuthExpired(
            skill,
            f"OAuth refresh failed with HTTP {r.status_code}. "
            f"Re-authorize the credential.")
    body = r.json()
    if "access_token" not in body:
        raise AuthExpired(skill, "OAuth refresh response had no access_token.")
    out = {"access_token": body["access_token"]}
    if body.get("refresh_token"):
        out["refresh_token"] = body["refresh_token"]
    if body.get("expires_in"):
        try:
            out["expires_at"] = int(time.time()) + int(body["expires_in"])
        except (TypeError, ValueError):
            pass
    return out


def oauth_status(name: str) -> dict | None:
    """Inspect stored OAuth metadata for a credential (no secrets)."""
    from . import credentials
    rec = credentials._read_store().get(name)
    if not isinstance(rec, dict) or "oauth" not in rec:
        return None
    oauth = rec["oauth"]
    return {
        "name": name,
        "token_url": oauth.get("token_url"),
        "expires_at": oauth.get("expires_at"),
        "expiring": _is_expiring(rec),
        "has_refresh_token": bool(oauth.get("refresh_token")),
        "scopes": rec.get("scopes"),
    }
