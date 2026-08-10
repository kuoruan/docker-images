#!/usr/bin/env python3
"""Tag each image listed in ``.changes`` as ``<image>/v<version>`` and push.

``.changes`` is written by ``update-versions.py`` as ``image<TAB>version``
lines, one per bumped image. Pushing a tag of the form ``<image>/v<version>``
triggers the Build Image workflow (its ``push.tags`` trigger).

Existence is checked against the remote (``git ls-remote``) so a tag that was
created locally but failed to push is retried instead of being silently
skipped. If a push fails, the local tag is rolled back so the next run can
retry cleanly. Called by ``.github/workflows/update-versions.yml`` after the
commit step.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHANGES_FILE = Path(".changes")


def remote_tag_exists(tag: str) -> bool:
    """True if the tag already exists on the remote (origin)."""
    r = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and bool(r.stdout.strip())


def main() -> int:
    if not CHANGES_FILE.exists():
        print("no .changes file; nothing to tag")
        return 0

    for line in CHANGES_FILE.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            print(f"::warning::skipping malformed .changes line: {line!r}")
            continue
        name, version = parts
        tag = f"{name}/v{version}"

        if remote_tag_exists(tag):
            print(f"tag {tag} already exists on remote, skipping")
            continue

        subprocess.run(["git", "tag", tag], check=True)
        try:
            subprocess.run(["git", "push", "origin", tag], check=True)
        except subprocess.CalledProcessError:
            # Roll back the local-only tag so the next run retries cleanly.
            subprocess.run(["git", "tag", "-d", tag], capture_output=True)
            print(f"::error::failed to push tag {tag}; rolled back local tag")
            return 1
        print(f"tagged {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
