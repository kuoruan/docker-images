# syntax=docker/dockerfile:1

# Caddy with custom plugins, built via xcaddy.
#
# Version pinning:
#   VERSION pins both the builder and runtime base images (caddy:<VERSION>-builder
#   and caddy:<VERSION>-alpine). The builder image also sets CADDY_VERSION ENV,
#   which pins the Caddy version xcaddy builds. VERSION is passed by the workflow
#   from image.yml / the version input; it has no default here on purpose so the
#   version stays a single source of truth.
#
# Multi-arch without QEMU:
#   The builder stage is pinned to the build platform (--platform=$BUILDPLATFORM)
#   and cross-compiles the Caddy binary via GOARCH=$TARGETARCH (xcaddy passes
#   GOOS/GOARCH/GOARM through to go build). The runtime stage has no RUN steps,
#   so buildx pulls the target-arch base without emulation. CGO_ENABLED=0 keeps
#   the pure-Go build cross-compilable; all included plugins must stay pure-Go.

ARG VERSION

FROM --platform=$BUILDPLATFORM caddy:${VERSION}-builder AS builder

ARG TARGETARCH
ARG GOPROXY=https://proxy.golang.org,direct

ENV CGO_ENABLED=0

# Caddy version comes from the builder image's CADDY_VERSION ENV.
RUN GOARCH=$TARGETARCH xcaddy build \
      --with github.com/caddy-dns/cloudflare \
      --with github.com/WeidiDeng/caddy-cloudflare-ip \
      --with github.com/caddy-dns/tencentcloud \
      --with github.com/imgk/caddy-trojan \
      --with github.com/caddyserver/forwardproxy@caddy2=github.com/klzgrad/forwardproxy@naive \
      --output /usr/bin/caddy

FROM caddy:${VERSION}-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
