#!/bin/sh
# Fetch the Caddy source at the requested ref and apply the patches from the
# forwardproxy `naive` branch on top.
#
# Mirrors https://github.com/klzgrad/forwardproxy/blob/naive/.github/workflows/build.yml:
# the resulting tree is meant to replace github.com/caddyserver/caddy/v2 via
# `xcaddy build --replace <dest>`.
#
# Usage: caddy-src.sh <ref> <dest>
#   <ref>  is a tag (v2.11.7), a commit hash (short or full), or `latest`
#          (resolves to the Caddy version the naive patches currently target).
#   <dest> is the directory to put the patched source tree in (created if
#          missing, resolved to an absolute path).

set -eu

ref_arg="${1:?usage: caddy-src.sh <ref> <dest>}"
dest="${2:?usage: caddy-src.sh <ref> <dest>}"
proxy_url=https://raw.githubusercontent.com/klzgrad/forwardproxy/naive
patches="caddy-sing-quic-bbrv1.patch caddy-read-idle-timeout.patch"
# Bound the network calls so a stalled fetch cannot hang a build (or the
# Update Versions hook that runs this script) indefinitely.
# Unquoted on purpose: $wget_opts expands to several wget arguments.
wget_opts="--timeout=30 --tries=3"

if [ "$ref_arg" = "latest" ]; then
	# The patches are written for one Caddy release, so a moving ref such as
	# `master` will not apply.
	ref_arg=$(wget -q $wget_opts -O- "$proxy_url/CADDY_VERSION")
fi

mkdir -p "$dest"
dest=$(cd "$dest" && pwd)

# codeload accepts tags and both short and full commit hashes.
wget -q $wget_opts -O- "https://codeload.github.com/caddyserver/caddy/tar.gz/$ref_arg" \
	| tar xz -C "$dest" --strip-components=1

cd "$dest"
for patch in $patches; do
	if ! wget -q $wget_opts -O- "$proxy_url/$patch" | git apply -; then
		echo "caddy-src: failed to apply $patch to $ref_arg (the naive patches target one Caddy release each; see $proxy_url/CADDY_VERSION)" >&2
		exit 1
	fi
done
