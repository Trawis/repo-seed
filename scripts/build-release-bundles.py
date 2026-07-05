#!/usr/bin/env python3
"""Build one self-contained repo-seed documentation-pack archive."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

PACK_DIRECTORY = "pack"
MANIFEST_FILE = "manifest.json"
FILES_DIRECTORY = "files"
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def safe_relative_path(value: str) -> Path:
    if not value or "\\" in value:
        raise ValueError(f"Unsafe asset path: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts or ":" in path.parts[0]:
        raise ValueError(f"Unsafe asset path: {value}")
    if path.as_posix() != value:
        raise ValueError(f"Asset path must be a canonical POSIX path: {value}")
    return Path(*path.parts)


def load_manifest(pack_root: Path) -> dict[str, object]:
    manifest_path = pack_root / MANIFEST_FILE
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as ex:
        raise ValueError(f"Pack manifest does not exist: {manifest_path}") from ex
    except json.JSONDecodeError as ex:
        raise ValueError(f"Pack manifest is not valid JSON: {ex}") from ex

    if not isinstance(data, dict):
        raise ValueError("Pack manifest root must be an object")
    if data.get("schema_version") != 1:
        raise ValueError(f"Unsupported manifest schema_version: {data.get('schema_version')}")
    if not isinstance(data.get("pack_version"), str) or not SEMVER_PATTERN.fullmatch(data["pack_version"]):
        raise ValueError("Pack manifest must define a semantic pack_version")
    profiles = data.get("profiles")
    if (
        not isinstance(profiles, list)
        or not profiles
        or not all(isinstance(profile, str) and profile for profile in profiles)
        or len(profiles) != len(set(profiles))
    ):
        raise ValueError("Pack manifest must define unique profile names")
    if data.get("default_profile") not in profiles:
        raise ValueError("Pack manifest default_profile must be listed in profiles")
    if not isinstance(data.get("assets"), list) or not data["assets"]:
        raise ValueError("Pack manifest must define a non-empty assets array")

    seen_paths: set[str] = set()
    seen_scaffolds: set[str] = set()
    for index, asset in enumerate(data["assets"]):
        context = f"manifest.assets[{index}]"
        if not isinstance(asset, dict):
            raise ValueError(f"{context} must be an object")
        asset_path = asset.get("path")
        asset_type = asset.get("type")
        asset_profiles = asset.get("profiles")
        if not isinstance(asset_path, str):
            raise ValueError(f"{context}.path must be a string")
        safe_relative_path(asset_path)
        if asset_path in seen_paths:
            raise ValueError(f"Duplicate asset path: {asset_path}")
        if asset_type not in {"managed", "template"}:
            raise ValueError(f"{context}.type must be managed or template")
        if (
            not isinstance(asset_profiles, list)
            or not asset_profiles
            or not all(isinstance(profile, str) and profile in profiles for profile in asset_profiles)
        ):
            raise ValueError(f"{context}.profiles contains an invalid profile")

        scaffold_group = asset.get("scaffold_group")
        scaffold_target = asset.get("scaffold_target")
        if asset_type == "template":
            if scaffold_group not in {"project", "github"} or not isinstance(scaffold_target, str):
                raise ValueError(f"{context} must define a valid scaffold group and target")
            safe_relative_path(scaffold_target)
            if scaffold_target in seen_scaffolds:
                raise ValueError(f"Duplicate scaffold target: {scaffold_target}")
            seen_scaffolds.add(scaffold_target)
        elif scaffold_group is not None or scaffold_target is not None:
            raise ValueError(f"{context} managed assets cannot define scaffold fields")
        seen_paths.add(asset_path)
    return data


def build_archive(source_root: Path, output_dir: Path) -> Path:
    pack_root = source_root / PACK_DIRECTORY
    manifest = load_manifest(pack_root)
    version = manifest["pack_version"]
    assets = manifest["assets"]
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"repo-seed-pack-{version}.zip"

    release_sources: list[tuple[str, Path]] = []
    for asset in assets:
        asset_path = asset["path"]
        source = pack_root / FILES_DIRECTORY / safe_relative_path(asset_path)
        if not source.is_file():
            raise FileNotFoundError(f"Missing release source: {asset_path}")
        release_sources.append((asset_path, source))

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(pack_root / MANIFEST_FILE, f"{PACK_DIRECTORY}/{MANIFEST_FILE}")
        for asset_path, source in release_sources:
            bundle.write(source, f"{PACK_DIRECTORY}/{FILES_DIRECTORY}/{asset_path}")

    print(f"created {archive}")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the universal repo-seed documentation-pack ZIP.")
    parser.add_argument("--source", default=".", help="Repository root containing pack/. Defaults to the current directory.")
    parser.add_argument("--output", default="dist", help="Output directory. Defaults to dist.")
    args = parser.parse_args()

    try:
        build_archive(
            Path(args.source).expanduser().resolve(),
            Path(args.output).expanduser().resolve(),
        )
    except (OSError, ValueError) as ex:
        parser.exit(2, f"error: {ex}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
