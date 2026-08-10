#!/usr/bin/env python3
"""Fail if the `image` choice options in build.yml drift from the images/*/
directories. Called by .github/workflows/sync-check.yml.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def main() -> int:
    with open(".github/workflows/build.yml") as f:
        wf = yaml.safe_load(f)
    # PyYAML parses the bare `on:` key as boolean True.
    on = wf.get("on") or wf.get(True) or {}
    options = sorted((on.get("workflow_dispatch") or {}).get("inputs", {}).get("image", {}).get("options", []))

    dirs = sorted(p.name for p in Path("images").iterdir() if p.is_dir())

    print("workflow 'image' choice options:")
    print("\n".join(options))
    print("images/*/ directories:")
    print("\n".join(dirs))

    if options != dirs:
        print("::error::workflow 'image' choice options do not match images/*/ directories. Update both the choice list and the images/ directory.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
