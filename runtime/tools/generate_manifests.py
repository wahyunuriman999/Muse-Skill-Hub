"""Generate skills/<name>/manifest.yaml from the registry (canonical contract).

Thin wrapper around skillhub.manifests — the generator logic lives in the
package so `skillhub validate` can regenerate manifests in memory and fail
on any driver/manifest/SKILL.md drift.

Run:  python runtime/tools/generate_manifests.py

Risk preservation: the manifest is the canonical risk source and may be
hand-tuned. The generator only overwrites a manifest risk when the driver
declares an explicit ActionDef(risk=...); otherwise the existing manifest
risk is kept (new actions fall back to the driver default).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub.manifests import main

if __name__ == "__main__":
    main()
