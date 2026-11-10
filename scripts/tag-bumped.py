#!/usr/bin/env python3
"""Tag each image listed in ``.changes`` as ``<image>/v<version>`` and push.

``.changes`` is written by ``update-versions.py`` as ``image<TAB>version``
lines, one per bumped image. The tags record which version was released; they
are not the build trigger, because GitHub starts no run for a push made with the
default ``GITHUB_TOKEN``. ``dispatch-builds.py`` starts the builds.

Existence is checked against the remote once per run (``git ls-remote``) so a
tag that was created locally but failed to push is retried instead of being
silently skipped. If a push fails, the local tag is rolled back so the next run
can retry cleanly. Called by ``.github/workflows/update-versions.yml`` after the
commit step.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHANGES_FILE = Path(".changes")


def remote_tags() -> set[str] | None:
    """Return the tags that already exist on the remote (origin), or None."""
    try:
        r = subprocess.run(
            ["git", "ls-remote", "--tags", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"::error::git ls-remote failed: {(exc.stderr or '').strip()}", file=sys.stderr)
        return None
    tags = set()
    for line in r.stdout.splitlines():
        _, _, ref = line.partition("\t")
        # Peeled entries for annotated tags (refs/tags/x^{}) are not tag names.
        if ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tags.add(ref[len("refs/tags/"):])
    return tags


def main() -> int:
    if not CHANGES_FILE.exists():
        print("no .changes file; nothing to tag")
        return 0

    remote = remote_tags()
    if remote is None:
        return 1

    for line in CHANGES_FILE.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            print(f"::warning::skipping malformed .changes line: {line!r}")
            continue
        name, version = parts
        # The `v` is a fixed marker in the tag name, not image.yml's
        # `tag_prefix`: build-meta.py strips it and re-applies the prefix, so
        # the round-trip holds for any prefix.
        tag = f"{name}/v{version}"

        if tag in remote:
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
        remote.add(tag)
        print(f"tagged {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
