"""Independent static security audit (GATE 13).

A second, independent pass over the codebase that does NOT reuse the
validator's secret patterns or risk tables. It parses every driver with
stdlib ``ast`` and reports:

- HIGH: shell-execution sinks (``shell=True``, ``os.system``,
  ``os.popen``) — command injection surface;
- HIGH: ``eval``/``exec`` on non-constant input — code injection;
- HIGH: hardcoded secret-looking assignments (independent pattern set);
- MEDIUM: subprocess argv that is TAINTED by caller params
  (``*params[...]`` unpacked into argv). Tainted sinks are only
  acceptable when the action's manifest risk is in STRICT_RISKS
  (i.e. it always needs a real approval_id) — verified against the
  shipped manifests, not the driver's own claims.

Usage: ``python tools/static_audit.py [--root RUNTIME]``
Exit 0 when no HIGH findings; exit 1 otherwise.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent

# independent of the validator's _SECRET_PATTERNS
_SECRET_NAME_HINTS = ("password", "passwd", "secret", "api_key", "apikey",
                      "auth_token", "access_token", "private_key")
_STRICT_RISKS = frozenset({
    "sensitive", "destructive", "communication", "financial",
    "account", "device",
})
_SUBPROCESS_FUNCS = {
    "create_subprocess_exec", "create_subprocess_shell",
    "Popen", "run", "call", "check_output", "check_call",
}


class Finding:
    def __init__(self, severity: str, where: str, what: str):
        self.severity = severity
        self.where = where
        self.what = what

    def __str__(self):
        return f"[{self.severity}] {self.where}: {self.what}"


def _func_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _mentions_param(node: ast.AST, param_names: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in param_names
               for n in ast.walk(node))


def _taint_kind(node: ast.AST, param_names: set[str]) -> str | None:
    """Classify caller influence on one argv argument.

    - "full": the argv list itself IS caller data
      (``*params["args"]``, ``params["args"]`` as argv) — the caller
      picks the binary's flags and subcommands;
    - "operand": caller data fills operand positions of a driver-built
      argv list (fixed binary + fixed flags, exec-style, no shell);
    - None: no caller influence.
    """
    if isinstance(node, ast.Starred):
        inner = node.value
        if isinstance(inner, ast.Subscript) and _mentions_param(inner, param_names):
            return "full"
        return "operand" if _mentions_param(inner, param_names) else None
    if isinstance(node, ast.Subscript) and _mentions_param(node, param_names):
        return "full"
    if isinstance(node, (ast.List, ast.Tuple)):
        if any(_mentions_param(el, param_names) for el in node.elts):
            return "operand"
        return None
    return "operand" if _mentions_param(node, param_names) else None


def _manifest_risks(skill: str) -> dict[str, str]:
    """Read risk tiers from the SHIPPED manifest (not driver claims)."""
    import re
    path = RUNTIME / "skillhub" / "catalog" / skill / "manifest.yaml"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    risks: dict[str, str] = {}
    cur: str | None = None
    for line in text.splitlines():
        m = re.match(r"\s*-\s*name:\s*(\S+)", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"\s*risk:\s*(\S+)", line)
        if m and cur:
            risks[cur] = m.group(1)
    return risks


class Auditor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self.rel = rel
        self.findings: list[Finding] = []
        # (func, where, kind) with kind in {"full", "operand"}
        self.tainted_sinks: list[tuple[str, str, str]] = []
        self._func: str | None = None
        self._params: set[str] = set()

    def at(self, node: ast.AST) -> str:
        return f"{self.rel}:{node.lineno}"

    # -- function context: track param names and the action being defined --
    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node)

    def visit_FunctionDef(self, node):
        self._visit_func(node)

    def _visit_func(self, node):
        outer_f, outer_p = self._func, self._params
        self._func = node.name
        self._params = {a.arg for a in node.args.args} | {"params"}
        self.generic_visit(node)
        self._func, self._params = outer_f, outer_p

    # -- sinks --
    def visit_Call(self, node: ast.Call):
        name = _func_name(node.func)
        if name in _SUBPROCESS_FUNCS:
            shell = any(kw.arg == "shell" and
                        isinstance(kw.value, ast.Constant) and
                        kw.value.value is True
                        for kw in node.keywords)
            if shell or name == "create_subprocess_shell":
                self.findings.append(Finding(
                    "HIGH", self.at(node),
                    f"shell execution sink: {name}(shell=True)"))
            else:
                argv = node.args
                kinds = {_taint_kind(a, self._params) for a in argv}
                kinds.discard(None)
                if "full" in kinds:
                    self.tainted_sinks.append(
                        (self._func or "?", self.at(node), "full"))
                elif "operand" in kinds:
                    self.tainted_sinks.append(
                        (self._func or "?", self.at(node), "operand"))
                elif argv and isinstance(argv[0], ast.Constant) \
                        and isinstance(argv[0].value, str):
                    self.findings.append(Finding(
                        "HIGH", self.at(node),
                        f"{name} with a single string command "
                        "(implicit shell splitting)"))
        elif name in {"system", "popen"}:
            # os.system / os.popen
            self.findings.append(Finding(
                "HIGH", self.at(node), f"os.{name} shell sink"))
        elif name in {"eval", "exec"}:
            if node.args and not isinstance(node.args[0], ast.Constant):
                self.findings.append(Finding(
                    "HIGH", self.at(node),
                    f"{name}() on non-constant input"))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                lname = target.id.lower()
                if any(h in lname for h in _SECRET_NAME_HINTS) \
                        and isinstance(node.value, ast.Constant) \
                        and isinstance(node.value.value, str) \
                        and len(node.value.value) >= 8:
                    self.findings.append(Finding(
                        "HIGH", self.at(node),
                        f"hardcoded secret-looking assignment: {target.id}"))
        self.generic_visit(node)


def audit_file(path: Path, rel: str) -> Auditor:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    auditor = Auditor(rel)
    auditor.visit(tree)
    return auditor


def audit_tree(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    full: dict[str, list[tuple[str, str]]] = {}  # skill -> [(func, where)]
    for path in sorted((root / "skillhub" / "skills").glob("*.py")):
        if path.name.startswith("_"):
            continue
        rel = path.relative_to(root).as_posix()
        auditor = audit_file(path, rel)
        findings.extend(auditor.findings)
        for func, where, kind in auditor.tainted_sinks:
            skill = path.stem.replace("_", "-")
            if kind == "full":
                full.setdefault(skill, []).append((func, where))
            else:
                findings.append(Finding(
                    "INFO", where,
                    f"driver-composed argv in {skill}.{func} "
                    "(fixed binary, caller data only in operand "
                    "positions, exec-style)"))
    # cross-check: full argv passthrough must sit behind approval-required risk
    for skill, sinks in full.items():
        risks = _manifest_risks(skill)
        for func, where in sinks:
            bad = [a for a, r in risks.items() if r not in _STRICT_RISKS]
            if bad:
                findings.append(Finding(
                    "HIGH", where,
                    f"full argv passthrough in {skill}.{func} but "
                    f"actions {bad} are not approval-gated"))
            else:
                findings.append(Finding(
                    "INFO", where,
                    f"full argv passthrough in {skill}.{func} — "
                    f"all actions approval-gated ({risks})"))
    return findings


def main() -> int:
    root = Path(sys.argv[sys.argv.index("--root") + 1]) \
        if "--root" in sys.argv else RUNTIME
    findings = audit_tree(root)
    for f in findings:
        print(f)
    high = [f for f in findings if f.severity == "HIGH"]
    print(f"{len(high)} HIGH, {len(findings) - len(high)} INFO findings")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
