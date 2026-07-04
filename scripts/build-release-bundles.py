#!/usr/bin/env python3
"""Build self-contained profile archives from pack-manifest.json."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

MANIFEST_FILE = "pack-manifest.json"


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe asset source path: {value}")
    return path


def load_manifest(source_root: Path) -> dict[str, object]:
    manifest_path = source_root / MANIFEST_FILE
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Pack manifest root must be an object")
    if not isinstance(data.get("pack_version"), str):
        raise ValueError("Pack manifest must define pack_version")
    if not isinstance(data.get("profiles"), list) or not isinstance(data.get("assets"), list):
        raise ValueError("Pack manifest must define profiles and assets arrays")
    return data


def filtered_manifest(manifest: dict[str, object], profile: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    profiles = manifest["profiles"]
    assets = manifest["assets"]
    if profile not in profiles:
        raise ValueError(f"Unknown profile: {profile}")

    selected: list[dict[str, object]] = []
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("profiles"), list):
            raise ValueError("Every asset must be an object with a profiles array")
        if profile in asset["profiles"]:
            copy = dict(asset)
            copy["profiles"] = [profile]
            selected.append(copy)

    bundle_manifest = dict(manifest)
    bundle_manifest["profiles"] = [profile]
    bundle_manifest["default_profile"] = profile
    bundle_manifest["assets"] = selected
    bundle_manifest["bundle_profile"] = profile
    return bundle_manifest, selected


def build_archives(source_root: Path, output_dir: Path) -> list[Path]:
    manifest = load_manifest(source_root)
    version = manifest["pack_version"]
    profiles = manifest["profiles"]
    output_dir.mkdir(parents=True, exist_ok=True)
    archives: list[Path] = []

    for profile in profiles:
        bundle_manifest, assets = filtered_manifest(manifest, profile)
        archive = output_dir / f"agent-guidelines-pack_{profile}_{version}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr(MANIFEST_FILE, json.dumps(bundle_manifest, indent=2) + "\n")
            for asset in assets:
                source = asset.get("source")
                if not isinstance(source, str):
                    raise ValueError("Every asset must define a source path")
                source_path = source_root / safe_relative_path(source)
                if not source_path.is_file():
                    raise FileNotFoundError(f"Missing release source: {source}")
                bundle.write(source_path, source)
        archives.append(archive)
        print(f"created {archive}")

    return archives


def main() -> int:
    parser = argparse.ArgumentParser(description="Build repo-seed profile ZIP archives.")
    parser.add_argument("--source", default=".", help="Repository root containing pack-manifest.json.")
    parser.add_argument("--output", default="dist", help="Output directory. Defaults to dist.")
    args = parser.parse_args()
    source_root = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    build_archives(source_root, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
