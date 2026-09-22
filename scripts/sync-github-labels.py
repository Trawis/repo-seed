#!/usr/bin/env python3
"""Check or apply the canonical repo-seed label catalog on a GitHub repository.

This is a separate, explicitly invoked tool. Normal repo-seed file
synchronization (`sync-docs.py`) never requires GitHub CLI or network access,
and this tool never touches target repository files.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "pack" / "github-labels.json"

LEGACY_LABELS = {
    "bug": "type: bug",
    "enhancement": "type: feature",
    "feature": "type: feature",
    "critical": "priority: critical",
    "high": "priority: high",
    "medium": "priority: medium",
    "low": "priority: low",
    "lowest": "priority: low",
}


def load_catalog(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
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
    command = [gh, "label", "list", "--json", "name,description,color", "--limit", "1000"]
    if repo:
        command.extend(["--repo", repo])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gh label list failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def create_label(gh: str, repo: str | None, label: dict) -> None:
    command = [gh, "label", "create", label["name"], "--description", label.get("description", "")]
    if label.get("color"):
        command.extend(["--color", label["color"]])
    if repo:
        command.extend(["--repo", repo])
    subprocess.run(command, check=True)


def update_label(gh: str, repo: str | None, label: dict) -> None:
    command = [gh, "label", "edit", label["name"], "--description", label.get("description", "")]
    if label.get("color"):
        command.extend(["--color", label["color"]])
    if repo:
        command.extend(["--repo", repo])
    subprocess.run(command, check=True)


def label_differs(label: dict, existing: dict) -> bool:
    if label.get("description") and existing.get("description") != label["description"]:
        return True
    if label.get("color") and existing.get("color", "").lower() != label["color"].lower():
        return True
    return False


def audit(catalog: list[dict], hosted: list[dict]) -> list[str]:
    hosted_by_name = {entry["name"]: entry for entry in hosted}
    findings: list[str] = []
    for label in catalog:
        name = label["name"]
        existing = hosted_by_name.get(name)
        if existing is None:
            findings.append(f"missing: {name}")
        elif label_differs(label, existing):
            findings.append(f"drift: {name} differs from the canonical catalog")
    for legacy_name, replacement in LEGACY_LABELS.items():
        if legacy_name in hosted_by_name:
            findings.append(f"legacy label: '{legacy_name}' is still hosted (replace with '{replacement}')")
    return findings


def apply_catalog(gh: str, repo: str | None, catalog: list[dict], hosted: list[dict]) -> list[str]:
    hosted_by_name = {entry["name"]: entry for entry in hosted}
    report: list[str] = []
    for label in catalog:
        existing = hosted_by_name.get(label["name"])
        if existing is None:
            create_label(gh, repo, label)
            report.append(f"created: {label['name']}")
        elif label_differs(label, existing):
            update_label(gh, repo, label)
            report.append(f"updated: {label['name']}")
    for legacy_name, replacement in LEGACY_LABELS.items():
        if legacy_name in hosted_by_name:
            report.append(f"legacy label present, not removed: '{legacy_name}' (replace with '{replacement}')")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check or apply the canonical repo-seed label catalog on a GitHub repository."
    )
    parser.add_argument(
        "--catalog",
        default=str(DEFAULT_CATALOG),
        help="Path to the label catalog JSON file. Defaults to pack/github-labels.json.",
    )
    parser.add_argument("--repo", help="owner/repo to target. Defaults to the current gh-configured repository.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report drift without changing any hosted labels.")
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Create missing canonical labels and update their managed description or color. Never deletes labels.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        catalog = load_catalog(Path(args.catalog).expanduser().resolve())
        gh = require_gh()
        hosted = fetch_hosted_labels(gh, args.repo)
    except (OSError, ValueError, RuntimeError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2

    if args.check:
        findings = audit(catalog, hosted)
        for finding in findings:
            print(finding)
        if not findings:
            print("no drift detected")
            return 0
        return 1

    for line in apply_catalog(gh, args.repo, catalog, hosted):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
