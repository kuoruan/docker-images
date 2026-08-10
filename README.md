# docker-images

Personal Docker images, built via GitHub Actions and published to the
[GitHub Container Registry](https://ghcr.io) under `ghcr.io/<owner>/<image>`.

Each image lives in its own directory under [`images/`](./images) with a
`Dockerfile` (the build recipe) and an `image.yml` (metadata consumed by the
build workflow). Workflow logic lives in small scripts under [`scripts/`](./scripts),
kept out of the YAML for readability and local testing.

## Images

| Image | Description |
| --- | --- |
| [`caddy`](./images/caddy) | Custom Caddy built via xcaddy |

## Build

Builds are **manually triggered**. Go to **Actions → Build Docker Image →
Run workflow**, pick an image from the dropdown, optionally pass a concrete
`version` (defaults to that image's [`image.yml`](./images/caddy/image.yml)),
and run. The build pushes to `ghcr.io/<owner>/<image>`.

Every build is pinned to a concrete version and pushes `<version>`, `latest`,
and `sha-<short>` tags. Reproducible. The workflow passes a single `VERSION`
build-arg; each image's `Dockerfile` uses it to assemble its own `FROM` lines,
so the workflow stays image-agnostic (no per-image base-tag assumptions).

A separate [`sync-check`](.github/workflows/sync-check.yml) workflow fails on
push/PR if the `image` choice list drifts from the `images/*/` directories.

## Add a new image

1. Create `images/<name>/` with `Dockerfile`, `image.yml`, and `README.md`
   (see [`images/caddy`](./images/caddy) as a template).
2. Add `<name>` to the `image` choice `options` in
   [`.github/workflows/build.yml`](./.github/workflows/build.yml).

The `sync-check` job fails the build if step 2 is skipped.

To opt a new image into the weekly version bump, add an `update:` block to its
`image.yml` (see [`images/caddy/image.yml`](./images/caddy/image.yml)):

```yaml
update:
  github: <owner>/<repo>   # latest release tag fetched from this repo
  tag_prefix: v            # strip this prefix from the tag to get the version
```

[`update-versions`](.github/workflows/update-versions.yml) rewrites each
image's `version:` line to the latest upstream release on a weekly schedule
(and manually). It only bumps the version; builds stay manual.

## Notes

- GHCR packages are created **private** by default; the `GITHUB_TOKEN` can push
  packages but cannot change their visibility, so a new package must be made
  public manually from its package settings page.
- Multi-arch images (`linux/amd64`, `linux/arm64`) are built by cross-
  compilation on an amd64 runner (no QEMU emulation). Arm64 builds are verified
  to compile, but are **not run-tested** in CI (runners are amd64 only) — they
  should be validated on an arm64 host before production use.
- The default branch is `main`. If `main` has branch protection that blocks
  direct pushes, the `update-versions` cron's auto-commit will fail; either allow
  the `GITHUB_TOKEN` to push, or switch that workflow to open a PR.
