"""Philips Hue driver — real Hue Bridge local API implementation.

Setup: press the link button on your Hue Bridge, then create a username:
  curl -X POST http://<bridge-ip>/api -d '{"devicetype":"skillhub"}'
Copy the returned username. Set HUE_BRIDGE_IP and HUE_USERNAME.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "philips-hue"
REQUIRED_ENV = ["HUE_BRIDGE_IP", "HUE_USERNAME"]
SETUP_HELP = (
    "Find your bridge IP (https://discovery.meethue.com), press its link button, "
    "then POST {\"devicetype\":\"skillhub\"} to http://<ip>/api to get a username. "
    "Set HUE_BRIDGE_IP and HUE_USERNAME."
)


def _base() -> str:
    ip = os.environ.get("HUE_BRIDGE_IP")
    user = os.environ.get("HUE_USERNAME")
    if not ip or not user:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return f"http://{ip}/api/{user}"


async def list_lights(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_base()}/lights")
    return {"status": "ok", "lights": [
        {"id": lid, "name": l.get("name"),
         "on": (l.get("state") or {}).get("on"),
         "bri": (l.get("state") or {}).get("bri")}
        for lid, l in (r or {}).items()]}


async def set_light(params: dict) -> dict:
    body = {}
    if "on" in params:
        body["on"] = bool(params["on"])
    if params.get("brightness") is not None:
        body["bri"] = max(1, min(254, int(params["brightness"])))
    r = await api_request(SKILL, "PUT",
                          f"{_base()}/lights/{params['light_id']}/state",
                          json=body)
    return {"status": "ok", "result": r}


ACTIONS = {
    "list_lights": ActionDef("List Hue lights and their state.",
        {}, [], list_lights),
    "set_light": ActionDef("Turn a light on/off or set brightness 1-254 (needs confirm=true).",
        {"light_id": {"type": "string"}, "on": {"type": "boolean"},
         "brightness": {"type": "integer", "minimum": 1, "maximum": 254}},
        ["light_id"], set_light, write=True),
}
