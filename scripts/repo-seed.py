#!/usr/bin/env python3
"""repo-seed maintainer tooling: build, check, labels, notes. Never copied into targets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "pack" / "files" / "scripts" / "sync-docs.py"


def load_sync():
    spec = importlib.util.spec_from_file_location("sync_docs", SYNC_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_docs"] = module
    spec.loader.exec_module(module)
    return module


# build

def contained_file(root: Path, relative: str, kind: str) -> Path:
    source = root / relative
    if source.is_symlink():
        raise ValueError(f"{kind} cannot be a symbolic link: {relative}")
    resolved = source.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as ex:
        raise ValueError(f"{kind} resolves outside {root.name}: {relative}") from ex
    if not resolved.is_file():
        raise FileNotFoundError(f"Missing {kind.lower()}: {relative}")
    return resolved


def build_archive(source_root: Path, output_dir: Path) -> Path:
    pack_root = source_root / "pack"
    manifest = load_sync().load_manifest(pack_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"repo-seed-pack-{manifest.pack_version}.zip"
    files_root = pack_root / "files"
    package_sources = [(p, contained_file(pack_root, p, "Package file")) for p in manifest.package_files]
    # Generated assets share their source file, so only authored paths ship.
    asset_sources = [
        (a.path, contained_file(files_root, a.path, "Release source")) for a in manifest.assets if a.source is None
    ]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(pack_root / "manifest.json", "pack/manifest.json")
        for path, source in package_sources:
            bundle.write(source, f"pack/{path}")
        for path, source in asset_sources:
            bundle.write(source, f"pack/files/{path}")
    print(f"created {archive}")
    return archive


# check
REGISTRY_FILE = "skill-sources.json"
SCHEMA_VERSION = 1
SURFACES = (".agents/skills",)
NOTICE_FILE = "NOTICE.md"
SKILL_FILE = "SKILL.md"
ALLOWED_LICENSES = frozenset(
    {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "CC0-1.0", "Unlicense"}
)
ADAPTATIONS = frozenset({"copied", "adapted"})
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DOCUMENT_SUFFIXES = {".md"}
FORBIDDEN_NAMES = {"hooks.json", "plugin.json", "marketplace.json", ".mcp.json", "settings.json", "settings.local.json"}
FORBIDDEN_DIRECTORIES = {"hooks", ".claude-plugin", ".codex-plugin"}
NETWORK_PATTERN = re.compile(r"(?i)\b(curl|wget|invoke-webrequest|invoke-restmethod)\b")


def posix_path(value: object, context: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        errors.append(f"{context} must be a non-empty POSIX path")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        errors.append(f"{context} must be a safe relative path: {value}")
        return None
    return value


def load_json(path: Path, errors: list[str]) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        errors.append(f"{path.name}: cannot read valid JSON ({ex})")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path.name}: must be a JSON object")
        return None
    return data


def skill_files(manifest: dict, surface: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    prefix = f"{surface}/"
    assets = manifest.get("assets")
    for asset in assets if isinstance(assets, list) else []:
        path = asset.get("path") if isinstance(asset, dict) else None
        if isinstance(path, str) and path.startswith(prefix):
            name, _, relative = path[len(prefix):].partition("/")
            if relative:
                result.setdefault(name, set()).add(relative)
    return result


def check_entry(entry: object, index: int, pack_root: Path, manifest: dict, errors: list[str]) -> str | None:
    context = f"skills[{index}]"
    if not isinstance(entry, dict):
        errors.append(f"{context} must be an object")
        return None
    name = entry.get("name")
    if not isinstance(name, str) or not SKILL_NAME_PATTERN.fullmatch(name):
        errors.append(f"{context}.name must be a valid skill name")
        return None
    context = f"skill '{name}'"

    repository = entry.get("upstream_repository")
    if not isinstance(repository, str) or not repository.startswith("https://"):
        errors.append(f"{context}: upstream_repository must be an https URL")
        repository = None
    posix_path(entry.get("source_path"), f"{context}: source_path", errors)
    revision = entry.get("source_revision")
    if not isinstance(revision, str) or not REVISION_PATTERN.fullmatch(revision):
        errors.append(f"{context}: source_revision must be a full 40-character lowercase commit SHA")
        revision = None
    license_id = entry.get("license")
    if license_id not in ALLOWED_LICENSES:
        errors.append(
            f"{context}: license {license_id!r} is not an allowed redistributable license "
            f"({', '.join(sorted(ALLOWED_LICENSES))}); unlicensed or incompatible sources are rejected"
        )
        license_id = None
    posix_path(entry.get("license_evidence"), f"{context}: license_evidence", errors)
    if entry.get("adaptation") not in ADAPTATIONS:
        errors.append(f"{context}: adaptation must be one of {', '.join(sorted(ADAPTATIONS))}")
    reviewed = entry.get("reviewed")
    if not isinstance(reviewed, str) or not DATE_PATTERN.fullmatch(reviewed):
        errors.append(f"{context}: reviewed must be a YYYY-MM-DD date")
    review = entry.get("security_review")
    if not isinstance(review, str) or not review.strip():
        errors.append(f"{context}: security_review must record the review of every distributed file")

    declared_raw = entry.get("distributed_files")
    declared: set[str] = set()
    if not isinstance(declared_raw, list) or not declared_raw or len(declared_raw) != len(set(declared_raw)):
        errors.append(f"{context}: distributed_files must be a non-empty list without duplicates")
    else:
        for item in declared_raw:
            if posix_path(item, f"{context}: distributed_files entry", errors):
                declared.add(item)
    for required in (SKILL_FILE, NOTICE_FILE):
        if declared and required not in declared:
            errors.append(f"{context}: distributed_files must include {required}")

    executables = entry.get("security_reviewed_files", [])
    if not isinstance(executables, list) or not all(isinstance(item, str) for item in executables):
        errors.append(f"{context}: security_reviewed_files must be a string list")
        executables = []
    for relative in sorted(declared):
        path = PurePosixPath(relative)
        if path.name in FORBIDDEN_NAMES or FORBIDDEN_DIRECTORIES.intersection(path.parts):
            errors.append(f"{context}: {relative} is a hook, plugin, or tool-configuration file and cannot be distributed")
        if path.suffix.lower() not in DOCUMENT_SUFFIXES and relative not in executables:
            errors.append(f"{context}: non-document file {relative} must be listed in security_reviewed_files")
    for relative in executables:
        if relative not in declared:
            errors.append(f"{context}: security_reviewed_files entry {relative} is not distributed")

    for surface in SURFACES:
        actual = skill_files(manifest, surface).get(name)
        if actual is None:
            errors.append(f"{context}: not in the manifest under {surface}/")
            continue
        if declared and actual != declared:
            extra = sorted(actual - declared)
            missing = sorted(declared - actual)
            errors.append(
                f"{context}: {surface} files differ from distributed_files "
                f"(unregistered: {extra or 'none'}; missing: {missing or 'none'})"
            )
        for relative in sorted(actual):
            source = pack_root / "files" / surface / name / relative
            if not source.is_file():
                continue
            data = source.read_bytes()
            text = data.decode("utf-8", errors="replace")
            if NETWORK_PATTERN.search(text):
                errors.append(f"{context}: {surface}/{name}/{relative} contains a network fetch command")
            if relative == SKILL_FILE and "AGENTS.md" not in text:
                errors.append(f"{context}: {surface}/{name}/{SKILL_FILE} must defer to the applicable AGENTS.md")
            if relative == NOTICE_FILE:
                for needle, label in ((repository, "upstream repository"), (revision, "source revision"), (license_id, "license")):
                    if needle and needle not in text:
                        errors.append(f"{context}: {surface}/{name}/{NOTICE_FILE} does not state the {label}")
    return name


def validate(pack_root: Path) -> list[str]:
    errors: list[str] = []
    manifest = load_json(pack_root / "manifest.json", errors)
    registry = load_json(pack_root / REGISTRY_FILE, errors)
    if manifest is None or registry is None:
        return errors
    if not isinstance(manifest.get("assets"), list):
        errors.append("manifest.json: assets must be a list")
        return errors
    if registry.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{REGISTRY_FILE}: schema_version must be {SCHEMA_VERSION}")
    entries = registry.get("skills")
    if not isinstance(entries, list):
        errors.append(f"{REGISTRY_FILE}: skills must be a list")
        entries = []

    registered: set[str] = set()
    for index, entry in enumerate(entries):
        name = check_entry(entry, index, pack_root, manifest, errors)
        if name is not None:
            if name in registered:
                errors.append(f"skill '{name}': registered more than once")
            registered.add(name)

    surface_maps = {surface: skill_files(manifest, surface) for surface in SURFACES}
    for surface, skills in surface_maps.items():
        for name, files in skills.items():
            if NOTICE_FILE in files and name not in registered:
                errors.append(f"skill '{name}': ships {NOTICE_FILE} in {surface} but has no {REGISTRY_FILE} entry")
    return errors


# labels
LABEL_LIST_LIMIT = 1000
DEFAULT_CATALOG = ROOT / "pack" / "github-labels.json"
RETIRED_TYPE_REPLACEMENT = "type: feature, type: tech-debt, or type: chore"
LEGACY_LABELS = {
    "bug": "type: bug",
    "enhancement": "type: feature",
    "feature": "type: feature",
    "critical": "priority: critical",
    "high": "priority: high",
    "medium": "priority: medium",
    "low": "priority: low",
    "lowest": "priority: low",
    "type: decision": RETIRED_TYPE_REPLACEMENT,
    "type: idea": RETIRED_TYPE_REPLACEMENT,
}


def load_catalog(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Label catalog must be a JSON object")
    labels = data.get("labels")
    if not isinstance(labels, list) or not labels:
        raise ValueError("Label catalog must define a non-empty 'labels' array")
    seen: set[str] = set()
    for entry in labels:
        if not isinstance(entry, dict):
            raise ValueError("Each catalog entry must be an object")
        name = entry.get("name")
        description = entry.get("description")
        if not isinstance(name, str) or not name:
            raise ValueError("Each catalog label needs a non-empty 'name'")
        if not isinstance(description, str) or not description:
            raise ValueError(f"Label '{name}' needs a non-empty string 'description'")
        color = entry.get("color")
        if color is not None and not isinstance(color, str):
            raise ValueError(f"Label '{name}' color must be a string")
        if name in seen:
            raise ValueError(f"Duplicate label in catalog: {name}")
        seen.add(name)
    return labels


def require_gh() -> str:
    gh = shutil.which("gh")
    if gh is None:
        raise RuntimeError("The GitHub CLI ('gh') is required and was not found on PATH")
    return gh


def fetch_hosted_labels(gh: str, repo: str | None) -> list[dict]:
    command = [gh, "label", "list", "--json", "name,description,color", "--limit", str(LABEL_LIST_LIMIT)]
    if repo:
        command.extend(["--repo", repo])
    result = subprocess.run(command, capture_output=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gh label list failed: {result.stderr.strip()}")
    labels = json.loads(result.stdout)
    if len(labels) >= LABEL_LIST_LIMIT:
        raise RuntimeError(
            f"The repository has {LABEL_LIST_LIMIT} or more labels, so the list may be truncated; refusing to compare"
        )
    return labels


def run_label_mutation(command: list[str], operation: str, name: str) -> None:
    result = subprocess.run(command, capture_output=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gh label {operation} failed for '{name}': {result.stderr.strip()}")


def create_label(gh: str, repo: str | None, label: dict) -> None:
    command = [gh, "label", "create", label["name"], "--description", label.get("description", "")]
    if label.get("color"):
        command.extend(["--color", label["color"]])
    if repo:
        command.extend(["--repo", repo])
    run_label_mutation(command, "create", label["name"])


def update_label(gh: str, repo: str | None, label: dict, existing_name: str | None = None) -> None:
    command = [gh, "label", "edit", existing_name or label["name"], "--description", label.get("description", "")]
    if existing_name is not None and existing_name != label["name"]:
        command.extend(["--name", label["name"]])
    if label.get("color"):
        command.extend(["--color", label["color"]])
    if repo:
        command.extend(["--repo", repo])
    run_label_mutation(command, "edit", label["name"])


def label_differs(label: dict, existing: dict) -> bool:
    if label.get("description") and existing.get("description") != label["description"]:
        return True
    if label.get("color") and (existing.get("color") or "").lower() != label["color"].lower():
        return True
    return existing.get("name") != label["name"]


def index_by_name(hosted: list[dict]) -> dict[str, dict]:
    return {entry["name"].lower(): entry for entry in hosted}


def audit(catalog: list[dict], hosted: list[dict]) -> list[str]:
    hosted_by_name = index_by_name(hosted)
    findings: list[str] = []
    for label in catalog:
        name = label["name"]
        existing = hosted_by_name.get(name.lower())
        if existing is None:
            findings.append(f"missing: {name}")
        elif label_differs(label, existing):
            findings.append(f"drift: {name} differs from the canonical catalog")
    for legacy_name, replacement in LEGACY_LABELS.items():
        if legacy_name.lower() in hosted_by_name:
            findings.append(f"legacy label: '{legacy_name}' is still hosted (replace with '{replacement}')")
    return findings


def apply_catalog(gh: str, repo: str | None, catalog: list[dict], hosted: list[dict]) -> list[str]:
    hosted_by_name = index_by_name(hosted)
    report: list[str] = []
    for label in catalog:
        existing = hosted_by_name.get(label["name"].lower())
        if existing is None:
            create_label(gh, repo, label)
            report.append(f"created: {label['name']}")
        elif label_differs(label, existing):
            update_label(gh, repo, label, existing["name"])
            report.append(f"updated: {label['name']}")
    for legacy_name, replacement in LEGACY_LABELS.items():
        if legacy_name.lower() in hosted_by_name:
            report.append(f"legacy label present, not removed: '{legacy_name}' (replace with '{replacement}')")
    return report


# notes
DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def heading_lines(lines: list[str]) -> list[int]:
    indexes: list[int] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        marker = stripped[:3] if stripped.startswith(("```", "~~~")) else None
        if marker is not None:
            fence = None if fence == marker else (fence or marker)
        elif fence is None and line.startswith("## "):
            indexes.append(index)
    return indexes


def entry_for(changelog: str, version: str) -> str:
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"Not a MAJOR.MINOR.PATCH version: {version}")
    lines = changelog.split("\n")
    headings = heading_lines(lines)
    start = next((index for index in headings if lines[index].startswith(f"## {version} - ")), None)
    if start is None:
        raise ValueError(f"CHANGELOG.md has no entry for version {version}")
    end = next((index for index in headings if index > start), len(lines))
    body = "\n".join(lines[start + 1 : end]).strip()
    if not body:
        raise ValueError(f"CHANGELOG.md entry for version {version} is empty")
    return body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="repo-seed maintainer tooling.")
    commands = parser.add_subparsers(dest="command", required=True)

    cmd = commands.add_parser("build", help="Build the release archive.")
    cmd.add_argument("--source", default=".", help="Repository root containing pack/. Defaults to the current directory.")
    cmd.add_argument("--output", default="dist", help="Output directory. Defaults to dist.")

    cmd = commands.add_parser("check", help="Validate upstream-skill provenance and licensing.")
    cmd.add_argument("--source", default="pack", help="Pack directory. Defaults to pack.")

    cmd = commands.add_parser("labels", help="Check or apply the hosted label catalog.")
    cmd.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Label catalog JSON. Defaults to pack/github-labels.json.")
    cmd.add_argument("--repo", help="owner/repo. Defaults to the current gh repository.")
    mode = cmd.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report drift without changing labels.")
    mode.add_argument("--apply", action="store_true", help="Create missing labels and update managed fields. Never deletes.")

    cmd = commands.add_parser("notes", help="Print the CHANGELOG.md entry for one version.")
    cmd.add_argument("version", help="Version such as 5.18.0, without a leading v.")
    cmd.add_argument("--changelog", default=str(DEFAULT_CHANGELOG), help="Changelog path. Defaults to CHANGELOG.md.")
    return parser


def run_labels(args: argparse.Namespace) -> int:
    catalog = load_catalog(Path(args.catalog).expanduser().resolve())
    gh = require_gh()
    hosted = fetch_hosted_labels(gh, args.repo)
    if args.check:
        findings = audit(catalog, hosted)
        print("\n".join(findings) if findings else "no drift detected")
        return 1 if findings else 0
    for line in apply_catalog(gh, args.repo, catalog, hosted):
        print(line)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            build_archive(Path(args.source).expanduser().resolve(), Path(args.output).expanduser().resolve())
        elif args.command == "check":
            errors = validate(Path(args.source))
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            if not errors:
                print("skill sources valid")
            return 1 if errors else 0
        elif args.command == "labels":
            return run_labels(args)
        else:
            print(entry_for(Path(args.changelog).expanduser().read_text(encoding="utf-8"), args.version))
    except (OSError, ValueError, RuntimeError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
