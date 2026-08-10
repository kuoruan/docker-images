# caddy

Custom [Caddy](https://caddyserver.com/) image built from the official `caddy:builder`
image via [xcaddy](https://github.com/caddyserver/xcaddy). See [Dockerfile](./Dockerfile)
for the build recipe.

## Tags

- `ghcr.io/<owner>/caddy:<version>` — e.g. `2.11.4`
- `ghcr.io/<owner>/caddy:latest` — most recent build (may differ from the newest released version)
- `ghcr.io/<owner>/caddy:sha-<short>` — the 7-char short SHA of the commit that triggered the build (re-runs of the same commit overwrite this tag)

Every build is pinned to a concrete version (from [`image.yml`](./image.yml) or the workflow `version` input). It uses `caddy:<version>-builder` / `caddy:<version>-alpine` base images and pushes `<version>` + `latest` + `sha-<short>`.

## Architectures

`linux/amd64`, `linux/arm64`. Arm64 is produced by cross-compilation on an amd64
runner (`GOARCH=$TARGETARCH`, `CGO_ENABLED=0`) — no QEMU emulation is used. The
arm64 build is verified to **compile**, but is **not run-tested** in CI (runners
are amd64 only); it should be validated on an arm64 host before production use.

## Build

Trigger via GitHub Actions: **Actions → Build Docker Image → Run workflow**,
choose `caddy`, optionally pass a concrete `version` (defaults to [`image.yml`](./image.yml)). Locally:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg VERSION=2.11.4 \
  -t ghcr.io/<owner>/caddy:2.11.4 \
  images/caddy
```

## Notes

- The build uses `CGO_ENABLED=0` so it cross-compiles to arm64; all Go dependencies must be pure-Go.
- The Caddy version is pinned by the `VERSION` build arg (which selects the `caddy:<version>-builder` base image, whose `CADDY_VERSION` ENV drives xcaddy).
