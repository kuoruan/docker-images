#!/usr/bin/env python3
"""Bump each image.yml's `version` to the latest upstream release, when the
image declares an `update.github` source. Writes changed images (as
``image<TAB>version`` lines) to ``.changes`` and ``changed=<n>`` to
``$GITHUB_OUTPUT``, so the workflow can tag each bumped image.

If an image ships an ``update-check.sh`` hook, it decides whether the new
version is allowed: the hook receives the upstream tag as its only argument,
exit 0 permits the bump, and any other exit status (or a timeout/failure to
run it) skips that image so the current pin is kept. This lets an image veto a
release its build cannot produce, for example when its patches no longer
apply.

Reads and writes with PyYAML (YAML round-trip); blank lines/comments are not
preserved. Called by .github/workflows/update-versions.yml.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

CHANGES_FILE = Path(".changes")
UPDATE_CHECK = "update-check.sh"
# The hook may download and patch an upstream source tree; bound it so a
# stalled fetch cannot wedge the whole update run.
HOOK_TIMEOUT = 600


def latest_release(repo: str) -> str | None:
    """Return the latest release tag for a ``owner/name`` repo, or None."""
    try:
        out = subprocess.run(
            ["gh", "release", "view", "-R", repo, "--json", "tagName", "-q", ".tagName"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return out.stdout.strip() or None


def bump_allowed(name: str, tag: str) -> bool:
    """Ask the image's update-check hook whether ``tag`` may be bumped to.

    Images without a hook are always allowed. A rejecting hook's last output
    line is reported as the reason.
    """
    hook = Path("images") / name / UPDATE_CHECK
    if not hook.exists():
        return True
    if not hook.is_file():
        # A directory or other non-file named like the hook would make `sh`
        # exit 0 and silently allow the bump.
        print(f"::warning::{name}: {UPDATE_CHECK} is not a regular file; skipping")
        return False
    try:
        proc = subprocess.run(
            ["sh", str(hook), tag],
            capture_output=True,
            text=True,
            check=False,
            timeout=HOOK_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"::warning::{name}: {UPDATE_CHECK} timed out after {HOOK_TIMEOUT}s for {tag}; skipping")
        return False
    except OSError as exc:
        print(f"::warning::{name}: could not run {UPDATE_CHECK} ({exc}); skipping")
        return False
    if proc.returncode != 0:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
        print(f"::warning::{name}: {UPDATE_CHECK} rejected {tag}: {lines[-1] if lines else 'hook failed'}")
        return False
    return True


def main() -> int:
    changed: list[tuple[str, str]] = []

    for img_path in sorted(Path("images").glob("*/image.yml")):
        name = img_path.parent.name
        with open(img_path) as f:
            img = yaml.safe_load(f) or {}

        update = img.get("update") or {}
        repo = update.get("github")
        if not repo:
            print(f"skip {name}: no update.github configured")
            continue

        prefix = update.get("tag_prefix") or ""
        tag = latest_release(repo)
        if tag is None:
            print(f"::warning::{name}: failed to fetch latest release from {repo}, skipping")
            continue
        latest = tag.removeprefix(prefix)
        cur = str(img.get("version", ""))

        print(f"{name}: current={cur} latest={latest} (repo={repo}, tag={tag})")

        if cur == latest:
            continue

        if not bump_allowed(name, tag):
            print(f"::warning::{name}: keeping {cur}")
            continue

        # Write the bumped version back.
        img["version"] = latest
        with open(img_path, "w") as f:
            yaml.safe_dump(img, f, sort_keys=False, default_flow_style=False)

        # Verify the write landed.
        with open(img_path) as f:
            got = str((yaml.safe_load(f) or {}).get("version", ""))
        if got != latest:
            print(f"::error::{name}: version edit failed (expected {latest}, got {got})")
            return 1

        changed.append((name, latest))
        print(f"{name}: bumped {cur} -> {latest}")

    with CHANGES_FILE.open("w") as f:
        for name, ver in changed:
            f.write(f"{name}\t{ver}\n")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"changed={len(changed)}\n")

    print(f"::group::Bump summary ({len(changed)} changed)")
    for name, ver in changed:
        print(f"{name}\t{ver}")
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
