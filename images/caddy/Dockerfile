# syntax=docker/dockerfile:1

# Caddy with custom plugins, built via xcaddy.
#
# BUILD_VERSION  upstream ref to compile: a tag like v2.11.7 (image.yml's version
#                with update.tag_prefix re-applied by the workflow), a commit
#                hash, or `latest` for manual builds.
# BASE_VERSION   semver without the prefix, used for both caddy:<x>-builder-alpine
#                and caddy:<x>-alpine. Commit-hash builds fall back to image.yml's
#                version, because Docker Hub has no <hash>-based tags.

ARG BUILD_VERSION=latest
ARG BASE_VERSION=2

FROM --platform=$BUILDPLATFORM caddy:${BASE_VERSION}-builder-alpine AS builder

ARG TARGETARCH
ARG BUILD_VERSION
ARG GOPROXY=https://proxy.golang.org,direct

ENV CGO_ENABLED=0

# Fetch the Caddy source and apply the forwardproxy naive patches (sing-quic
# BBRv1, read-idle-timeout). The patched tree replaces caddy/v2 in the build
# below.
COPY --chmod=755 caddy-src.sh /usr/local/bin/caddy-src
RUN caddy-src "${BUILD_VERSION}" /src/caddy

RUN GOARCH=$TARGETARCH xcaddy build "${BUILD_VERSION}" \
      --replace github.com/caddyserver/caddy/v2=/src/caddy \
      --with github.com/caddy-dns/cloudflare \
      --with github.com/WeidiDeng/caddy-cloudflare-ip \
      --with github.com/fvbommel/caddy-combine-ip-ranges \
      --with github.com/caddy-dns/tencentcloud \
      --with github.com/imgk/caddy-trojan \
      --with github.com/caddyserver/forwardproxy@caddy2=github.com/klzgrad/forwardproxy@naive \
      --with github.com/relvacode/caddy-oidc \
      --with github.com/kuoruan/caddy-forwarded-host \
      --output /usr/bin/caddy

FROM caddy:${BASE_VERSION}-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
