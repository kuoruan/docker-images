#!/usr/bin/env bash
# Bumps each image.yml's `version` to the latest upstream release, when the
# image declares an `update` source. Reads with yq, writes with sed (only the
# `version:` line), so blank lines and comments are preserved.
# Called by .github/workflows/update-versions.yml.

set -euo pipefail

# yq and gh are preinstalled on GitHub-hosted ubuntu runners.
shopt -s nullglob

for img in images/*/image.yml; do
  name="$(basename "$(dirname "$img")")"

  repo="$(yq '.update.github' "$img" 2>/dev/null || true)"
  if [ -z "$repo" ] || [ "$repo" = "null" ]; then
    echo "skip ${name}: no update.github configured"
    continue
  fi

  prefix="$(yq '.update.tag_prefix // ""' "$img")"
  # Tolerate a single upstream failure so other images still get bumped.
  if ! tag="$(gh release view -R "$repo" --json tagName -q .tagName)"; then
    echo "::warning::${name}: failed to fetch latest release from ${repo}, skipping"
    continue
  fi
  latest="${tag#"$prefix"}"
  cur="$(yq '.version' "$img")"

  echo "${name}: current=${cur} latest=${latest} (repo=${repo}, tag=${tag})"

  if [ "$cur" != "$latest" ]; then
    # Only rewrite the `version:` line; leave blank lines/comments untouched.
    sed -i "s|^version:.*|version: \"${latest}\"|" "$img"
    # Verify the edit actually landed (guards against silent sed mismatch).
    got="$(yq '.version' "$img")"
    if [ "$got" != "$latest" ]; then
      echo "::error::${name}: version edit failed (expected ${latest}, got ${got})"
      exit 1
    fi
    echo "${name}: bumped ${cur} -> ${latest}"
  fi
done
