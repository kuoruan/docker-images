#!/usr/bin/env python3
"""Dispatch the Build Image workflow for each image in ``.changes``.

Update Versions cannot rely on its own tags to start a build: GitHub creates no
workflow run for a push made with the default ``GITHUB_TOKEN``. Dispatching the
workflow through the API instead needs the ``actions: write`` permission granted
in ``.github/workflows/update-versions.yml``.

``.changes`` is written by ``update-versions.py`` as ``image<TAB>version`` lines,
one per bumped image. Called by ``.github/workflows/update-versions.yml`` after
the commit and tag steps.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHANGES_FILE = Path(".changes")
BUILD_WORKFLOW = "build.yml"


def main() -> int:
    if not CHANGES_FILE.exists():
        print("no .changes file; nothing to dispatch")
        return 0

    failed: list[str] = []
    for line in CHANGES_FILE.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            print(f"::warning::skipping malformed .changes line: {line!r}")
            continue
        name, version = parts

        r = subprocess.run(
            ["gh", "workflow", "run", BUILD_WORKFLOW, "-f", f"image={name}", "-f", f"version={version}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            # Keep going: one rejected dispatch should not hide the others.
            failed.append(name)
            print(f"::error::failed to dispatch {BUILD_WORKFLOW} for {name} {version}: {(r.stderr or '').strip()}")
            continue
        print(f"dispatched {BUILD_WORKFLOW} for {name} {version}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
