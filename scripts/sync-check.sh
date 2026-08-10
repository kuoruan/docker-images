#!/usr/bin/env bash
# Fails if the `image` choice options in build.yml drift from the images/*/
# directories. Called by .github/workflows/sync-check.yml.

set -euo pipefail

# yq is preinstalled on GitHub-hosted ubuntu runners.
options="$(yq '.on.workflow_dispatch.inputs.image.options[]' .github/workflows/build.yml | sort)"
dirs="$(find images -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null | sort)"

echo "workflow 'image' choice options:"
echo "$options"
echo "images/*/ directories:"
echo "$dirs"

if [ "$options" != "$dirs" ]; then
  echo "::error::workflow 'image' choice options do not match images/*/ directories. Update both the choice list and the images/ directory."
  exit 1
fi
