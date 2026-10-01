"""JSON Schema validation for action inputs AND outputs.

Implemented on the standard ``jsonschema`` library (Draft 2020-12) with a
format checker — the real JSON Schema vocabulary (``$ref``/``$defs``,
``if``/``then``/``else``, ``dependentRequired``, ``contains``,
``propertyNames``, ``unevaluatedProperties``, ``contentSchema``, …),
not a hand-rolled subset.

``validate_params`` checks caller params against the action's input schema
before any handler runs. ``validate_output`` checks the handler's result
against the action's ``output_schema`` after execution — a declared contract
that is actually enforced, not just documented.

The schema is the source of truth: when an action is ``strict`` (the
default), unknown parameters are rejected via
``additionalProperties: false``, matching the MCP tool declaration.
Optional parameters explicitly passed as ``None`` are treated as absent
(lenient, backwards-compatible); ``None`` for a *required* parameter is
still rejected.
"""
from __future__ import annotations

from typing import Any

import jsonschema
from jsonschema import Draft202012Validator, FormatChecker

_FORMAT_CHECKER = FormatChecker()


def _validator_for(schema: dict) -> Draft202012Validator:
    # NOTE: no check_schema() on the hot path — driver schemas are linted
    # by `skillhub validate`; a malformed schema must not become a new
    # runtime crash mode at dispatch time.
    return Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)


def _problems(schema: dict, value: Any) -> list[str]:
    validator = _validator_for(schema)
    problems = []
    for error in sorted(validator.iter_errors(value),
                        key=lambda e: (list(e.absolute_path), e.message)):
        loc = "$" + "".join(f"[{p!r}]" if not isinstance(p, str)
                            else f".{p}" for p in error.absolute_path)
        problems.append(f"{loc}: {error.message}")
    return problems


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

    if not isinstance(params, dict):
        raise InvalidInput(skill, action, ["params must be an object"])

    required = required or []
    # lenient: explicit None for an *optional* param means "absent"
    check = {k: v for k, v in params.items()
             if v is not None or k in required}
    parameters = dict(parameters or {})
    # hoist $defs so actions can use $ref (full Draft 2020-12 vocabulary)
    defs = parameters.pop("$defs", None)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": parameters,
        "required": required,
        "additionalProperties": not strict,
    }
    if defs:
        schema["$defs"] = defs
    problems = _problems(schema, check)
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
    problems = _problems(dict(output_schema), result)
    if problems:
        raise OutputContractViolation(
            f"{skill}.{action} returned a result that violates its "
            f"output_schema.",
            internal={"action": f"{skill}.{action}", "problems": problems,
                      "result_type": type(result).__name__})
    return result
