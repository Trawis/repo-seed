#!/usr/bin/env python3
"""Mirror the authored skill tree into the Claude Code skill tree.

`pack/files/.agents/skills/` is the only place skills are edited. This tool
makes `pack/files/.claude/skills/` a byte-for-byte copy of it. It never changes
the source tree and never touches skill content.

Repo-seed-only tooling: never copied into target repositories.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PACK_FILES = Path(__file__).resolve().parents[1] / "pack" / "files"
SOURCE_SURFACE = Path(".agents/skills")
MIRROR_SURFACE = Path(".claude/skills")


@dataclass
class Drift:
    missing: list[str] = field(default_factory=list)
    different: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    empty_dirs: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.missing or self.different or self.stale or self.empty_dirs)

    def lines(self) -> list[str]:
        return (
            [f"missing: {path}" for path in self.missing]
            + [f"different: {path}" for path in self.different]
            + [f"stale: {path}" for path in self.stale]
            + [f"empty directory: {path}" for path in self.empty_dirs]
        )


def tree_files(root: Path) -> dict[str, Path]:
    """Map POSIX relative path -> file for every file under root. Symlinks are rejected."""
    files: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported in skill trees: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def reject_symlinked_root(pack_files: Path, mirror_root: Path) -> None:
    """Refuse to write through a symlink at the mirror root or any parent below pack_files."""
    current = mirror_root
    while current != pack_files and current != current.parent:
        if current.is_symlink():
            raise ValueError(f"Mirror path cannot be a symbolic link: {current}")
        current = current.parent


def empty_directories(root: Path) -> list[str]:
    """Directories under root that hold no files at any depth, as POSIX relative paths."""
    if not root.is_dir():
        return []
    return sorted(
        directory.relative_to(root).as_posix()
        for directory in root.rglob("*")
        if directory.is_dir() and not any(child.is_file() for child in directory.rglob("*"))
    )


def find_drift(source_root: Path, mirror_root: Path) -> Drift:
    if not source_root.is_dir():
        raise ValueError(f"Source skill tree not found: {source_root}")
    source = tree_files(source_root)
    mirror = tree_files(mirror_root) if mirror_root.is_dir() else {}
    drift = Drift()
    for relative, path in source.items():
        if relative not in mirror:
            drift.missing.append(relative)
        elif path.read_bytes() != mirror[relative].read_bytes():
            drift.different.append(relative)
    drift.stale = sorted(set(mirror) - set(source))
    drift.empty_dirs = empty_directories(mirror_root)
    return drift


def remove_empty_directories(mirror_root: Path) -> None:
    """Remove directories left empty, deepest first."""
    for directory in sorted((p for p in mirror_root.rglob("*") if p.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()


def apply_mirror(source_root: Path, mirror_root: Path, drift: Drift) -> None:
    # Delete before copying so a path that differs only by case on a
    # case-insensitive filesystem is removed first and then recreated.
    for relative in drift.stale:
        (mirror_root / relative).unlink()
    remove_empty_directories(mirror_root)
    for relative in drift.missing + drift.different:
        target = mirror_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mirror pack/files/.agents/skills into pack/files/.claude/skills."
    )
    parser.add_argument(
        "--pack-files",
        default=str(DEFAULT_PACK_FILES),
        help="Directory that contains .agents/skills and .claude/skills. Defaults to pack/files.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report drift and change nothing.")
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Make the Claude tree match the authored tree. Overwrites and removes files in the Claude tree only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pack_files = Path(args.pack_files).expanduser().resolve()
    source_root = pack_files / SOURCE_SURFACE
    mirror_root = pack_files / MIRROR_SURFACE

    try:
        reject_symlinked_root(pack_files, mirror_root)
        drift = find_drift(source_root, mirror_root)
        for line in drift.lines():
            print(line)
        if args.check:
            if drift:
                print(f"{MIRROR_SURFACE} is out of date; run with --apply", file=sys.stderr)
                return 1
            print("skill trees match")
            return 0
        if drift:
            apply_mirror(source_root, mirror_root, drift)
        else:
            print("skill trees already match")
    except (OSError, ValueError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
