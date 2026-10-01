"""JSON Schema validation for action inputs AND outputs.

``validate_params`` checks caller params against the action's input schema
before any handler runs. ``validate_output`` checks the handler's result
against the action's ``output_schema`` after execution — a declared contract
that is actually enforced, not just documented.

Supported keywords: type, enum, const, pattern, format (email/uri/date-time),
minLength/maxLength, minimum/maximum, exclusiveMinimum/exclusiveMaximum,
multipleOf, items, minItems/maxItems, uniqueItems, properties, required,
additionalProperties, oneOf/anyOf/allOf/not, nested objects/arrays.

The schema is the source of truth: when an action is ``strict`` (the
default), unknown parameters are rejected — matching the
``additionalProperties: false`` declared on every MCP tool.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_TYPEMAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_format(fmt: str, value: str, path: str, problems: list[str]) -> None:
    if fmt == "email" and not _EMAIL_RE.match(value):
        problems.append(f"'{path}' must be a valid email")
    elif fmt == "uri":
        try:
            p = urlparse(value)
            if not p.scheme or not p.netloc:
                problems.append(f"'{path}' must be a valid uri")
        except Exception:
            problems.append(f"'{path}' must be a valid uri")
    elif fmt == "date-time":
        try:
            from datetime import datetime
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            problems.append(f"'{path}' must be a valid date-time")


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_type(want: str, value: Any) -> bool:
    if want == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if want == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    py = _TYPEMAP.get(want)
    return isinstance(value, py) if py else True


def _validate_value(path: str, spec: Any, value: Any, problems: list[str]) -> None:
    """Recursive JSON Schema validation. Appends human-readable problems."""
    if not isinstance(spec, dict):
        return
    # boolean schemas
    if spec is True:
        return
    if spec is False:
        problems.append(f"'{path}' is not allowed here")
        return

    want = spec.get("type")
    if want:
        wants = [want] if isinstance(want, str) else list(want)
        if not any(_matches_type(w, value) for w in wants):
            problems.append(
                f"'{path}' must be {'/'.join(wants)}, got {_type_name(value)}")
            return  # further keyword checks are meaningless on wrong type

    if "enum" in spec and value not in spec["enum"]:
        problems.append(f"'{path}' must be one of {spec['enum']}")
    if "const" in spec and value != spec["const"]:
        problems.append(f"'{path}' must equal {spec['const']!r}")

    if isinstance(value, str):
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            problems.append(f"'{path}' exceeds maxLength {spec['maxLength']}")
        if "minLength" in spec and len(value) < spec["minLength"]:
            problems.append(f"'{path}' below minLength {spec['minLength']}")
        if "pattern" in spec:
            try:
                if not re.search(spec["pattern"], value):
                    problems.append(f"'{path}' does not match pattern "
                                    f"{spec['pattern']!r}")
            except re.error:
                problems.append(f"'{path}' has an invalid pattern in its schema")
        if "format" in spec:
            _check_format(spec["format"], value, path, problems)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            problems.append(f"'{path}' below minimum {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            problems.append(f"'{path}' above maximum {spec['maximum']}")
        if "exclusiveMinimum" in spec and value <= spec["exclusiveMinimum"]:
            problems.append(f"'{path}' must be > {spec['exclusiveMinimum']}")
        if "exclusiveMaximum" in spec and value >= spec["exclusiveMaximum"]:
            problems.append(f"'{path}' must be < {spec['exclusiveMaximum']}")
        if "multipleOf" in spec:
            try:
                if value % spec["multipleOf"] != 0:
                    problems.append(f"'{path}' must be a multiple of "
                                    f"{spec['multipleOf']}")
            except Exception:
                pass

    if isinstance(value, list):
        if "minItems" in spec and len(value) < spec["minItems"]:
            problems.append(f"'{path}' needs at least {spec['minItems']} items")
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            problems.append(f"'{path}' allows at most {spec['maxItems']} items")
        if spec.get("uniqueItems"):
            try:
                seen = {repr(v) for v in value}
                if len(seen) != len(value):
                    problems.append(f"'{path}' must contain unique items")
            except Exception:
                pass
        items = spec.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(value):
                _validate_value(f"{path}[{i}]", items, item, problems)
        elif isinstance(items, list):  # tuple form
            for i, (sub, item) in enumerate(zip(items, value)):
                _validate_value(f"{path}[{i}]", sub, item, problems)

    if isinstance(value, dict):
        properties = spec.get("properties") or {}
        for name in spec.get("required", []) or []:
            if name not in value or value[name] is None:
                problems.append(f"'{path}.{name}' is required" if path
                                else f"missing required parameter: '{name}'")
        for name, subspec in properties.items():
            if name in value and value[name] is not None:
                sub_path = f"{path}.{name}" if path else name
                _validate_value(sub_path, subspec, value[name], problems)
        if spec.get("additionalProperties") is False:
            extra = [k for k in value if k not in properties]
            for k in extra:
                sub_path = f"{path}.{k}" if path else k
                problems.append(f"unknown parameter: '{sub_path}'")

    # combinators
    for kw in ("oneOf", "anyOf"):
        if kw in spec and isinstance(spec[kw], list):
            matches = 0
            for sub in spec[kw]:
                sub_problems: list[str] = []
                _validate_value(path, sub, value, sub_problems)
                if not sub_problems:
                    matches += 1
            if kw == "oneOf" and matches != 1:
                problems.append(f"'{path}' must match exactly one schema "
                                f"in oneOf (matched {matches})")
            elif kw == "anyOf" and matches == 0:
                problems.append(f"'{path}' must match at least one schema in anyOf")
    if "allOf" in spec and isinstance(spec["allOf"], list):
        for sub in spec["allOf"]:
            _validate_value(path, sub, value, problems)
    if "not" in spec and isinstance(spec["not"], dict):
        sub_problems = []
        _validate_value(path, spec["not"], value, sub_problems)
        if not sub_problems:
            problems.append(f"'{path}' must not match the forbidden schema")


def validate_params(skill: str, action: str, parameters: dict[str, Any],
                    required: list[str], params: dict,
                    strict: bool = True) -> dict:
    """Validate `params` against the action schema. Returns params unchanged.

    Raises InvalidInput with a list of human-readable problems.
    When ``strict`` (default), unknown params are rejected — the schema is
    the source of truth, matching ``additionalProperties: false`` on the
    MCP tool declaration.
    """
    from .errors import InvalidInput

    problems: list[str] = []
    if not isinstance(params, dict):
        raise InvalidInput(skill, action, ["params must be an object"])

    schema = {
        "type": "object",
        "properties": parameters or {},
        "required": required or [],
        "additionalProperties": not strict,
    }
    _validate_value("", schema, params, problems)
    if problems:
        raise InvalidInput(skill, action, problems)
    return params


def validate_output(skill: str, action: str, output_schema: dict[str, Any],
                    result: Any) -> Any:
    """Validate a handler's result against its declared output_schema.

    Empty schema → no constraints, passes. Violations raise
    OutputContractViolation (a driver bug, never a caller error).
    """
    from .errors import OutputContractViolation

    if not output_schema:
        return result
    problems: list[str] = []
    _validate_value("result", output_schema, result, problems)
    if problems:
        raise OutputContractViolation(
            f"{skill}.{action} returned a result that violates its "
            f"output_schema.",
            internal={"action": f"{skill}.{action}", "problems": problems,
                      "result_type": _type_name(result)})
    return result
