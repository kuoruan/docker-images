#!/bin/sh
# Update Versions hook: do this image's patches still apply to upstream tag $1?
#
# The build applies patches that only target the Caddy release they were
# written for, so a newer upstream release may not patch cleanly. This applies
# them to a throwaway checkout, then exits 0 to let Update Versions bump to $1;
# any other status keeps the current pin and surfaces caddy-src.sh's message as
# the reason.
#
# It checks patch compatibility only, not that the result compiles.
#
# Usage: update-check.sh <upstream-tag>   (e.g. v2.11.7)

set -eu

tag="${1:?usage: update-check.sh <upstream-tag>}"
here=$(cd "$(dirname "$0")" && pwd)

dest=$(mktemp -d)
trap 'rm -rf "$dest"' EXIT INT TERM

"$here/caddy-src.sh" "$tag" "$dest/src"
