#!/usr/bin/env python3
"""Synchronize a repo-seed profile into a target repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_NAME = "sync-agent-guidelines"
SCRIPT_VERSION = "2.0.0"
PACK_MANIFEST_FILE = "pack-manifest.json"
STATE_FILE = ".agent-guidelines-manifest.json"
CONFLICT_DIR = ".agent-guidelines-conflicts"
TEMPLATE_METADATA_START = "<!-- repo-seed-template:start -->"
TEMPLATE_METADATA_END = "<!-- repo-seed-template:end -->"
PROVENANCE_PATTERN = re.compile(
    r'<!-- repo-seed-template id="(?P<id>[^"]+)" sha256="(?P<hash>[0-9a-f]{64})" -->'
)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PROJECT_OWNED_ROOT_PATHS = {"README.md", "CHANGELOG.md", "FEATURES.md", "ROADMAP.md"}
VALID_ROLES = {"managed", "template"}
VALID_SCAFFOLD_GROUPS = {"project", "github"}


@dataclass(frozen=True)
class Asset:
    asset_id: str
    source: str
    target: str
    role: str
    profiles: tuple[str, ...]
    scaffold_group: str | None = None
    scaffold_target: str | None = None
    legacy_targets: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackManifest:
    schema_version: int
    pack_version: str
    default_profile: str
    profiles: tuple[str, ...]
    assets: tuple[Asset, ...]


@dataclass(frozen=True)
class SyncAction:
    relative_path: str
    action: str
    reason: str


def validate_relative_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if not relative_path or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe relative path: {relative_path}")
    return path


def require_string(data: dict[str, object], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def require_string_list(data: dict[str, object], key: str, context: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context}.{key} must be a non-empty string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{context}.{key} contains duplicates")
    return tuple(value)


def load_pack_manifest(source_root: Path, validate_sources: bool = True) -> PackManifest:
    manifest_path = source_root / PACK_MANIFEST_FILE
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as ex:
        raise ValueError(f"Pack manifest does not exist: {manifest_path}") from ex
    except json.JSONDecodeError as ex:
        raise ValueError(f"Pack manifest is not valid JSON: {ex}") from ex

    if not isinstance(raw, dict):
        raise ValueError("Pack manifest root must be an object")

    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise ValueError(f"Unsupported pack manifest schema_version: {schema_version}")

    pack_version = require_string(raw, "pack_version", "manifest")
    if not SEMVER_PATTERN.fullmatch(pack_version):
        raise ValueError("manifest.pack_version must use MAJOR.MINOR.PATCH")

    profiles = require_string_list(raw, "profiles", "manifest")
    default_profile = require_string(raw, "default_profile", "manifest")
    if default_profile not in profiles:
        raise ValueError("manifest.default_profile must be listed in manifest.profiles")

    raw_assets = raw.get("assets")
    if not isinstance(raw_assets, list) or not raw_assets:
        raise ValueError("manifest.assets must be a non-empty array")

    assets: list[Asset] = []
    asset_ids: set[str] = set()
    targets: set[str] = set()
    profile_set = set(profiles)

    for index, item in enumerate(raw_assets):
        context = f"manifest.assets[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{context} must be an object")

        asset_id = require_string(item, "id", context)
        source = require_string(item, "source", context)
        target = require_string(item, "target", context)
        role = require_string(item, "role", context)
        asset_profiles = require_string_list(item, "profiles", context)
        scaffold_group = item.get("scaffold_group")
        scaffold_target = item.get("scaffold_target")
        legacy_targets_value = item.get("legacy_targets", [])

        validate_relative_path(source)
        validate_relative_path(target)

        if asset_id in asset_ids:
            raise ValueError(f"Duplicate asset id: {asset_id}")
        if target in targets:
            raise ValueError(f"Duplicate managed target: {target}")
        if role not in VALID_ROLES:
            raise ValueError(f"{context}.role must be one of: {', '.join(sorted(VALID_ROLES))}")
        if not set(asset_profiles).issubset(profile_set):
            raise ValueError(f"{context}.profiles contains an unknown profile")
        if not isinstance(legacy_targets_value, list) or not all(isinstance(path, str) for path in legacy_targets_value):
            raise ValueError(f"{context}.legacy_targets must be a string array")

        legacy_targets = tuple(legacy_targets_value)
        for legacy_target in legacy_targets:
            validate_relative_path(legacy_target)

        if role == "template":
            if scaffold_group not in VALID_SCAFFOLD_GROUPS:
                raise ValueError(f"{context}.scaffold_group must be project or github")
            if not isinstance(scaffold_target, str) or not scaffold_target:
                raise ValueError(f"{context}.scaffold_target must be a non-empty string")
            validate_relative_path(scaffold_target)
        elif scaffold_group is not None or scaffold_target is not None:
            raise ValueError(f"{context} managed assets cannot define scaffold fields")

        if validate_sources:
            source_path = source_root / source
            if not source_path.is_file():
                raise ValueError(f"Asset source does not exist: {source}")
            if role == "template":
                template_body(source_path)

        asset_ids.add(asset_id)
        targets.add(target)
        assets.append(
            Asset(
                asset_id=asset_id,
                source=source,
                target=target,
                role=role,
                profiles=asset_profiles,
                scaffold_group=scaffold_group if isinstance(scaffold_group, str) else None,
                scaffold_target=scaffold_target if isinstance(scaffold_target, str) else None,
                legacy_targets=legacy_targets,
            )
        )

    return PackManifest(
        schema_version=schema_version,
        pack_version=pack_version,
        default_profile=default_profile,
        profiles=profiles,
        assets=tuple(assets),
    )


def assets_for_profile(manifest: PackManifest, profile: str) -> list[Asset]:
    if profile not in manifest.profiles:
        raise ValueError(f"Unknown profile '{profile}'. Choices: {', '.join(manifest.profiles)}")
    return [asset for asset in manifest.assets if profile in asset.profiles]


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def template_body(source: Path) -> str:
    content = source.read_text(encoding="utf-8")
    start = content.find(TEMPLATE_METADATA_START)
    end = content.find(TEMPLATE_METADATA_END)
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"Template metadata markers are missing or invalid: {source}")
    end += len(TEMPLATE_METADATA_END)
    before = content[:start].rstrip()
    after = content[end:].lstrip()
    return f"{before}\n\n{after}" if before else after


def render_template(asset: Asset, source: Path) -> str:
    body = template_body(source).rstrip()
    provenance = f'<!-- repo-seed-template id="{asset.asset_id}" sha256="{content_hash(body)}" -->'
    return f"{body}\n\n{provenance}\n"


def read_state(target_root: Path) -> dict[str, str]:
    state_path = target_root / STATE_FILE
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise ValueError(f"Target state manifest is not valid JSON: {ex}") from ex
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise ValueError("Target state manifest must contain a files object")
    files = data["files"]
    if not all(isinstance(path, str) and isinstance(hash_value, str) for path, hash_value in files.items()):
        raise ValueError("Target state manifest files must map paths to hashes")
    return dict(files)


def write_state(
    target_root: Path,
    manifest: PackManifest,
    profile: str,
    hashes: dict[str, str],
    dry_run: bool,
) -> SyncAction:
    state_path = target_root / STATE_FILE
    payload = {
        "schema_version": 2,
        "pack_version": manifest.pack_version,
        "profile": profile,
        "sync_script": f"{SCRIPT_NAME}.py",
        "sync_script_version": SCRIPT_VERSION,
        "files": dict(sorted(hashes.items())),
    }
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if state_path.exists() and state_path.read_text(encoding="utf-8") == content:
        return SyncAction(STATE_FILE, "unchanged", "state manifest already current")
    if dry_run:
        return SyncAction(STATE_FILE, "dry-run", "would update managed-file state")
    state_path.write_text(content, encoding="utf-8")
    return SyncAction(STATE_FILE, "copied", "managed-file state written")


def conflict_filename(relative_path: str) -> str:
    safe_path = relative_path.replace("/", "__").replace("\\", "__")
    return f"{SCRIPT_NAME}_{SCRIPT_VERSION}_incoming_{safe_path}"


def write_conflict(source: Path, target_root: Path, relative_path: str, dry_run: bool) -> SyncAction:
    conflict_path = target_root / CONFLICT_DIR / conflict_filename(relative_path)
    if dry_run:
        return SyncAction(relative_path, "conflict", f"would write incoming file to {conflict_path.relative_to(target_root)}")
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, conflict_path)
    return SyncAction(relative_path, "conflict", f"kept local file; incoming file written to {conflict_path.relative_to(target_root)}")


def sync_asset(
    source_root: Path,
    target_root: Path,
    asset: Asset,
    previous_hashes: dict[str, str],
    new_hashes: dict[str, str],
    dry_run: bool,
) -> SyncAction:
    source = source_root / validate_relative_path(asset.source)
    target = target_root / validate_relative_path(asset.target)
    source_hash = file_hash(source)

    if not target.exists():
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        new_hashes[asset.target] = source_hash
        return SyncAction(asset.target, "dry-run" if dry_run else "copied", "would create" if dry_run else "created")

    if not target.is_file():
        return SyncAction(asset.target, "conflict", "managed target exists but is not a file")

    target_hash = file_hash(target)
    if target_hash == source_hash:
        new_hashes[asset.target] = source_hash
        return SyncAction(asset.target, "unchanged", "target already matches source")

    previous_hash = previous_hashes.get(asset.target)
    if previous_hash is None or target_hash != previous_hash:
        return write_conflict(source, target_root, asset.target, dry_run)

    if not dry_run:
        shutil.copy2(source, target)
    new_hashes[asset.target] = source_hash
    return SyncAction(asset.target, "dry-run" if dry_run else "copied", "would update" if dry_run else "updated")


def scaffold_asset(source_root: Path, target_root: Path, asset: Asset, dry_run: bool) -> SyncAction:
    if asset.scaffold_target is None:
        raise ValueError(f"Template asset has no scaffold target: {asset.asset_id}")
    source = source_root / validate_relative_path(asset.source)
    target = target_root / validate_relative_path(asset.scaffold_target)
    try:
        content = render_template(asset, source)
    except (OSError, UnicodeError, ValueError) as ex:
        return SyncAction(asset.scaffold_target, "invalid-template", str(ex))
    if target.exists():
        return SyncAction(asset.scaffold_target, "skipped", "project-owned file already exists")
    if dry_run:
        return SyncAction(asset.scaffold_target, "dry-run", "would scaffold missing project-owned file")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return SyncAction(asset.scaffold_target, "scaffolded", "created project-owned file")


def template_drift_action(source_root: Path, target_root: Path, asset: Asset) -> SyncAction | None:
    if asset.scaffold_target is None:
        return None
    target = target_root / validate_relative_path(asset.scaffold_target)
    if not target.is_file():
        return None
    try:
        content = target.read_text(encoding="utf-8")
        current_hash = content_hash(template_body(source_root / asset.source).rstrip())
    except (OSError, UnicodeError, ValueError):
        return None
    matches = [match for match in PROVENANCE_PATTERN.finditer(content) if match.group("id") == asset.asset_id]
    if not matches or matches[-1].group("hash") == current_hash:
        return None
    marker = f'<!-- repo-seed-template id="{asset.asset_id}" sha256="{current_hash}" -->'
    return SyncAction(
        asset.scaffold_target,
        "review-needed",
        f"template changed; review the live document, then replace its provenance marker with {marker}",
    )


def prune_obsolete_files(
    target_root: Path,
    previous_hashes: dict[str, str],
    selected_targets: set[str],
    dry_run: bool,
) -> list[SyncAction]:
    actions: list[SyncAction] = []
    for relative_path in sorted(previous_hashes.keys() - selected_targets):
        target = target_root / validate_relative_path(relative_path)
        if not target.exists():
            actions.append(SyncAction(relative_path, "absent", "obsolete managed file already absent"))
        elif relative_path in PROJECT_OWNED_ROOT_PATHS:
            actions.append(SyncAction(relative_path, "preserved", "root project document is protected"))
        elif not target.is_file() or file_hash(target) != previous_hashes[relative_path]:
            actions.append(SyncAction(relative_path, "preserved", "obsolete managed path has local changes"))
        elif dry_run:
            actions.append(SyncAction(relative_path, "dry-run", "would remove obsolete managed file"))
        else:
            target.unlink()
            actions.append(SyncAction(relative_path, "removed", "obsolete managed file removed"))
    return actions


def run_git(target_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=target_root,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def is_git_repo(target_root: Path) -> bool:
    result = run_git(target_root, "rev-parse", "--is-inside-work-tree", check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def branch_exists(target_root: Path, branch_name: str) -> bool:
    return run_git(target_root, "show-ref", "--verify", f"refs/heads/{branch_name}", check=False).returncode == 0


def remote_branch_exists(target_root: Path, branch_name: str) -> bool:
    return run_git(target_root, "show-ref", "--verify", f"refs/remotes/origin/{branch_name}", check=False).returncode == 0


def switch_branch(target_root: Path, branch_name: str) -> None:
    run_git(target_root, "switch", branch_name)


def create_branch(target_root: Path, branch_name: str, start_point: str) -> None:
    run_git(target_root, "switch", "-c", branch_name, start_point)


def ensure_base_branch(target_root: Path, base_branch: str) -> list[str]:
    if branch_exists(target_root, base_branch):
        switch_branch(target_root, base_branch)
        return [f"checked out existing base branch {base_branch}"]
    if remote_branch_exists(target_root, base_branch):
        create_branch(target_root, base_branch, f"origin/{base_branch}")
        return [f"created local {base_branch} from origin/{base_branch}"]
    create_branch(target_root, base_branch, "HEAD")
    return [f"created {base_branch} from current HEAD because no local or origin branch was found"]


def prepare_branch(
    target_root: Path,
    branch_name: str,
    base_branch: str,
    dry_run: bool,
    no_branch: bool,
    skip_fetch: bool,
) -> list[str]:
    if no_branch:
        return ["branch creation skipped because --no-branch was used"]
    if not is_git_repo(target_root):
        raise RuntimeError("Target is not a Git repository. Initialize Git or use --no-branch explicitly.")
    status = run_git(target_root, "status", "--porcelain").stdout.strip()
    if status:
        raise RuntimeError(f"Target working tree has uncommitted changes:\n{status}")
    if dry_run:
        fetch_text = "" if skip_fetch else "fetch/prune remotes, then "
        return [f"dry-run: would {fetch_text}create or reuse branch {branch_name} from {base_branch}"]

    messages: list[str] = []
    if not skip_fetch:
        result = run_git(target_root, "fetch", "--all", "--prune", check=False)
        if result.returncode == 0:
            messages.append("fetched/pruned remotes")
        else:
            message = result.stderr.strip() or result.stdout.strip() or "git fetch failed"
            messages.append(f"remote fetch/prune failed: {message}")
    messages.extend(ensure_base_branch(target_root, base_branch))
    if branch_exists(target_root, branch_name):
        switch_branch(target_root, branch_name)
        messages.append(f"checked out existing task branch {branch_name}")
    else:
        create_branch(target_root, branch_name, base_branch)
        messages.append(f"created task branch {branch_name} from {base_branch}")
    return messages


def default_source_root() -> Path:
    script_path = Path(__file__).resolve()
    return script_path.parent.parent if script_path.parent.name == "scripts" else Path.cwd()


def resolve_root(value: str | None, fallback: Path) -> Path:
    return Path(value).expanduser().resolve() if value else fallback.expanduser().resolve()


def version_branch_name(pack_version: str) -> str:
    return f"feature/sync-agent-guidelines-{pack_version.replace('.', '-')}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync a repo-seed documentation and agent-guidance profile.")
    parser.add_argument("--source", help="Path to repo-seed or an extracted profile bundle.")
    parser.add_argument("--target", default=".", help="Target repository root. Defaults to the current directory.")
    parser.add_argument("--profile", help="Profile from pack-manifest.json. Defaults to its default_profile.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without switching branches or writing files.")
    parser.add_argument("--branch-name", help="Task branch. Defaults to feature/sync-agent-guidelines-<version>.")
    parser.add_argument("--base-branch", default="main", help="Base branch for the sync branch. Defaults to main.")
    parser.add_argument("--no-branch", action="store_true", help="Do not create or switch branches.")
    parser.add_argument("--skip-fetch", action="store_true", help="Do not fetch/prune remotes before branch preparation.")
    parser.add_argument("--scaffold-project-files", action="store_true", help="Create missing project-owned files for the selected profile.")
    parser.add_argument("--include-project-docs", action="store_true", help="Deprecated alias for --scaffold-project-files.")
    parser.add_argument("--scaffold-github-templates", action="store_true", help="Create missing generic GitHub issue templates.")
    parser.add_argument("--skip-editorconfig", action="store_true", help="Do not sync .editorconfig.")
    parser.add_argument("--exclude", action="append", default=[], help="Managed or scaffold target to exclude. May be repeated.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_root = resolve_root(args.source, default_source_root())
    target_root = resolve_root(args.target, Path.cwd())
    if source_root == target_root:
        print("Source and target are the same directory; nothing to sync.", file=sys.stderr)
        return 2
    if not source_root.is_dir() or not target_root.is_dir():
        print("Source and target must both be existing directories.", file=sys.stderr)
        return 2

    try:
        manifest = load_pack_manifest(source_root)
        profile = args.profile or manifest.default_profile
        profile_assets = assets_for_profile(manifest, profile)
        previous_hashes = read_state(target_root)
    except (OSError, UnicodeError, ValueError) as ex:
        print(f"Validation failed: {ex}", file=sys.stderr)
        return 2

    branch_name = args.branch_name or version_branch_name(manifest.pack_version)
    try:
        branch_messages = prepare_branch(
            target_root,
            branch_name,
            args.base_branch,
            args.dry_run,
            args.no_branch,
            args.skip_fetch,
        )
    except (RuntimeError, subprocess.CalledProcessError) as ex:
        print(f"Branch preparation failed: {ex}", file=sys.stderr)
        return 2

    for message in branch_messages:
        print(f"branch         {message}")

    excluded = set(args.exclude)
    if args.skip_editorconfig:
        excluded.add(".editorconfig")
    selected = [asset for asset in profile_assets if asset.target not in excluded]
    profile_targets = {asset.target for asset in profile_assets}
    new_hashes = {
        path: hash_value
        for path, hash_value in previous_hashes.items()
        if path in profile_targets
    }

    print(f"profile        {profile} ({len(selected)} managed files selected)")
    actions: list[SyncAction] = []
    for asset in selected:
        actions.append(sync_asset(source_root, target_root, asset, previous_hashes, new_hashes, args.dry_run))

    scaffold_project = args.scaffold_project_files or args.include_project_docs
    if args.include_project_docs:
        print("warning        --include-project-docs is deprecated; use --scaffold-project-files")

    scaffold_groups: set[str] = set()
    if scaffold_project:
        scaffold_groups.add("project")
    if args.scaffold_github_templates:
        scaffold_groups.add("github")

    for asset in selected:
        if asset.role == "template" and asset.scaffold_group in scaffold_groups and asset.scaffold_target not in excluded:
            actions.append(scaffold_asset(source_root, target_root, asset, args.dry_run))

    for asset in selected:
        if asset.role == "template" and asset.scaffold_group == "project":
            drift = template_drift_action(source_root, target_root, asset)
            if drift is not None:
                actions.append(drift)

    actions.extend(prune_obsolete_files(target_root, previous_hashes, profile_targets, args.dry_run))
    actions.append(write_state(target_root, manifest, profile, new_hashes, args.dry_run))

    changed = 0
    conflicts = 0
    invalid_templates = 0
    review_needed = 0
    for action in actions:
        print(f"{action.action:14} {action.relative_path} - {action.reason}")
        if action.action in {"copied", "scaffolded", "removed", "dry-run"}:
            changed += 1
        elif action.action == "conflict":
            conflicts += 1
        elif action.action == "invalid-template":
            invalid_templates += 1
        elif action.action == "review-needed":
            review_needed += 1

    mode = "Dry run" if args.dry_run else "Sync"
    print(
        f"\n{mode} complete. Changes: {changed}. Conflicts: {conflicts}. "
        f"Invalid templates: {invalid_templates}. Template reviews: {review_needed}."
    )
    if conflicts:
        location = "would be written under" if args.dry_run else "were written under"
        print(f"Conflict files {location} {CONFLICT_DIR}/.")
    if not args.dry_run:
        print(f"Current/intended branch: {branch_name}")
        print(f"Next steps: review the diff, run relevant checks, commit, push, and open a PR to {args.base_branch}.")
    return 1 if conflicts or invalid_templates else 0


if __name__ == "__main__":
    raise SystemExit(main())
