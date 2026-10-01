"""Input validation: params are checked against the action's JSON schema
before any handler runs. The LLM gets precise, actionable errors instead
of Python tracebacks from deep inside a driver.
"""
from __future__ import annotations

from typing import Any

_TYPEMAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def validate_params(skill: str, action: str, parameters: dict[str, Any],
                    required: list[str], params: dict) -> dict:
    """Validate `params` against the action schema. Returns the params unchanged.

    Raises InvalidInput with a list of human-readable problems.
    Unknown extra params are allowed (forward compatibility) but required
    params and types are enforced strictly.
    """
    from .errors import InvalidInput

    problems: list[str] = []
    if not isinstance(params, dict):
        raise InvalidInput(skill, action, ["params must be an object"])

    for name in required:
        if name not in params or params[name] is None:
            problems.append(f"missing required parameter: '{name}'")

    for name, spec in parameters.items():
        if name not in params or params[name] is None:
            continue
        value = params[name]
        want = spec.get("type") if isinstance(spec, dict) else None
        if want and want in _TYPEMAP and not isinstance(value, _TYPEMAP[want]):
            # bool is a subclass of int — reject bool where integer is wanted
            if want == "integer" and isinstance(value, bool):
                problems.append(f"'{name}' must be integer, got boolean")
            elif not (want == "integer" and isinstance(value, bool)):
                problems.append(
                    f"'{name}' must be {want}, got {type(value).__name__}")
        if isinstance(spec, dict):
            if "enum" in spec and value not in spec["enum"]:
                problems.append(f"'{name}' must be one of {spec['enum']}")
            if want == "string" and isinstance(value, str):
                if "maxLength" in spec and len(value) > spec["maxLength"]:
                    problems.append(f"'{name}' exceeds maxLength {spec['maxLength']}")
                if "minLength" in spec and len(value) < spec["minLength"]:
                    problems.append(f"'{name}' below minLength {spec['minLength']}")
            if want in ("integer", "number") and isinstance(value, (int, float)):
                if "minimum" in spec and value < spec["minimum"]:
                    problems.append(f"'{name}' below minimum {spec['minimum']}")
                if "maximum" in spec and value > spec["maximum"]:
                    problems.append(f"'{name}' above maximum {spec['maximum']}")

    if problems:
        raise InvalidInput(skill, action, problems)
    return params
