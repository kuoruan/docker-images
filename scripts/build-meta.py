#!/usr/bin/env python3
"""Resolve which image + version to build, validate the image directory,
and emit version/platforms for later steps.

Trigger sources (read from the environment GitHub Actions sets):
    push (tag)        -> parse <image>/v<version> from GITHUB_REF
    workflow_dispatch -> use INPUT_IMAGE / INPUT_VERSION (version may be
       empty, in which case image.yml's version is used)

Env:
    INPUT_IMAGE     image to build (workflow_dispatch only)
    INPUT_VERSION   version override (workflow_dispatch only; may be empty)
    GITHUB_REF      refs/tags/<image>/v<version> on tag push
    GITHUB_EVENT_NAME  push | workflow_dispatch
    GITHUB_OUTPUT   step output file

Writes image=, version=, base_version=, platforms=, release= to
$GITHUB_OUTPUT. Called by .github/workflows/build.yml.

Version model:
    version      what `xcaddy build` compiles: a semver tag or a full 40-char
                 commit hash (input wins over image.yml).
    base_version the caddy:<x>-builder/-alpine base image tag; always a semver:
                 follows version when it is a semver, else falls back to
                 image.yml's version (Docker Hub has no <hash>-builder tag).
    release      true for semver builds (tagged latest), false for hashes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$")
# Full 40-char git commit hash (for building unreleased fixes).
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def resolve_from_event() -> tuple[str, str]:
    """Return (image, version_hint) from the triggering event.

    version_hint may be empty (workflow_dispatch with no version input),
    meaning "use image.yml".
    """
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "push":
        ref = os.environ.get("GITHUB_REF", "")
        if not ref.startswith("refs/tags/"):
            print(f"::error::expected a tag ref (refs/tags/...), got: {ref}", file=sys.stderr)
            sys.exit(1)
        tag = ref[len("refs/tags/"):]
        if "/" not in tag:
            print(f"::error::Tag '{tag}' is not of the form <image>/v<version>", file=sys.stderr)
            sys.exit(1)
        image, vpart = tag.split("/", 1)
        return image, vpart.removeprefix("v")
    # workflow_dispatch
    image = os.environ.get("INPUT_IMAGE", "")
    version = (os.environ.get("INPUT_VERSION") or "").strip()
    return image, version


def main() -> int:
    image, version_input = resolve_from_event()
    if not image:
        print("::error::image could not be resolved from the event", file=sys.stderr)
        return 1

    img_dir = Path("images") / image
    img_yml = img_dir / "image.yml"
    dockerfile = img_dir / "Dockerfile"
    for p in (img_dir, dockerfile, img_yml):
        if not p.exists():
            print(f"::error::{p} not found", file=sys.stderr)
            return 1

    with open(img_yml) as f:
        img = yaml.safe_load(f) or {}

    version = version_input or str(img.get("version", ""))

    is_commit = bool(COMMIT_RE.match(version))
    if not is_commit and not VERSION_RE.match(version):
        print(
            f"::error::Version must be a concrete tag such as 2.11.4, or a full "
            f"40-char commit hash (got: {version})",
            file=sys.stderr,
        )
        return 1

    # Base image tag: follows a semver version; falls back to image.yml's
    # version when building a commit hash (Docker Hub has no <hash>-builder tag).
    if is_commit:
        base_version = str(img.get("version", ""))
        if not VERSION_RE.match(base_version):
            print(
                f"::error::image.yml version must be a semver tag such as 2.11.4; "
                f"it is the base-image fallback for commit-hash builds (got: {base_version})",
                file=sys.stderr,
            )
            return 1
    else:
        base_version = version

    platforms = ",".join(img.get("platforms") or [])

    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        print("::error::GITHUB_OUTPUT is required", file=sys.stderr)
        return 1
    with open(github_output, "a") as f:
        f.write(f"image={image}\n")
        f.write(f"version={version}\n")
        f.write(f"base_version={base_version}\n")
        f.write(f"platforms={platforms}\n")
        # Commit-hash builds are treated as unreleased; the workflow uses this
        # to skip the `latest` docker tag for them.
        f.write(f"release={str(not is_commit).lower()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
