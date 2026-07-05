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
VALID_SCAFFOLD_GROUPS = {"project", "github", "editorconfig"}
TEMPLATE_METADATA_START = "repo-seed-template:start"
TEMPLATE_METADATA_END = "repo-seed-template:end"


def safe_relative_path(value: str) -> Path:
    if not value or "\\" in value:
        raise ValueError(f"Unsafe asset path: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts or ":" in path.parts[0]:
        raise ValueError(f"Unsafe asset path: {value}")
    if path.as_posix() != value:
        raise ValueError(f"Asset path must be a canonical POSIX path: {value}")
    return Path(*path.parts)


def require_string_list(value: object, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context} must be a non-empty string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{context} contains duplicates")
    return tuple(value)


def optional_string_list(value: object, context: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context} must be a string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{context} contains duplicates")
    return tuple(value)


def load_manifest(pack_root: Path) -> dict[str, object]:
    manifest_path = pack_root / MANIFEST_FILE
    if manifest_path.is_symlink():
        raise ValueError("Pack manifest cannot be a symbolic link")
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

    profiles = require_string_list(data.get("profiles"), "manifest.profiles")
    if data.get("default_profile") not in profiles:
        raise ValueError("Pack manifest default_profile must be listed in profiles")

    package_files = optional_string_list(data.get("package_files"), "manifest.package_files")
    for index, package_file in enumerate(package_files):
        package_path = safe_relative_path(package_file)
        if package_file == MANIFEST_FILE or package_path.parts[0] == FILES_DIRECTORY:
            raise ValueError(
                f"manifest.package_files[{index}] must not replace manifest.json or use files/"
            )

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
        if not isinstance(asset_path, str):
            raise ValueError(f"{context}.path must be a string")
        safe_relative_path(asset_path)
        if asset_path in seen_paths:
            raise ValueError(f"Duplicate asset path: {asset_path}")
        if asset_type not in {"managed", "template"}:
            raise ValueError(f"{context}.type must be managed or template")

        asset_profiles = require_string_list(asset.get("profiles"), f"{context}.profiles")
        if not set(asset_profiles).issubset(profiles):
            raise ValueError(f"{context}.profiles contains an invalid profile")

        scaffold_group = asset.get("scaffold_group")
        scaffold_target = asset.get("scaffold_target")
        if asset_type == "template":
            if scaffold_group not in VALID_SCAFFOLD_GROUPS or not isinstance(scaffold_target, str):
                raise ValueError(f"{context} must define a valid scaffold group and target")
            safe_relative_path(scaffold_target)
            if not asset_path.startswith("docs/templates/"):
                raise ValueError(f"{context}.path must be under docs/templates")
            if scaffold_target in seen_scaffolds:
                raise ValueError(f"Duplicate scaffold target: {scaffold_target}")
            seen_scaffolds.add(scaffold_target)
        elif scaffold_group is not None or scaffold_target is not None:
            raise ValueError(f"{context} managed assets cannot define scaffold fields")
        seen_paths.add(asset_path)

    collisions = seen_paths.intersection(seen_scaffolds)
    if collisions:
        raise ValueError(f"Scaffold targets collide with managed paths: {', '.join(sorted(collisions))}")
    return data


def release_source(pack_root: Path, asset_path: str) -> Path:
    files_directory = pack_root / FILES_DIRECTORY
    if files_directory.is_symlink():
        raise ValueError("Pack files directory cannot be a symbolic link")
    files_root = files_directory.resolve()
    source = pack_root / FILES_DIRECTORY / safe_relative_path(asset_path)
    if source.is_symlink():
        raise ValueError(f"Release source cannot be a symbolic link: {asset_path}")
    resolved = source.resolve()
    try:
        resolved.relative_to(files_root)
    except ValueError as ex:
        raise ValueError(f"Release source resolves outside pack/files: {asset_path}") from ex
    if not resolved.is_file():
        raise FileNotFoundError(f"Missing release source: {asset_path}")
    return resolved


def package_source(pack_root: Path, package_path: str) -> Path:
    root = pack_root.resolve()
    source = pack_root / safe_relative_path(package_path)
    if source.is_symlink():
        raise ValueError(f"Package file cannot be a symbolic link: {package_path}")
    resolved = source.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as ex:
        raise ValueError(f"Package file resolves outside pack: {package_path}") from ex
    if not resolved.is_file():
        raise FileNotFoundError(f"Missing package file: {package_path}")
    return resolved


def validate_template_source(source: Path, asset_path: str) -> None:
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if TEMPLATE_METADATA_START in line]
    ends = [index for index, line in enumerate(lines) if TEMPLATE_METADATA_END in line]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ValueError(f"Template metadata markers are missing or invalid: {asset_path}")
    body = "".join(lines[: starts[0]] + lines[ends[0] + 1 :]).strip()
    if not body:
        raise ValueError(f"Template body is empty: {asset_path}")


def build_archive(source_root: Path, output_dir: Path) -> Path:
    pack_root = source_root / PACK_DIRECTORY
    manifest = load_manifest(pack_root)
    version = manifest["pack_version"]
    package_files = optional_string_list(manifest.get("package_files"), "manifest.package_files")
    assets = manifest["assets"]
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"repo-seed-pack-{version}.zip"

    release_sources: list[tuple[str, Path]] = []
    package_sources = [
        (package_path, package_source(pack_root, package_path))
        for package_path in package_files
    ]
    for asset in assets:
        asset_path = asset["path"]
        source = release_source(pack_root, asset_path)
        if asset["type"] == "template":
            validate_template_source(source, asset_path)
        release_sources.append((asset_path, source))

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(pack_root / MANIFEST_FILE, f"{PACK_DIRECTORY}/{MANIFEST_FILE}")
        for package_path, source in package_sources:
            bundle.write(source, f"{PACK_DIRECTORY}/{package_path}")
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
