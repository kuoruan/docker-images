#!/usr/bin/env python3
"""Local checks for the update-check hook handling in update-versions.py.

Run from anywhere:  python3 scripts/test-update-versions.py

Builds a throwaway tree with a fake `gh` on PATH, so it needs no network and
never touches the real images/. Exits non-zero if any assertion fails.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_TAG = "v9.9.9"
HOOK_TIMEOUT_UNDER_TEST = 1

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def make_image(root: Path, name: str, version: str, hook: str | None = None) -> Path:
    img = root / "images" / name
    img.mkdir(parents=True)
    (img / "image.yml").write_text(
        f"name: {name}\nversion: {version}\nplatforms:\n- linux/amd64\n"
        "update:\n  github: foo/bar\n  tag_prefix: v\n"
    )
    (img / "Dockerfile").touch()
    if hook is not None:
        (img / "update-check.sh").write_text(hook)
        (img / "update-check.sh").chmod(0o755)
    return img


def version_of(img: Path) -> str:
    for line in (img / "image.yml").read_text().splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip()
    return ""


def load_module(script: Path):
    spec = importlib.util.spec_from_file_location("update_versions", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "bin").mkdir()
        (root / "scripts").mkdir()
        shutil.copy(REPO_ROOT / "scripts" / "update-versions.py", root / "scripts")

        # Fake gh: every repo reports the same upstream tag.
        fake_gh = root / "bin" / "gh"
        fake_gh.write_text(f"#!/bin/sh\necho {UPSTREAM_TAG}\n")
        fake_gh.chmod(0o755)

        plain = make_image(root, "plain", "1.0.0")
        allowed = make_image(root, "allowed", "1.0.0", '#!/bin/sh\nprintf "%s" "$1" > hook-arg.txt\nexit 0\n')
        rejected = make_image(root, "rejected", "1.0.0", '#!/bin/sh\necho "refusing $1" >&2\nexit 1\n')
        current = make_image(root, "current", "9.9.9", '#!/bin/sh\ntouch hook-called.txt\nexit 0\n')

        env = dict(os.environ, PATH=f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}")
        env["GITHUB_OUTPUT"] = str(root / "out.txt")
        proc = subprocess.run(
            [sys.executable, "scripts/update-versions.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        changes = (root / ".changes").read_text()
        output = (root / "out.txt").read_text().strip()

        print("no hook: bumps as before")
        check("bumped to the upstream version", version_of(plain) == "9.9.9", version_of(plain))

        print("hook allows: bumps and sees the upstream tag")
        check("bumped", version_of(allowed) == "9.9.9", version_of(allowed))
        check("hook received the v-prefixed tag", (root / "hook-arg.txt").read_text() == UPSTREAM_TAG)

        print("hook rejects: pin kept, out of .changes, reason surfaced")
        check("pin unchanged", version_of(rejected) == "1.0.0", version_of(rejected))
        check("not listed in .changes", "rejected\t" not in changes)
        check("warning carries the hook's message", f"refusing {UPSTREAM_TAG}" in proc.stdout)

        print("already at the upstream version: hook not consulted")
        check("hook was not run", not (root / "hook-called.txt").exists())

        print("accounting")
        check("changed counts only the bumped images", output == "changed=2", output)
        check(
            ".changes lists exactly the bumped images",
            sorted(changes.split()) == ["9.9.9", "9.9.9", "allowed", "plain"],
            repr(changes),
        )

        # Module-level checks: exercise the hook runner directly, so a timeout
        # can be proven without waiting the production 600s.
        module = load_module(root / "scripts" / "update-versions.py")
        module.HOOK_TIMEOUT = HOOK_TIMEOUT_UNDER_TEST
        os.chdir(root)

        slow = make_image(root, "slow", "1.0.0", "#!/bin/sh\nsleep 30\n")
        print(f"hook times out ({HOOK_TIMEOUT_UNDER_TEST}s): bump vetoed, run continues")
        started = time.time()
        allowed_by_slow = module.bump_allowed("slow", UPSTREAM_TAG)
        elapsed = time.time() - started
        check("vetoed", allowed_by_slow is False)
        check("returned promptly", elapsed < 10, f"{elapsed:.1f}s")

        (slow / "update-check.sh").unlink()
        (slow / "update-check.sh").mkdir()
        print("hook path is not a regular file: vetoed, not silently allowed")
        check("vetoed", module.bump_allowed("slow", UPSTREAM_TAG) is False)

        print("unknown image with no hook: allowed")
        (root / "images" / "nohooks").mkdir()
        check("allowed", module.bump_allowed("nohooks", UPSTREAM_TAG) is True)

    print()
    if failures:
        print(f"FAILED ({len(failures)}): {', '.join(failures)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
