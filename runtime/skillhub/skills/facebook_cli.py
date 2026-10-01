"""facebook-cli passthrough driver.

Runs the user's installed `facebook-cli` binary and returns its output.
Setup: install the CLI (see the facebook-cli SKILL.md), then it is used as-is.
"""
from __future__ import annotations

import asyncio
import shutil

from ..driver import ActionDef
from ..errors import SkillError

SKILL = "facebook-cli"
REQUIRED_ENV: list[str] = []
SETUP_HELP = (
    "Install the facebook-cli binary and make sure it is on PATH "
    "(see skills/facebook-cli/SKILL.md for install instructions)."
)


def _bin() -> str:
    path = shutil.which("facebook-cli")
    if not path:
        raise SkillError(SKILL, "cli_not_installed", SETUP_HELP)
    return path


async def run_command(params: dict) -> dict:
    proc = await asyncio.create_subprocess_exec(
        _bin(), *params["args"],
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return {"status": "ok", "exit_code": proc.returncode,
            "stdout": out.decode(errors="replace")[:8000],
            "stderr": err.decode(errors="replace")[:2000]}


ACTIONS = {
    "run_command": ActionDef("Run a facebook-cli command and return its output.",
        {"args": {"type": "array", "items": {"type": "string"},
                  "description": "e.g. ['post', '--help']"}},
        ["args"], run_command,
        # Broad argv passthrough: the caller controls the full facebook-cli
        # command surface (read, post, delete, message as the user), so this
        # is typed destructive — it always needs a real approval_id.
        risk="destructive"),
}
