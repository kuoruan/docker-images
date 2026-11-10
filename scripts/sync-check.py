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
    dispatch = on.get("workflow_dispatch") or {}
    image_input = (dispatch.get("inputs") or {}).get("image") or {}
    options = sorted(image_input.get("options") or [])

    # glob("*/") matches directories only, and yields nothing when images/ is
    # missing instead of raising.
    dirs = sorted(p.name for p in Path("images").glob("*/"))

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
