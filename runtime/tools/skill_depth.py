"""Skill depth markers for the README Skill List table.

Depth is derived from the skill registry — never hand-written:

  Full     — has at least one mutating action (write, sensitive,
             destructive, communication, financial, account, device).
             The skill can act, not just read.
  Standard — 3+ actions, all read-only. Decent coverage, no writes.
  Limited  — 1-2 actions, all read-only. Narrow surface, often
             API-limited (e.g. canva's 2 read-only actions).
  Stub     — not implemented (honest stub).

Usage:
  python tools/skill_depth.py --write   # add/update Depth column + legend
  python tools/skill_depth.py --check   # exit 1 if the table is out of sync
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "README.md"

MUTATING = {"write", "sensitive", "destructive",
            "communication", "financial", "account", "device"}

LEGEND = """<!-- DEPTH-LEGEND:START -->
**Depth** is computed from the skill registry, not hand-written:

- **Full** — has mutating actions (write, send, pay, delete, …): the skill can act, not just read.
- **Standard** — 3+ actions, all read-only.
- **Limited** — 1–2 read-only actions (narrow surface, often API-limited).
- **Stub** — not implemented yet (honest stub).
<!-- DEPTH-LEGEND:END -->"""


def depth_of(entry) -> str:
    if not entry.implemented or not entry.actions:
        return "Stub"
    if any(d.risk in MUTATING for d in entry.actions.values()):
        return "Full"
    if len(entry.actions) >= 3:
        return "Standard"
    return "Limited"


def compute_depths() -> dict:
    sys.path.insert(0, str(REPO / "runtime"))
    from skillhub import registry
    reg = registry.load_registry()
    return {name: depth_of(e) for name, e in reg.items()}


def render_table(lines: list, depths: dict) -> list:
    """Rewrite the Skill List table with an accurate Depth column + legend."""
    out = []
    i = 0
    # copy everything up to and including the "## Skill List" header
    while i < len(lines) and lines[i].strip() != "## Skill List":
        out.append(lines[i])
        i += 1
    if i < len(lines):
        out.append(lines[i])  # the header itself
        i += 1
    out.append("")
    out.append(LEGEND)
    out.append("")
    # skip blank lines, then consume the existing table (if any)
    while i < len(lines) and not lines[i].startswith("|"):
        i += 1
    # skip old legend block if present (idempotency)
    table_start = i
    while i < len(lines) and lines[i].startswith("|"):
        i += 1
    # rebuild table from depths, preserving Skill/Title/Description text
    # from the old rows keyed by skill name
    old = {}
    for ln in lines[table_start:i]:
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if len(parts) >= 3 and parts[0].startswith("`"):
            old[parts[0].strip("`")] = parts
    header = "| Skill | Title | Description | Depth |"
    sep = "|-------|-------|-------------|-------|"
    out.append(header)
    out.append(sep)
    for name in sorted(depths):
        depth = depths[name]
        if name in old and len(old[name]) >= 3:
            _, title, desc = old[name][:3]
            skill_cell = f"`{name}`"
        else:
            title, desc, skill_cell = name, "", f"`{name}`"
        out.append(f"| {skill_cell} | {title} | {desc} | {depth} |")
    # copy the rest
    out.extend(lines[i:])
    return out


def check(readme_text: str, depths: dict) -> list:
    """Return a list of problems; empty means in sync."""
    problems = []
    if "<!-- DEPTH-LEGEND:START -->" not in readme_text:
        problems.append("depth legend block missing")
    section = readme_text.split("## Skill List", 1)
    if len(section) < 2:
        return problems + ["## Skill List section missing"]
    rows = {}
    for ln in section[1].splitlines():
        if not ln.startswith("|"):
            if rows:
                break
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if len(parts) == 4 and parts[0].startswith("`") and parts[0] != "`Skill`":
            rows[parts[0].strip("`")] = parts[3]
    for name, want in sorted(depths.items()):
        got = rows.get(name)
        if got is None:
            problems.append(f"row missing for skill {name!r}")
        elif got != want:
            problems.append(f"{name}: table says {got!r}, registry says {want!r}")
    return problems


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    depths = compute_depths()
    text = README.read_text(encoding="utf-8")
    if mode == "--write":
        new_lines = render_table(text.splitlines(), depths)
        README.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"updated {README} ({len(depths)} skills)")
        return 0
    if mode == "--check":
        problems = check(text, depths)
        if problems:
            print("skill depth table out of sync:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"skill depth table in sync ({len(depths)} skills)")
        return 0
    print(f"unknown mode {mode!r}; want --write or --check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
