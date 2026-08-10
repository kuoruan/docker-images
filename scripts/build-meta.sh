#!/usr/bin/env bash
# Helpers for the build workflow: validate an image directory and resolve its
# version. Called by .github/workflows/build.yml.
#
# Usage:
#   IMAGE=<name> [VERSION_INPUT=<ver>] ./scripts/build-meta.sh validate
#   IMAGE=<name> [VERSION_INPUT=<ver>] ./scripts/build-meta.sh resolve
#
# `resolve` writes `version` and `platforms` to $GITHUB_OUTPUT.

set -euo pipefail

# yq is preinstalled on GitHub-hosted ubuntu runners.
IMAGE="${IMAGE:?IMAGE is required}"
IMG="images/${IMAGE}/image.yml"

cmd="${1:?subcommand required: validate | resolve}"

case "$cmd" in
  validate)
    for f in "images/${IMAGE}" "images/${IMAGE}/Dockerfile" "$IMG"; do
      if [ ! -e "$f" ]; then
        echo "::error::${f} not found"
        exit 1
      fi
    done
    ;;

  resolve)
    image_version="$(yq '.version' "$IMG")"
    # Workflow input overrides image.yml.
    if [ -n "${VERSION_INPUT:-}" ]; then
      version="$VERSION_INPUT"
    else
      version="$image_version"
    fi
    # Always a concrete, pinned tag (no floating mode).
    if ! printf '%s' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$'; then
      echo "::error::Version must be a concrete tag such as 2.11.4 (got: ${version})"
      exit 1
    fi
    platforms="$(yq '.platforms | join(",")' "$IMG")"
    {
      echo "version=${version}"
      echo "platforms=${platforms}"
    } >> "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"
    ;;

  *)
    echo "unknown subcommand: $cmd" >&2
    exit 1
    ;;
esac
