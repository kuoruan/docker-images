# caddy

Custom [Caddy](https://caddyserver.com/) image built from the official
`caddy:<version>-builder-alpine` image via [xcaddy](https://github.com/caddyserver/xcaddy).
See [Dockerfile](./Dockerfile) for the build recipe.

## Tags

- `ghcr.io/<owner>/caddy:<version>` — e.g. `2.11.4`
- `ghcr.io/<owner>/caddy:latest` — most recent build (may differ from the newest released version)
- `ghcr.io/<owner>/caddy:sha-<short>` — the 7-char short SHA of the commit that triggered the build (re-runs of the same commit overwrite this tag)

Every build is pinned to a concrete version (from [`image.yml`](./image.yml) or the workflow `version` input). It uses `caddy:<version>-builder-alpine` / `caddy:<version>-alpine` base images and pushes `<version>` + `latest` + `sha-<short>`.

## Architectures

`linux/amd64`, `linux/arm64`. Arm64 is produced by cross-compilation on an amd64
runner (`GOARCH=$TARGETARCH`, `CGO_ENABLED=0`) — no QEMU emulation is used. The
arm64 build is verified to **compile**, but is **not run-tested** in CI (runners
are amd64 only); it should be validated on an arm64 host before production use.

## Build

Trigger via GitHub Actions: **Actions → Build Image → Run workflow**,
choose `caddy`, optionally pass a concrete `version` (defaults to [`image.yml`](./image.yml)). Locally:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg BUILD_VERSION=v2.11.4 \
  --build-arg BASE_VERSION=2.11.4 \
  -t ghcr.io/<owner>/caddy:2.11.4 \
  images/caddy
```

`BUILD_VERSION` is the upstream ref xcaddy fetches (`v2.11.4`, or a commit hash);
`BASE_VERSION` is the un-prefixed version used for the base images.

## Notes

- The build uses `CGO_ENABLED=0` so it cross-compiles to arm64; all Go dependencies must be pure-Go.
- The Caddy source ref is pinned by the `BUILD_VERSION` build arg (`v2.11.4`, or a commit hash); the base images are pinned separately by `BASE_VERSION`.
