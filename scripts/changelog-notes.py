#!/usr/bin/env python3
"""Print the CHANGELOG.md entry for one version, for use as release notes.

Repo-seed-only tooling: never copied into target repositories.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def entry_for(changelog: str, version: str) -> str:
    """Return the body under `## <version> - <date>`, up to the next `## ` heading."""
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"Not a MAJOR.MINOR.PATCH version: {version}")
    lines = changelog.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith(f"## {version} - ")),
        None,
    )
    if start is None:
        raise ValueError(f"CHANGELOG.md has no entry for version {version}")
    end = next((index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")), len(lines))
    body = "\n".join(lines[start + 1 : end]).strip()
    if not body:
        raise ValueError(f"CHANGELOG.md entry for version {version} is empty")
    return body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print the CHANGELOG.md entry for one version.")
    parser.add_argument("version", help="Version to print, such as 5.18.0 (no leading v).")
    parser.add_argument(
        "--changelog",
        default=str(DEFAULT_CHANGELOG),
        help="Path to the changelog. Defaults to CHANGELOG.md at the repository root.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = Path(args.changelog).expanduser().read_text(encoding="utf-8")
        print(entry_for(text, args.version))
    except (OSError, ValueError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
