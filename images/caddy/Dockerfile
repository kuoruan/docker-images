# syntax=docker/dockerfile:1

# Caddy with custom plugins, built via xcaddy.
#
# Version model (two args from the workflow):
#   BUILD_VERSION what xcaddy compiles: an upstream ref such as `v2.11.7` (the
#                image.yml version with update.tag_prefix re-applied by the
#                workflow) or a commit hash (7-40 hex chars) for unreleased
#                fixes. Defaults to `latest` for manual builds.
#   BASE_VERSION the base image tag; always a semver without the prefix. The
#                builder stage uses caddy:<x>-builder-alpine, the runtime stage
#                caddy:<x>-alpine. For a commit-hash build it falls back to
#                image.yml's version, since Docker Hub has no <hash>-based tag.
#                Defaults to the major line (2); the workflow always overrides
#                it with the resolved semver.
#
# Multi-arch without QEMU:
#   The builder stage is pinned to the build platform (--platform=$BUILDPLATFORM)
#   and cross-compiles the Caddy binary via GOARCH=$TARGETARCH (xcaddy passes
#   GOOS/GOARCH/GOARM through to go build). The runtime stage has no RUN steps,
#   so buildx pulls the target-arch base without emulation. CGO_ENABLED=0 keeps
#   the pure-Go build cross-compilable; all included plugins must stay pure-Go.

ARG BUILD_VERSION=latest
ARG BASE_VERSION=2

FROM --platform=$BUILDPLATFORM caddy:${BASE_VERSION}-builder-alpine AS builder

ARG TARGETARCH
ARG BUILD_VERSION
ARG GOPROXY=https://proxy.golang.org,direct

ENV CGO_ENABLED=0

RUN GOARCH=$TARGETARCH xcaddy build "${BUILD_VERSION}" \
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
