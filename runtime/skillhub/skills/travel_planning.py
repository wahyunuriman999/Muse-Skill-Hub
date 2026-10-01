"""Travel planning — local itinerary builder.

Builds a structured day-by-day itinerary from a destination, trip length, and
interests. Real local planning logic (no booking — pair with the booking/duffel
drivers for actual reservations).
"""
from __future__ import annotations

from ..driver import ActionDef

SKILL = "travel-planning"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — builds itineraries locally."

_SLOTS = [("09:00", "Morning"), ("13:00", "Afternoon"), ("19:00", "Evening")]


async def build_itinerary(params: dict) -> dict:
    days = max(1, min(int(params.get("days", 3)), 30))
    interests = params.get("interests", []) or ["sightseeing"]
    destination = params["destination"]
    plan = []
    for day in range(1, days + 1):
        slots = []
        for i, (t, label) in enumerate(_SLOTS):
            interest = interests[(day + i) % len(interests)]
            slots.append({"time": t, "slot": label, "theme": interest,
                          "suggestion": f"{label} in {destination}: {interest} (day {day})"})
        plan.append({"day": day, "slots": slots})
    return {"status": "ok", "destination": destination, "days": days,
            "interests": interests, "itinerary": plan,
            "note": "Suggestions are structural; use the booking skill for real reservations."}


ACTIONS = {
    "build_itinerary": ActionDef("Build a day-by-day itinerary.",
        {"destination": {"type": "string"}, "days": {"type": "integer", "default": 3},
         "interests": {"type": "array", "items": {"type": "string"},
                       "description": "e.g. ['food', 'museums', 'hiking']"}},
        ["destination"], build_itinerary),
}
