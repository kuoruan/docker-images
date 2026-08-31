# syntax=docker/dockerfile:1

# Caddy with custom plugins, built via xcaddy.
#
# Version model (two args from the workflow):
#   VERSION      what xcaddy compiles: a semver tag (2.11.4) or a full 40-char
#                commit hash for unreleased fixes.
#   BASE_VERSION the caddy:<x>-builder/-alpine base image tag; always a semver.
#                It follows VERSION when VERSION is a semver, and falls back to
#                image.yml's version for commit-hash builds (Docker Hub has no
#                <hash>-builder tag).
#
# Multi-arch without QEMU:
#   The builder stage is pinned to the build platform (--platform=$BUILDPLATFORM)
#   and cross-compiles the Caddy binary via GOARCH=$TARGETARCH (xcaddy passes
#   GOOS/GOARCH/GOARM through to go build). The runtime stage has no RUN steps,
#   so buildx pulls the target-arch base without emulation. CGO_ENABLED=0 keeps
#   the pure-Go build cross-compilable; all included plugins must stay pure-Go.

ARG VERSION
ARG BASE_VERSION

FROM --platform=$BUILDPLATFORM caddy:${BASE_VERSION}-builder AS builder

ARG TARGETARCH
ARG VERSION
ARG GOPROXY=https://proxy.golang.org,direct

ENV CGO_ENABLED=0

RUN GOARCH=$TARGETARCH xcaddy build "${VERSION}" \
      --with github.com/caddy-dns/cloudflare \
      --with github.com/WeidiDeng/caddy-cloudflare-ip \
      --with github.com/fvbommel/caddy-combine-ip-ranges \
      --with github.com/caddy-dns/tencentcloud \
      --with github.com/imgk/caddy-trojan \
      --with github.com/caddyserver/forwardproxy@caddy2=github.com/klzgrad/forwardproxy@naive \
      --with github.com/relvacode/caddy-oidc \
      --output /usr/bin/caddy

FROM caddy:${BASE_VERSION}-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
