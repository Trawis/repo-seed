from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPOSITORY_ROOT / "pack"
SYNC_SCRIPT = PACK_ROOT / "files" / "scripts" / "sync-docs.py"
BUILD_SCRIPT = REPOSITORY_ROOT / "scripts" / "build-release-bundle.py"
GITHUB_LABELS_SCRIPT = REPOSITORY_ROOT / "scripts" / "sync-github-labels.py"
GITHUB_LABELS_CATALOG = PACK_ROOT / "github-labels.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sync = load_module("sync_docs", SYNC_SCRIPT)
bundle_builder = load_module("build_release_bundle", BUILD_SCRIPT)
github_labels = load_module("sync_github_labels", GITHUB_LABELS_SCRIPT)

PACK_VERSION = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))["pack_version"]


def schema_1_state(profile: str = "app", managed_files: dict[str, str] | None = None) -> dict:
    """A minimal schema-1 state representative of the active pre-5.0 fleet."""
    return {
        "schema_version": 1,
        "pack_version": "4.1.0",
        "profile": profile,
        "managed_files": managed_files or {},
        "tombstones": {},
    }


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = sync.load_manifest(PACK_ROOT)

    def test_manifest_is_versioned_and_complete(self):
        self.assertEqual(self.manifest.schema_version, 3)
        self.assertEqual(self.manifest.pack_version, PACK_VERSION)
        self.assertEqual(self.manifest.state_file, ".repo-seed-state.json")
        self.assertEqual(self.manifest.profiles, ("minimal", "library", "app", "game"))
        self.assertEqual(self.manifest.package_files, ("README.md", "LICENSE", "github-labels.json"))
        for package_file in self.manifest.package_files:
            self.assertTrue((PACK_ROOT / package_file).is_file(), package_file)
        for asset in self.manifest.assets:
            self.assertTrue((PACK_ROOT / "files" / Path(asset.path)).is_file(), asset.path)

    def test_full_profile_is_removed(self):
        self.assertNotIn("full", self.manifest.profiles)
        for asset in self.manifest.assets:
            self.assertNotIn("full", asset.profiles, asset.path)

    def test_versions_are_consistent(self):
        agents = (PACK_ROOT / "files/AGENTS.md").read_text(encoding="utf-8")
        script = SYNC_SCRIPT.read_text(encoding="utf-8")
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertNotIn("SCRIPT_VERSION", script)
        self.assertNotIn("**Version**:", agents)
        self.assertEqual(sync.resolve_cli_version(str(PACK_ROOT), None), self.manifest.pack_version)
        self.assertIn(f"## {self.manifest.pack_version} -", changelog)
        # 5.0 folds the unreleased 4.2.0 entry into 5.0.0; no separate 4.2.0 section remains.
        self.assertNotIn("## 4.2.0", changelog)

    def test_pack_directory_and_manifest_inventory_match(self):
        files_root = PACK_ROOT / "files"
        actual = {
            path.relative_to(files_root).as_posix()
            for path in files_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        listed = {asset.path for asset in self.manifest.assets}
        self.assertEqual(actual, listed)

        actual_package_files = {
            path.name
            for path in PACK_ROOT.iterdir()
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(actual_package_files, set(self.manifest.package_files))
        self.assertEqual(
            (PACK_ROOT / "LICENSE").read_text(encoding="utf-8"),
            (REPOSITORY_ROOT / "LICENSE").read_text(encoding="utf-8"),
        )

    def test_manifest_uses_target_mirroring_paths_only(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        forbidden = {"id", "source", "target", "role", "legacy_targets", "previous_hashes", "migration"}
        self.assertNotIn("migration", raw)
        for asset in raw["assets"]:
            self.assertFalse(forbidden.intersection(asset), asset)

    def test_no_migration_machinery_remains_in_the_module(self):
        removed_names = (
            "LegacyState",
            "MigrationConfig",
            "RetiredAsset",
            "RetiredPathSet",
            "ScaffoldUpgrade",
            "load_migration",
            "read_legacy_state",
            "retire_legacy_paths",
            "report_project_owned_paths",
            "verified_legacy_scaffold",
            "legacy_template_id",
            "LEGACY_PROVENANCE_PATTERN",
            "file_hash",
            "detect_convention_evidence",
            "derive_migrated_conventions",
            "IGNORED_EVIDENCE_DIRS",
        )
        for name in removed_names:
            self.assertFalse(hasattr(sync, name), name)

    def test_core_guidance_is_installed_for_every_profile_regardless_of_conventions(self):
        all_profiles = {"minimal", "library", "app", "game"}
        expected = {
            "AGENTS.md": all_profiles,
            "CLAUDE.md": all_profiles,
            "scripts/sync-docs.py": all_profiles,
            ".agents/guidelines/documentation.md": all_profiles,
            ".agents/guidelines/git.md": all_profiles,
            ".agents/guidelines/ci-cd.md": all_profiles,
            ".agents/guidelines/issues.md": all_profiles,
        }
        actual = {
            asset.path: set(asset.profiles)
            for asset in self.manifest.assets
            if asset.asset_type == "managed" and asset.convention is None
        }
        self.assertEqual(actual, expected)

    def test_convention_catalog_is_independent_of_profile(self):
        all_profiles = {"minimal", "library", "app", "game"}
        expected = {
            ".agents/conventions/csharp.md": "csharp",
            ".agents/conventions/scripts.md": "scripts",
            ".agents/conventions/python.md": "python",
            ".agents/conventions/shell.md": "shell",
            ".agents/conventions/unity.md": "unity",
        }
        convention_assets_by_path = {
            asset.path: asset for asset in self.manifest.assets if asset.convention is not None
        }
        self.assertEqual({path: asset.convention for path, asset in convention_assets_by_path.items()}, expected)
        for path, asset in convention_assets_by_path.items():
            self.assertEqual(set(asset.profiles), all_profiles, path)
        self.assertEqual(
            sync.known_conventions(self.manifest),
            frozenset({"csharp", "python", "scripts", "shell", "unity"}),
        )

    def test_profiles_select_only_relevant_project_templates(self):
        common = {"changelog.template.md", "readme.template.md", "features.template.md"}
        expected = {
            "minimal": common,
            "library": common | {"architecture.template.md", "tsd.template.md"},
            "app": common | {"architecture.template.md", "fsd.template.md", "tsd.template.md", "user-guide.template.md"},
            "game": common | {"architecture.template.md", "gdd.template.md", "tsd.template.md"},
        }
        for profile, expected_names in expected.items():
            selected = sync.assets_for_profile(self.manifest, profile)
            actual_names = {
                Path(asset.path).name
                for asset in selected
                if asset.asset_type == "template"
                and asset.path.startswith("docs/templates/")
                and "/.github/" not in asset.path
                and Path(asset.path).name != "editorconfig.template"
            }
            self.assertEqual(actual_names, expected_names, profile)

    def test_reference_only_templates_have_no_scaffold_destination(self):
        assets = {asset.path: asset for asset in self.manifest.assets}
        self.assertIsNone(assets["docs/templates/tsd.template.md"].scaffold_target)
        self.assertIsNone(assets["docs/templates/features.template.md"].scaffold_target)
        self.assertEqual(
            assets["docs/templates/architecture.template.md"].scaffold_target,
            "docs/project/architecture.md",
        )

    def test_optional_group_covers_the_on_demand_documents(self):
        optional_targets = {
            asset.scaffold_target
            for asset in self.manifest.assets
            if asset.scaffold_group == "optional"
        }
        self.assertEqual(
            optional_targets,
            {
                "docs/project/architecture.md",
                "docs/project/fsd.md",
                "docs/project/gdd.md",
                "docs/project/user-guide.md",
            },
        )
        project_targets = {
            asset.scaffold_target
            for asset in self.manifest.assets
            if asset.scaffold_group == "project"
        }
        self.assertEqual(project_targets, {"README.md", "CHANGELOG.md"})

    def test_template_scaffold_fields_must_be_both_present_or_absent(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        asset = next(
            item
            for item in raw["assets"]
            if item["path"] == "docs/templates/tsd.template.md"
        )
        asset["scaffold_group"] = "project"
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            shutil.copytree(PACK_ROOT / "files", pack / "files")
            raw["package_files"] = []
            (pack / "manifest.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "both scaffold fields or neither"):
                sync.load_manifest(pack)

    def test_unsafe_paths_are_rejected(self):
        for value in ("../outside", "/absolute", r"docs\windows", "C:/drive", "docs/./file"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    sync.relative_path(value, "test")

    def test_invalid_manifest_and_missing_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            (pack / "files").mkdir()
            invalid = {
                "schema_version": 3,
                "pack_version": PACK_VERSION,
                "state_file": ".repo-seed-state.json",
                "profiles": ["minimal"],
                "assets": [
                    {
                        "path": "../outside.md",
                        "type": "managed",
                        "profiles": ["minimal"],
                    }
                ],
            }
            (pack / "manifest.json").write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(ValueError):
                sync.load_manifest(pack)

            invalid["assets"][0]["path"] = "missing.md"
            (pack / "manifest.json").write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not exist"):
                sync.load_manifest(pack)

    def test_unsupported_schema_version_is_rejected(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        for version in (2, 4, None):
            with self.subTest(version=version):
                with tempfile.TemporaryDirectory() as temp:
                    pack = Path(temp)
                    shutil.copytree(PACK_ROOT / "files", pack / "files")
                    modified = dict(raw)
                    modified["schema_version"] = version
                    (pack / "manifest.json").write_text(json.dumps(modified), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "schema_version"):
                        sync.load_manifest(pack)

    def test_package_files_must_be_safe_and_present(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            managed = pack / "files/AGENTS.md"
            managed.parent.mkdir(parents=True)
            managed.write_text("# Managed\n", encoding="utf-8")
            manifest = {
                "schema_version": 3,
                "pack_version": PACK_VERSION,
                "state_file": ".repo-seed-state.json",
                "profiles": ["minimal"],
                "package_files": ["../README.md"],
                "assets": [
                    {"path": "AGENTS.md", "type": "managed", "profiles": ["minimal"]}
                ],
            }
            (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsafe path"):
                sync.load_manifest(pack)

            manifest["package_files"] = ["README.md"]
            (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not exist"):
                sync.load_manifest(pack)

    def test_manifest_rejects_scaffold_managed_path_collisions(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            template = pack / "files/docs/templates/readme.template.md"
            managed = pack / "files/README.md"
            template.parent.mkdir(parents=True)
            managed.parent.mkdir(parents=True, exist_ok=True)
            template.write_text(
                "# Template\n<!-- repo-seed-template:start -->\nmetadata\n"
                "<!-- repo-seed-template:end -->\nBody\n",
                encoding="utf-8",
            )
            managed.write_text("# Managed\n", encoding="utf-8")
            manifest = {
                "schema_version": 3,
                "pack_version": PACK_VERSION,
                "state_file": ".repo-seed-state.json",
                "profiles": ["minimal"],
                "assets": [
                    {"path": "README.md", "type": "managed", "profiles": ["minimal"]},
                    {
                        "path": "docs/templates/readme.template.md",
                        "type": "template",
                        "profiles": ["minimal"],
                        "scaffold_group": "project",
                        "scaffold_target": "README.md",
                    },
                ],
            }
            (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "collide"):
                sync.load_manifest(pack)

    def test_manifest_rejects_project_owned_workflow_paths(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))

        def assert_rejected(manifest):
            with tempfile.TemporaryDirectory() as temp:
                pack = Path(temp)
                (pack / "manifest.json").write_text(
                    json.dumps(manifest),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "project-owned tree"):
                    sync.load_manifest(pack, validate_sources=False)
                with self.assertRaisesRegex(ValueError, "project-owned tree"):
                    bundle_builder.load_manifest(pack)

        managed = json.loads(json.dumps(raw))
        managed["assets"][0]["path"] = ".github/workflows/ci.yml"
        assert_rejected(managed)

        scaffolded = json.loads(json.dumps(raw))
        template = next(
            asset
            for asset in scaffolded["assets"]
            if asset.get("scaffold_group") == "github"
        )
        template["scaffold_target"] = ".github/workflows/ci.yml"
        assert_rejected(scaffolded)

    def test_convention_field_only_applies_to_managed_assets(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        modified = json.loads(json.dumps(raw))
        template = next(asset for asset in modified["assets"] if asset["path"].endswith("readme.template.md"))
        template["convention"] = "csharp"
        modified["package_files"] = []
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            shutil.copytree(PACK_ROOT / "files", pack / "files")
            (pack / "manifest.json").write_text(json.dumps(modified), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "convention only applies to managed"):
                sync.load_manifest(pack)


class GuidanceAndTemplateTests(unittest.TestCase):
    def test_agent_entry_points_route_specialized_work(self):
        agents = (PACK_ROOT / "files/AGENTS.md").read_text(encoding="utf-8")
        claude = (PACK_ROOT / "files/CLAUDE.md").read_text(encoding="utf-8")
        for required in (
            ".agents/project.md",
            "child `AGENTS.md`",
            "docs/project/",
            "docs/templates/",
            ".agents/guidelines/documentation.md",
            ".agents/guidelines/git.md",
            ".agents/guidelines/ci-cd.md",
            ".agents/guidelines/issues.md",
            ".agents/conventions/",
            "scripts/sync-docs.py",
            "Load only the guidance relevant to the task",
            "Do not scan `docs/project/` by default",
        ):
            self.assertIn(required, agents)
        self.assertIn("@AGENTS.md", claude)
        self.assertFalse((PACK_ROOT / "files/.agents/base.md").exists())

    def test_issue_guidance_is_not_conflated_with_pull_request_guidance(self):
        agents = (PACK_ROOT / "files/AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(agents.split())
        self.assertIn(
            "Git, branches, commits, pull requests, or PR descriptions: `.agents/guidelines/git.md`",
            normalized,
        )
        self.assertIn(
            "issue creation, labels, issue structure, or triage: `.agents/guidelines/issues.md`",
            normalized,
        )
        issues_guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        git_guidance = (PACK_ROOT / "files/.agents/guidelines/git.md").read_text(encoding="utf-8")
        self.assertIn("Keep PR titles and descriptions concise", git_guidance)
        self.assertNotIn("Keep PR titles", issues_guidance)
        self.assertNotIn("pull-request template", issues_guidance.lower())

    def test_managed_claude_wrapper_is_a_minimal_agents_import(self):
        claude = (PACK_ROOT / "files/CLAUDE.md").read_text(encoding="utf-8")
        visible = re.sub(r"<!--.*?-->", "", claude, flags=re.DOTALL).strip()
        self.assertEqual(visible, "@AGENTS.md")
        for duplicated in (
            "primary project instruction file",
            "Use the imported",
            "## Claude Code",
            "Document role",
        ):
            self.assertNotIn(duplicated, claude)
        for guidance_import in (
            "@.agents/guidelines/",
            "@.agents/conventions/",
            "@.agents/project.md",
            "@AGENTS.md\n@",
        ):
            self.assertNotIn(guidance_import, claude)

    def test_documentation_guidance_routes_only_applicable_bootstrap_documents(self):
        guidance = (
            PACK_ROOT / "files/.agents/guidelines/documentation.md"
        ).read_text(encoding="utf-8")
        self.assertIn("FSD for\n   applications or GDD for games", guidance)
        self.assertIn("user guidance for user-facing products", guidance)
        tsd = (PACK_ROOT / "files/docs/templates/tsd.template.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("issue, acceptance criteria, FSD, or GDD", tsd)

    def test_git_guidance_scopes_branch_model_preflight_to_git_operations(self):
        guidance = (PACK_ROOT / "files/.agents/guidelines/git.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(guidance.split())
        for required in (
            "Branch Model Preflight",
            "current branch and working tree",
            "applicable `AGENTS.md` files",
            ".agents/project.md",
            "CONTRIBUTING.md",
            "Consult remote or hosted information only when needed",
            "protected branches",
            "GitHub Flow",
            "GitFlow",
            "develop` or `dev`",
            "normal feature PRs must not target `main`",
            "Unknown model",
            "Do not infer GitHub Flow only because",
            "hosted default branch is `main` or `master`",
            "Unknown base branch",
            "missing branch-name convention",
            "wrong PR target is blocking",
            "Editing files alone does not require",
        ):
            self.assertIn(required, normalized)
        self.assertNotIn("Before starting work that may change files", normalized)

    def test_agent_guidance_scopes_code_inspection_and_final_compliance(self):
        agents = (PACK_ROOT / "files/AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(agents.split())
        for required in (
            "Inspect the affected implementation and nearby tests before editing",
            "Follow nearby established patterns",
            "only when relevant to the change or needed to resolve an uncertainty",
            "Make the smallest safe change",
            "review the final diff against the request",
            "scope, correctness, applicable local conventions, ownership boundaries",
            "Check branch and pull-request requirements only when performing Git",
            "Run the narrowest relevant validation",
        ):
            self.assertIn(required, normalized)
        for overly_broad in (
            "Before editing code, identify applicable conventions",
            "formatter and linter config, test style, naming, imports",
            "recheck the final diff against branch name, base branch, PR target",
        ):
            self.assertNotIn(overly_broad, normalized)

    def test_update_docs_prefer_the_new_pack_script(self):
        for path in (REPOSITORY_ROOT / "README.md", PACK_ROOT / "README.md"):
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                "python /path/to/extracted/pack/files/scripts/sync-docs.py",
                content,
            )

    def test_every_template_has_valid_metadata_and_a_body(self):
        for asset in sync.load_manifest(PACK_ROOT).assets:
            if asset.asset_type == "template":
                body = sync.template_body(PACK_ROOT / "files" / asset.path)
                self.assertTrue(body.strip(), asset.path)
                self.assertNotIn(sync.TEMPLATE_METADATA_START, body)
                self.assertNotIn(sync.TEMPLATE_METADATA_END, body)

    def test_markdown_templates_are_plain_ascii_and_wrapped(self):
        for path in (PACK_ROOT / "files/docs/templates").rglob("*.template.md"):
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertTrue(content.isascii())
                self.assertNotIn("Unreleased", content)
            for line_number, line in enumerate(content.splitlines(), 1):
                with self.subTest(path=path, line=line_number):
                    self.assertLessEqual(len(line), 100)

    def test_project_doc_templates_avoid_decision_diary_language(self):
        banned = (
            "we decided",
            "this replaces",
            "the old system",
            "consolidated",
            "tighter redesign",
            "because we",
            "because the previous version",
            "more legal sandbox depth",
        )
        for asset in sync.load_manifest(PACK_ROOT).assets:
            if asset.asset_type != "template" or not asset.path.endswith(".template.md"):
                continue
            source = PACK_ROOT / "files" / asset.path
            generated = sync.template_body(source)
            if asset.scaffold_target:
                generated = sync.render_scaffold(PACK_ROOT, asset)
            generated = generated.lower()
            with self.subTest(path=asset.path):
                for phrase in banned:
                    self.assertNotIn(phrase, generated)

    def test_architecture_scaffold_guidance_is_not_live_prose(self):
        asset = next(
            asset
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.path == "docs/templates/architecture.template.md"
        )
        rendered = sync.render_scaffold(PACK_ROOT, asset)
        visible = re.sub(r"<!--.*?-->", "", rendered, flags=re.DOTALL)
        self.assertIn("<!-- Remove this guidance", rendered)
        self.assertNotIn("Describe the verified current technical system", visible)
        self.assertIn("## Purpose, Scope, and Quality Goals", visible)

    def test_document_field_blocks_render_as_lists(self):
        bare_field_pattern = re.compile(
            r"^\*\*(Project|Game|Change|Status|Basis|Owner|Audience|Last Updated)\*\*:",
            re.MULTILINE,
        )
        for path in (PACK_ROOT / "files/docs/templates").rglob("*.template.md"):
            body = sync.template_body(path)
            with self.subTest(path=path):
                self.assertIsNone(bare_field_pattern.search(body))

    def test_markdown_source_marker_preserves_github_frontmatter(self):
        asset = next(
            asset
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.path.endswith("bug-report.template.md")
        )
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            action = sync.scaffold_asset(PACK_ROOT, target, asset, dry_run=False)
            content = (target / asset.scaffold_target).read_text(encoding="utf-8")
            self.assertEqual(action.action, "scaffold")
            self.assertTrue(content.startswith("---\n"))
            self.assertIn(f"<!-- Scaffolded from: {asset.path} -->", content)
            self.assertRegex(content, r"<!-- Scaffolded content SHA-256: [0-9a-f]{64} -->")
            self.assertLess(content.index("\n---", 4), content.index("<!-- Scaffolded from:"))

    def test_scaffolded_issue_templates_use_canonical_type_labels(self):
        manifest = sync.load_manifest(PACK_ROOT)
        bug_asset = next(
            asset for asset in manifest.assets if asset.path.endswith("bug-report.template.md")
        )
        feature_asset = next(
            asset for asset in manifest.assets if asset.path.endswith("feature-request.template.md")
        )
        bug_rendered = sync.render_scaffold(PACK_ROOT, bug_asset)
        feature_rendered = sync.render_scaffold(PACK_ROOT, feature_asset)
        self.assertIn('labels: ["type: bug"]', bug_rendered)
        self.assertIn('labels: ["type: feature"]', feature_rendered)
        self.assertNotIn("labels: bug", bug_rendered)
        self.assertNotIn("labels: enhancement", feature_rendered)

    def test_issues_guidance_defines_canonical_catalog_and_entry_points(self):
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        for required in (
            "type: bug",
            "type: feature",
            "type: tech-debt",
            "type: chore",
            "type: decision",
            "type: idea",
            "priority: critical",
            "priority: high",
            "priority: medium",
            "priority: low",
            "Do not establish a mandatory shared `area:*` taxonomy",
            "Priority is optional",
            "Bug Report",
            "Feature Request",
            "Blank issue -> assign type manually",
            "blank_issues_enabled: false",
            "do not add GitHub Issue Forms",
            "Do not replace `type:*` labels with GitHub's native issue types",
        ):
            self.assertIn(required, guidance)
        for legacy, replacement in {
            "bug": "type: bug",
            "enhancement": "type: feature",
            "critical": "priority: critical",
            "lowest": "priority: low",
        }.items():
            self.assertIn(legacy, guidance)
            self.assertIn(replacement, guidance)

    def test_distributed_issue_guidance_is_self_contained_for_target_repositories(self):
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        self.assertNotIn("pack/github-labels.json", guidance)
        self.assertNotIn("scripts/sync-github-labels.py", guidance)
        self.assertIn("GitHub-Hosted Labels", guidance)
        self.assertIn("verify it\ndirectly through GitHub", guidance)

    def test_no_distributed_file_references_repo_seed_only_tooling_paths(self):
        forbidden = ("pack/github-labels.json", "scripts/sync-github-labels.py")
        files_root = PACK_ROOT / "files"
        for path in files_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            for needle in forbidden:
                with self.subTest(path=path.relative_to(PACK_ROOT), needle=needle):
                    self.assertNotIn(needle, content)

    def test_manifest_has_exactly_two_contributor_issue_templates(self):
        github_scaffolds = {
            asset.scaffold_target
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.scaffold_group == "github"
        }
        self.assertEqual(
            github_scaffolds,
            {
                ".github/ISSUE_TEMPLATE/bug_report.md",
                ".github/ISSUE_TEMPLATE/feature_request.md",
                ".github/ISSUE_TEMPLATE/config.yml",
            },
        )

    def test_scaffolded_templates_have_no_forced_title_or_assignee(self):
        manifest = sync.load_manifest(PACK_ROOT)
        for suffix in ("bug-report.template.md", "feature-request.template.md"):
            asset = next(asset for asset in manifest.assets if asset.path.endswith(suffix))
            rendered = sync.render_scaffold(PACK_ROOT, asset)
            self.assertIn('title: ""', rendered)
            self.assertIn('assignees: ""', rendered)
            self.assertNotIn("[BUG]", rendered)

    def test_root_issue_chooser_has_two_valid_markdown_templates(self):
        issue_root = REPOSITORY_ROOT / ".github/ISSUE_TEMPLATE"
        for name in ("bug_report.md", "feature_request.md"):
            content = (issue_root / name).read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\n"), name)
            frontmatter = content.split("---", 2)[1]
            self.assertIn("name:", frontmatter, name)
            self.assertIn("about:", frontmatter, name)
        self.assertEqual(
            (issue_root / "config.yml").read_text(encoding="utf-8").strip(),
            "blank_issues_enabled: false",
        )


class ConventionSelectionTests(unittest.TestCase):
    def test_fresh_install_selects_no_conventions_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app")
            for name in ("csharp", "python", "scripts", "shell", "unity"):
                self.assertFalse((target / f".agents/conventions/{name}.md").exists(), name)
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual(state["conventions"], [])

    def test_selected_conventions_are_installed_and_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))
            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            self.assertFalse((target / ".agents/conventions/python.md").exists())
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["conventions"], ["csharp"])

    def test_conventions_available_even_under_the_minimal_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", conventions=frozenset({"python"}))
            self.assertTrue((target / ".agents/conventions/python.md").is_file())

    def test_omitted_conventions_reuse_the_recorded_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp", "shell"}))
            sync.synchronize(PACK_ROOT, target, "app")
            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            self.assertTrue((target / ".agents/conventions/shell.md").is_file())

    def test_changing_conventions_prunes_unchanged_but_preserves_modified_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp", "python"}))
            (target / ".agents/conventions/python.md").write_text("local customization\n", encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))

            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            self.assertTrue((target / ".agents/conventions/python.md").is_file())
            self.assertEqual(
                (target / ".agents/conventions/python.md").read_text(encoding="utf-8"),
                "local customization\n",
            )
            self.assertTrue(
                any(
                    action.action == "preserve" and action.path == ".agents/conventions/python.md"
                    for action in actions
                )
            )
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertIn(".agents/conventions/python.md", state["tombstones"])

    def test_switching_conventions_removes_unchanged_unselected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp", "python"}))
            actions = sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))
            self.assertFalse((target / ".agents/conventions/python.md").exists())
            self.assertTrue(
                any(
                    action.action == "remove" and action.path == ".agents/conventions/python.md"
                    for action in actions
                )
            )

    def test_unknown_convention_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            with self.assertRaisesRegex(ValueError, "Unknown convention"):
                sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"rust"}))
            self.assertEqual(list(target.iterdir()), [])

    def test_pre_5_0_state_without_conventions_fails_clearly_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".repo-seed-state.json").write_text(json.dumps(schema_1_state()), encoding="utf-8")
            before = (target / ".repo-seed-state.json").read_bytes()

            with self.assertRaisesRegex(ValueError, re.escape(sync.PRE_5_0_STATE_ERROR)):
                sync.synchronize(PACK_ROOT, target, "app")

            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), before)
            self.assertEqual(list(target.iterdir()), [target / ".repo-seed-state.json"])

    def test_pre_5_0_state_with_explicit_conventions_converts_to_schema_2(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            manifest = sync.load_manifest(PACK_ROOT)
            csharp_asset = next(a for a in manifest.assets if a.convention == "csharp")
            source = PACK_ROOT / "files" / csharp_asset.path
            destination = target / csharp_asset.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            state = schema_1_state(
                profile="app",
                managed_files={csharp_asset.path: sync.managed_file_hash(destination)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")
            project_owned = target / "docs/project/notes.md"
            project_owned.parent.mkdir(parents=True, exist_ok=True)
            project_owned.write_text("# Project notes\n", encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))

            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertEqual(project_owned.read_text(encoding="utf-8"), "# Project notes\n")
            new_state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(new_state["schema_version"], 2)
            self.assertEqual(new_state["conventions"], ["csharp"])
            self.assertTrue(any(action.action == "copy" and action.path == "AGENTS.md" for action in actions))

            # A second sync with no arguments is now fully idempotent: no migration behavior remains.
            second_actions = sync.synchronize(PACK_ROOT, target, "app")
            self.assertTrue(
                all(action.action in {"unchanged", "state"} for action in second_actions),
                [(a.action, a.path) for a in second_actions],
            )

    def test_pre_5_0_conversion_drops_a_convention_not_re_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            manifest = sync.load_manifest(PACK_ROOT)
            csharp_asset = next(a for a in manifest.assets if a.convention == "csharp")
            source = PACK_ROOT / "files" / csharp_asset.path
            destination = target / csharp_asset.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            state = schema_1_state(
                profile="library",
                managed_files={csharp_asset.path: sync.managed_file_hash(destination)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            sync.synchronize(PACK_ROOT, target, "library", conventions=frozenset({"python"}))

            self.assertFalse((target / ".agents/conventions/csharp.md").exists())
            self.assertTrue((target / ".agents/conventions/python.md").is_file())

    def test_audit_reports_unused_managed_convention(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp", "python"}))

            report = sync.audit_target(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))

            self.assertTrue(
                any("unused managed convention: .agents/conventions/python.md" in line for line in report)
            )
            self.assertIn("conventions: csharp", report)
            self.assertTrue((target / ".agents/conventions/python.md").is_file())

    def test_audit_on_a_pre_5_0_state_reports_info_without_failing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".repo-seed-state.json").write_text(json.dumps(schema_1_state()), encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "app")

            self.assertTrue(
                any("pre-5.0 state without explicit conventions" in line and line.startswith("info:") for line in report)
            )
            self.assertEqual(list(target.iterdir()), [target / ".repo-seed-state.json"])

    def test_cli_conventions_flag_is_persisted_and_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            first = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--profile",
                    "app",
                    "--conventions",
                    "csharp,shell",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            self.assertTrue((target / ".agents/conventions/shell.md").is_file())
            self.assertFalse((target / ".agents/conventions/python.md").exists())

            repeat = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(repeat.returncode, 0, repeat.stderr)

    def test_cli_rejects_an_unknown_convention_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--profile",
                    "app",
                    "--conventions",
                    "rust",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Unknown convention", result.stderr)
            self.assertEqual(list(target.iterdir()), [])

    def test_cli_reports_the_pre_5_0_error_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".repo-seed-state.json").write_text(json.dumps(schema_1_state()), encoding="utf-8")
            before = (target / ".repo-seed-state.json").read_bytes()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--profile",
                    "app",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("pre-5.0 repo-seed state", result.stderr)
            self.assertIn("Rerun with --conventions", result.stderr)
            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), before)


class SyncBehaviorTests(unittest.TestCase):
    def test_matching_managed_files_are_unchanged_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            agents = target / "AGENTS.md"
            claude = target / "CLAUDE.md"
            state_path = target / ".repo-seed-state.json"
            marker_time = 1_600_000_000_000_000_000
            os.utime(agents, ns=(marker_time, marker_time))
            os.utime(state_path, ns=(marker_time, marker_time))
            claude.write_text(claude.read_text(encoding="utf-8"), encoding="utf-8", newline="\r\n")
            claude_bytes = claude.read_bytes()

            actions = sync.synchronize(PACK_ROOT, target, "minimal")
            managed = [
                action
                for action in actions
                if action.path in {asset.path for asset in sync.assets_for_profile(sync.load_manifest(PACK_ROOT), "minimal")}
            ]
            self.assertTrue(managed)
            self.assertEqual({action.action for action in managed}, {"unchanged"})
            self.assertTrue(
                any(
                    action.action == "unchanged" and action.path == ".repo-seed-state.json"
                    for action in actions
                )
            )
            self.assertEqual(agents.stat().st_mtime_ns, marker_time)
            self.assertEqual(state_path.stat().st_mtime_ns, marker_time)
            self.assertEqual(claude.read_bytes(), claude_bytes)

            dry_run_actions = sync.synchronize(PACK_ROOT, target, "minimal", dry_run=True)
            self.assertEqual(
                {
                    action.action
                    for action in dry_run_actions
                    if action.path in {managed_action.path for managed_action in managed}
                },
                {"unchanged"},
            )
            self.assertEqual(agents.stat().st_mtime_ns, marker_time)
            self.assertEqual(state_path.stat().st_mtime_ns, marker_time)

    def test_different_managed_files_and_templates_are_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "docs/templates").mkdir(parents=True)
            (target / "AGENTS.md").write_text("local edit\n", encoding="utf-8")
            (target / "docs/templates/readme.template.md").write_text("local template edit\n", encoding="utf-8")
            sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertEqual((target / "AGENTS.md").read_bytes(), (PACK_ROOT / "files/AGENTS.md").read_bytes())
            self.assertEqual(
                (target / "docs/templates/readme.template.md").read_bytes(),
                (PACK_ROOT / "files/docs/templates/readme.template.md").read_bytes(),
            )
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "LICENSE").exists())

    def test_old_format_claude_wrapper_is_overwritten_with_the_minimal_import(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            claude = target / "CLAUDE.md"
            claude.write_text(
                "# CLAUDE.md\n\n@AGENTS.md\n\n## Claude Code\n\n"
                "Use the imported `AGENTS.md` as the primary project instruction file.\n",
                encoding="utf-8",
            )

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertEqual(claude.read_bytes(), (PACK_ROOT / "files/CLAUDE.md").read_bytes())
            self.assertNotIn("primary project instruction file", claude.read_text(encoding="utf-8"))
            self.assertTrue(any(action.path == "CLAUDE.md" and action.action == "copy" for action in actions))

    def test_every_profile_syncs_the_identical_minimal_claude_wrapper(self):
        source_bytes = (PACK_ROOT / "files/CLAUDE.md").read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for profile in sync.load_manifest(PACK_ROOT).profiles:
                target = root / profile
                target.mkdir()
                sync.synchronize(PACK_ROOT, target, profile)
                self.assertEqual((target / "CLAUDE.md").read_bytes(), source_bytes, profile)

    def test_every_profile_transition_leaves_exact_managed_selection(self):
        manifest = sync.load_manifest(PACK_ROOT)
        for source_profile in manifest.profiles:
            for target_profile in manifest.profiles:
                with self.subTest(source=source_profile, target=target_profile):
                    with tempfile.TemporaryDirectory() as temp:
                        target = Path(temp)
                        unknown = target / "project-owned.txt"
                        unknown.write_text("keep\n", encoding="utf-8")
                        sync.synchronize(PACK_ROOT, target, source_profile)
                        sync.synchronize(PACK_ROOT, target, target_profile)

                        selected = {
                            asset.path
                            for asset in sync.assets_for_profile(manifest, target_profile)
                        }
                        for asset in manifest.assets:
                            self.assertEqual(
                                (target / asset.path).is_file(),
                                asset.path in selected,
                                f"{source_profile} -> {target_profile}: {asset.path}",
                            )
                        self.assertEqual(unknown.read_text(encoding="utf-8"), "keep\n")

    def test_profile_changes_preserve_existing_github_workflows(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            workflows = target / ".github/workflows"
            workflows.mkdir(parents=True)
            ci = workflows / "ci.yml"
            release = workflows / "release.yml"
            ci.write_text("name: Project CI\n", encoding="utf-8")
            release.write_text("name: Project release\n", encoding="utf-8")
            expected = {ci: ci.read_bytes(), release: release.read_bytes()}

            sync.synchronize(PACK_ROOT, target, "game", scaffold_github_templates=True)
            actions = sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)

            for path, content in expected.items():
                self.assertEqual(path.read_bytes(), content)
            self.assertFalse(any(action.path.startswith(".github/workflows/") for action in actions))

    def test_profile_reduction_removes_unchanged_stale_managed_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game", conventions=frozenset({"unity"}))
            gdd = target / "docs/templates/gdd.template.md"
            self.assertTrue(gdd.is_file())
            actions = sync.synchronize(PACK_ROOT, target, "minimal", conventions=frozenset())

            self.assertFalse(gdd.exists())
            self.assertFalse((target / ".agents/conventions/unity.md").exists())
            removed = {action.path for action in actions if action.action == "remove"}
            self.assertIn("docs/templates/gdd.template.md", removed)
            self.assertIn(".agents/conventions/unity.md", removed)
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["profile"], "minimal")
            self.assertEqual(state["tombstones"], {})

    def test_modified_stale_asset_remains_tombstoned_until_safe_to_remove(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game")
            gdd = target / "docs/templates/gdd.template.md"
            original = (PACK_ROOT / "files/docs/templates/gdd.template.md").read_bytes()
            gdd.write_text("local changes\n", encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app")

            self.assertTrue(gdd.is_file())
            self.assertTrue(
                any(
                    action.action == "preserve" and action.path == "docs/templates/gdd.template.md"
                    for action in actions
                )
            )
            state_path = target / ".repo-seed-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn("docs/templates/gdd.template.md", state["tombstones"])

            gdd.write_bytes(original)
            before_dry_run = state_path.read_bytes()
            actions = sync.synchronize(PACK_ROOT, target, "app", dry_run=True)
            self.assertTrue(gdd.is_file())
            self.assertEqual(state_path.read_bytes(), before_dry_run)
            self.assertTrue(
                any(
                    action.action == "remove" and action.path == "docs/templates/gdd.template.md"
                    for action in actions
                )
            )

            sync.synchronize(PACK_ROOT, target, "app")
            self.assertFalse(gdd.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("docs/templates/gdd.template.md", state["tombstones"])

    def test_state_bootstrap_prunes_known_current_assets_but_not_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game")
            (target / ".repo-seed-state.json").unlink()
            unknown = target / "project-owned.txt"
            unknown.write_text("keep\n", encoding="utf-8")

            sync.synchronize(PACK_ROOT, target, "app")

            self.assertFalse((target / "docs/templates/gdd.template.md").exists())
            self.assertEqual(unknown.read_text(encoding="utf-8"), "keep\n")

    def test_project_scaffolding_excludes_editorconfig(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", scaffold_project_files=True)
            for relative in ("README.md", "CHANGELOG.md"):
                self.assertTrue((target / relative).is_file(), relative)
            self.assertFalse((target / ".editorconfig").exists())
            self.assertFalse((target / ".gitignore").exists())
            self.assertFalse((target / "docs/project").exists())
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("<!-- Scaffolded from: docs/templates/readme.template.md -->", readme)
            self.assertNotIn(sync.TEMPLATE_METADATA_START, readme)

    def test_scaffold_project_files_only_creates_the_baseline_readme_and_changelog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for profile in ("minimal", "library", "app", "game"):
                target = root / profile
                target.mkdir()
                sync.synchronize(PACK_ROOT, target, profile, scaffold_project_files=True)
                actual = {
                    path.relative_to(target).as_posix()
                    for path in target.rglob("*")
                    if path.is_file() and (path.name in {"README.md", "CHANGELOG.md"} or "docs/project" in path.as_posix())
                }
                self.assertEqual(actual, {"README.md", "CHANGELOG.md"}, profile)

    def test_on_demand_scaffold_creates_only_the_requested_optional_document(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            actions = sync.synchronize(PACK_ROOT, target, "app", scaffold_names=("architecture",))
            self.assertTrue((target / "docs/project/architecture.md").is_file())
            self.assertFalse((target / "docs/project/fsd.md").exists())
            self.assertFalse((target / "docs/project/user-guide.md").exists())
            self.assertFalse((target / "README.md").exists())
            content = (target / "docs/project/architecture.md").read_text(encoding="utf-8")
            self.assertIn("<!-- Scaffolded from: docs/templates/architecture.template.md -->", content)
            self.assertTrue(
                any(
                    action.action == "scaffold" and action.path == "docs/project/architecture.md"
                    for action in actions
                )
            )

    def test_on_demand_scaffold_can_combine_multiple_names_with_baseline_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                scaffold_project_files=True,
                scaffold_names=("fsd", "user-guide"),
            )
            for relative in ("README.md", "CHANGELOG.md", "docs/project/fsd.md", "docs/project/user-guide.md"):
                self.assertTrue((target / relative).is_file(), relative)
            self.assertFalse((target / "docs/project/architecture.md").exists())

    def test_on_demand_scaffold_refuses_a_name_unavailable_for_the_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            with self.assertRaisesRegex(ValueError, "Unknown or unavailable scaffold 'gdd'"):
                sync.synchronize(PACK_ROOT, target, "app", scaffold_names=("gdd",))
            self.assertEqual(list(target.iterdir()), [])

    def test_on_demand_scaffold_never_overwrites_a_project_owned_document(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            architecture = target / "docs/project/architecture.md"
            architecture.parent.mkdir(parents=True)
            architecture.write_text("# Existing project architecture\n", encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app", scaffold_names=("architecture",))

            self.assertEqual(architecture.read_text(encoding="utf-8"), "# Existing project architecture\n")
            self.assertTrue(
                any(
                    action.action == "skip" and action.path == "docs/project/architecture.md"
                    for action in actions
                )
            )

    def test_app_to_game_prunes_references_but_preserves_live_docs(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                scaffold_project_files=True,
                scaffold_names=("architecture", "user-guide", "fsd"),
            )
            project_tsd = target / "docs/project/tsd.md"
            project_tsd.parent.mkdir(parents=True, exist_ok=True)
            project_tsd.write_text("# Existing project TSD\n", encoding="utf-8")
            live_documents = (
                "docs/project/architecture.md",
                "docs/project/user-guide.md",
                "docs/project/fsd.md",
                "docs/project/tsd.md",
            )
            for path in live_documents:
                self.assertTrue((target / path).is_file())

            sync.synchronize(PACK_ROOT, target, "game")

            for path in (
                "docs/templates/user-guide.template.md",
                "docs/templates/fsd.template.md",
            ):
                self.assertFalse((target / path).exists())
            for path in (
                "docs/templates/architecture.template.md",
                "docs/templates/tsd.template.md",
            ):
                self.assertTrue((target / path).is_file())
            for path in live_documents:
                self.assertTrue((target / path).is_file())

    def test_existing_project_owned_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            existing = {
                "README.md": "project readme\n",
                ".editorconfig": "root = false\n",
                ".gitignore": "project-specific-output/\n",
                ".github/ISSUE_TEMPLATE/bug_report.md": "project bug form\n",
                "docs/project/features.md": "project capability index\n",
                "docs/project/tsd.md": "existing project technical document\n",
            }
            for relative, content in existing.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
            )
            for relative, content in existing.items():
                self.assertEqual((target / relative).read_text(encoding="utf-8"), content)
            self.assertFalse(any(action.path == ".gitignore" for action in actions))

            repeat = sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
            )
            self.assertFalse(any(action.path == ".gitignore" for action in repeat))

    def test_github_scaffolding_is_explicit_and_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            issue_root = target / ".github/ISSUE_TEMPLATE"
            self.assertFalse(issue_root.exists())
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            for name in ("bug_report.md", "feature_request.md", "config.yml"):
                self.assertTrue((issue_root / name).is_file(), name)
            self.assertEqual(
                (issue_root / "config.yml").read_text(encoding="utf-8").strip(),
                "blank_issues_enabled: false",
            )

    def test_preflight_rejects_directory_managed_target_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            agents = target / "AGENTS.md"
            agents.write_text("preserve me\n", encoding="utf-8")
            (target / "CLAUDE.md").mkdir()
            with self.assertRaisesRegex(ValueError, "not a file"):
                sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertEqual(agents.read_text(encoding="utf-8"), "preserve me\n")
            self.assertFalse((target / "CLAUDE.md/CLAUDE.md").exists())

    def test_preflight_rejects_parent_file_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            agents = target / "AGENTS.md"
            agents.write_text("preserve me\n", encoding="utf-8")
            (target / "scripts").write_text("not a directory\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "parent is not a directory"):
                sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertEqual(agents.read_text(encoding="utf-8"), "preserve me\n")

    def test_dry_run_validates_but_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                conventions=frozenset({"csharp"}),
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
                scaffold_names=("architecture",),
                dry_run=True,
            )
            self.assertTrue(actions)
            self.assertEqual(list(target.iterdir()), [])

    def test_editorconfig_scaffolding_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_editorconfig=True)
            content = (target / ".editorconfig").read_text(encoding="utf-8")
            self.assertIn("root = true", content)
            self.assertNotIn(sync.TEMPLATE_METADATA_START, content)

    def test_invalid_managed_state_fails_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".repo-seed-state.json").write_text("{invalid", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "not valid JSON"):
                sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertFalse((target / "AGENTS.md").exists())

    def test_managed_state_rejects_unknown_pack_owned_paths_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            important = target / "src/important.py"
            important.parent.mkdir(parents=True)
            important.write_text("important = True\n", encoding="utf-8")
            state = {
                "schema_version": 2,
                "pack_version": "5.0.0",
                "profile": "minimal",
                "conventions": [],
                "managed_files": {
                    "src/important.py": sync.managed_file_hash(important),
                },
                "tombstones": {},
            }
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unknown pack-owned path"):
                sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertEqual(important.read_text(encoding="utf-8"), "important = True\n")
            self.assertFalse((target / "AGENTS.md").exists())

    def test_state_rejects_editorconfig_recorded_as_a_managed_path(self):
        # .editorconfig is only ever a scaffold_target, never an asset path, so a
        # state file that records it under managed_files is invalid state, not a
        # legitimate historical reclassification.
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            editorconfig = target / ".editorconfig"
            editorconfig.write_text("root = false\n", encoding="utf-8")
            state_path = target / ".repo-seed-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["managed_files"][".editorconfig"] = sync.managed_file_hash(editorconfig)
            state_path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unknown pack-owned path"):
                sync.synchronize(PACK_ROOT, target, "minimal")

    def test_copied_script_updates_from_an_explicit_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            result = subprocess.run(
                [
                    sys.executable,
                    str(target / "scripts/sync-docs.py"),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--profile",
                    "minimal",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sync complete.", result.stdout)

    def test_copied_script_reports_version_from_managed_state(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            result = subprocess.run(
                [
                    sys.executable,
                    str(target / "scripts/sync-docs.py"),
                    "--target",
                    str(target),
                    "--version",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), f"sync-docs.py {PACK_VERSION}")

    def test_copied_script_without_a_pack_requests_source(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            result = subprocess.run(
                [sys.executable, str(target / "scripts/sync-docs.py"), "--target", str(target)],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("pass --source", result.stderr)

    def test_audit_reports_no_drift_for_a_fresh_sync(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            project_guidance = target / ".agents/project.md"
            project_guidance.parent.mkdir(parents=True, exist_ok=True)
            project_guidance.write_text("# Project\n", encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            self.assertTrue(any(line.endswith("no drift detected") for line in report))
            self.assertIn("profile: minimal", report)

    def test_audit_reports_missing_guidance_drift_and_legacy_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            bug_report = target / ".github/ISSUE_TEMPLATE/bug_report.md"
            content = sync.SCAFFOLD_HASH_PATTERN.sub("", bug_report.read_text(encoding="utf-8"), count=1)
            content = re.sub(r'labels: \["type: bug"\]', "labels: bug", content, count=1)
            bug_report.write_text(content, encoding="utf-8")
            (target / "AGENTS.md").write_text("local edit\n", encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            self.assertTrue(any(line == "info: .agents/project.md not present" for line in report))
            self.assertFalse(any(line.startswith("missing: .agents/project.md") for line in report))
            self.assertTrue(any(line.startswith("drift: AGENTS.md") for line in report))
            self.assertTrue(any("legacy label" in line and "bug_report.md" in line for line in report))

    def test_audit_missing_project_md_is_informational_and_allows_no_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertFalse((target / ".agents/project.md").exists())

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            self.assertIn("info: .agents/project.md not present", report)
            self.assertTrue(any(line.endswith("no drift detected") for line in report))
            self.assertFalse(any(line.startswith(("drift:", "missing:")) for line in report))

    def test_audit_scaffold_status_distinguishes_current_customized_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            manifest = sync.load_manifest(PACK_ROOT)
            bug_asset = next(a for a in manifest.assets if a.path.endswith("bug-report.template.md"))
            source_body = sync.template_body(PACK_ROOT / "files" / bug_asset.path)

            # Verified current scaffold: exactly what the sync path would produce.
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            current_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("outdated scaffold:") for line in current_report))
            self.assertFalse(any(line.startswith("info:") and "bug_report.md" in line for line in current_report))

            # Locally customized scaffold (provenance present but content has since
            # changed) must never be reported as "outdated"; at most informational.
            bug_report = target / bug_asset.scaffold_target
            bug_report.write_text(
                sync.add_source_marker(source_body, bug_asset.path) + "\nSome locally added section.\n",
                encoding="utf-8",
            )
            customized_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("outdated scaffold:") for line in customized_report))
            self.assertTrue(
                any(
                    line.startswith("info:") and "bug_report.md" in line and "customized" in line
                    for line in customized_report
                )
            )
            self.assertFalse(any("bug_report.md" in line for line in customized_report if line.startswith("drift:")))

            # Fully customized/hand-written scaffold with no repo-seed markers at all:
            # no provenance to evaluate, so no warning of any kind.
            bug_report.write_text("# Our own bug report form\n", encoding="utf-8")
            no_provenance_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any("bug_report.md" in line for line in no_provenance_report))

            # Invalid/mismatched provenance: source marker points at the wrong template.
            other_asset = next(a for a in manifest.assets if a.path.endswith("feature-request.template.md"))
            mismatched = sync.add_source_marker(source_body, other_asset.path)
            bug_report.write_text(mismatched, encoding="utf-8")
            mismatched_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("outdated scaffold:") for line in mismatched_report))

    def test_audit_without_a_recorded_profile_reports_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            report = sync.audit_target(PACK_ROOT, target, None)
            self.assertTrue(any("no recorded or requested profile" in line for line in report))
            self.assertEqual(list(target.iterdir()), [])

    def test_cli_audit_reports_without_writing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file())

            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(PACK_ROOT),
                    "--target",
                    str(target),
                    "--audit",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            after = sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("profile: minimal", result.stdout)
            self.assertEqual(before, after)


class BundleAndCliTests(unittest.TestCase):
    def test_first_sync_requires_an_explicit_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            result = subprocess.run(
                [sys.executable, str(SYNC_SCRIPT), "--target", str(target), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("No reusable project profile is recorded", result.stderr)
            self.assertEqual(list(target.iterdir()), [])

    def test_later_sync_reuses_the_recorded_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            first = subprocess.run(
                [sys.executable, str(SYNC_SCRIPT), "--target", str(target), "--profile", "library"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            repeat = subprocess.run(
                [sys.executable, str(SYNC_SCRIPT), "--target", str(target), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(repeat.returncode, 0, repeat.stderr)
            self.assertIn("profile        library", repeat.stdout)

    def test_universal_archive_contains_exact_manifest_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            archive = bundle_builder.build_archive(REPOSITORY_ROOT, output)
            self.assertEqual(archive.name, f"repo-seed-pack-{PACK_VERSION}.zip")
            self.assertEqual(list(output.glob("*.zip")), [archive])
            raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
            expected = {"pack/manifest.json"} | {
                f"pack/{package_file}" for package_file in raw["package_files"]
            } | {
                f"pack/files/{asset['path']}" for asset in raw["assets"]
            }
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()), expected)
                self.assertIn("pack/README.md", bundle.namelist())
                self.assertIn("pack/LICENSE", bundle.namelist())
                self.assertNotIn("README.md", bundle.namelist())
                self.assertNotIn("pack-manifest.json", bundle.namelist())
                self.assertNotIn("scripts/sync-github-labels.py", bundle.namelist())

    def test_extracted_archive_auto_discovers_source_and_syncs_every_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            archive = bundle_builder.build_archive(REPOSITORY_ROOT, temp_root)
            extract_root = temp_root / "extracted"
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extract_root)
            script = extract_root / "pack/files/scripts/sync-docs.py"
            for profile in ("minimal", "library", "app", "game"):
                target = temp_root / f"target-{profile}"
                target.mkdir()
                command = [
                    sys.executable,
                    str(script),
                    "--target",
                    str(target),
                    "--profile",
                    profile,
                    "--scaffold-project-files",
                    "--scaffold-github-templates",
                    "--scaffold-editorconfig",
                ]
                result = subprocess.run(
                    command,
                    cwd=extract_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, f"{profile}: {result.stderr}")
                self.assertTrue((target / "AGENTS.md").is_file())
                self.assertTrue((target / "scripts/sync-docs.py").is_file())
                self.assertTrue((target / ".editorconfig").is_file())
                self.assertTrue((target / ".github/ISSUE_TEMPLATE/feature_request.md").is_file())
                self.assertIn(
                    "<!-- Scaffolded from: docs/templates/readme.template.md -->",
                    (target / "README.md").read_text(encoding="utf-8"),
                )
                self.assertFalse((target / "LICENSE").exists())

    def test_release_builder_rejects_source_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = root / "pack"
            source = pack / "files/linked.md"
            source.parent.mkdir(parents=True)
            outside = root / "outside.md"
            outside.write_text("private\n", encoding="utf-8")
            try:
                source.symlink_to(outside)
            except OSError as ex:
                self.skipTest(f"Symbolic links are unavailable: {ex}")
            with self.assertRaisesRegex(ValueError, "symbolic link|outside"):
                bundle_builder.release_source(pack, "linked.md")

    def test_release_builder_rejects_invalid_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = root / "pack"
            source = pack / "files/docs/templates/readme.template.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Missing metadata\n", encoding="utf-8")
            manifest = {
                "schema_version": 3,
                "pack_version": PACK_VERSION,
                "state_file": ".repo-seed-state.json",
                "profiles": ["minimal"],
                "assets": [
                    {
                        "path": "docs/templates/readme.template.md",
                        "type": "template",
                        "profiles": ["minimal"],
                        "scaffold_group": "project",
                        "scaffold_target": "README.md",
                    }
                ],
            }
            (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata markers"):
                bundle_builder.build_archive(root, root / "dist")

    def test_release_builder_rejects_missing_package_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = root / "pack"
            managed = pack / "files/AGENTS.md"
            managed.parent.mkdir(parents=True)
            managed.write_text("# Managed\n", encoding="utf-8")
            manifest = {
                "schema_version": 3,
                "pack_version": PACK_VERSION,
                "state_file": ".repo-seed-state.json",
                "profiles": ["minimal"],
                "package_files": ["README.md"],
                "assets": [
                    {"path": "AGENTS.md", "type": "managed", "profiles": ["minimal"]}
                ],
            }
            (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "Missing package file"):
                bundle_builder.build_archive(root, root / "dist")

    def test_cli_help_has_only_the_small_interface(self):
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in (
            "--source",
            "--target",
            "--profile",
            "--conventions",
            "--scaffold-project-files",
            "--scaffold-github-templates",
            "--scaffold-editorconfig",
            "--scaffold",
            "--dry-run",
            "--audit",
        ):
            self.assertIn(option, result.stdout)
        for removed in ("--branch-name", "--base-branch", "--exclude", "--skip-editorconfig"):
            self.assertNotIn(removed, result.stdout)

    def test_repository_text_files_are_utf8(self):
        extensions = {".md", ".py", ".json", ".yml", ".yaml", ".template"}
        for path in REPOSITORY_ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix not in extensions:
                continue
            with self.subTest(path=path):
                path.read_text(encoding="utf-8")

    def test_repository_markdown_links_resolve(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for path in REPOSITORY_ROOT.rglob("*.md"):
            if ".git" in path.parts or "templates" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(content):
                if "://" in raw_target or raw_target.startswith("#"):
                    continue
                relative = raw_target.split("#", 1)[0]
                with self.subTest(path=path, target=relative):
                    self.assertTrue((path.parent / relative).resolve().exists())


class GitHubLabelToolTests(unittest.TestCase):
    def test_catalog_matches_issues_guidance(self):
        catalog = github_labels.load_catalog(GITHUB_LABELS_CATALOG)
        names = {label["name"] for label in catalog}
        self.assertEqual(
            names,
            {
                "type: bug",
                "type: feature",
                "type: tech-debt",
                "type: chore",
                "type: decision",
                "type: idea",
                "priority: critical",
                "priority: high",
                "priority: medium",
                "priority: low",
            },
        )
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        for name in names:
            self.assertIn(name, guidance)

    def test_catalog_rejects_duplicate_or_incomplete_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "labels.json"
            path.write_text(
                json.dumps({"labels": [{"name": "type: bug", "description": "x"}, {"name": "type: bug", "description": "y"}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                github_labels.load_catalog(path)

            path.write_text(json.dumps({"labels": [{"name": "type: bug"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "description"):
                github_labels.load_catalog(path)

    def test_audit_reports_missing_drift_and_legacy_labels(self):
        catalog = [
            {"name": "type: bug", "description": "Existing behavior is incorrect.", "color": "d73a4a"},
            {"name": "type: feature", "description": "New capability.", "color": "0e8a16"},
        ]
        hosted = [
            {"name": "type: bug", "description": "wrong description", "color": "d73a4a"},
            {"name": "bug", "description": "legacy", "color": "ffffff"},
            {"name": "component: cli", "description": "project-specific", "color": "ffffff"},
        ]

        findings = github_labels.audit(catalog, hosted)

        self.assertTrue(any(finding == "missing: type: feature" for finding in findings))
        self.assertTrue(any("drift: type: bug" in finding for finding in findings))
        self.assertTrue(any("legacy label: 'bug'" in finding for finding in findings))
        self.assertFalse(any("component: cli" in finding for finding in findings))

    def test_audit_reports_no_findings_for_a_matching_catalog(self):
        catalog = github_labels.load_catalog(GITHUB_LABELS_CATALOG)
        findings = github_labels.audit(catalog, catalog)
        self.assertEqual(findings, [])

    def test_apply_creates_missing_updates_drifted_and_never_deletes(self):
        catalog = [
            {"name": "type: bug", "description": "Existing behavior is incorrect.", "color": "d73a4a"},
            {"name": "type: feature", "description": "New capability.", "color": "0e8a16"},
        ]
        hosted = [
            {"name": "type: bug", "description": "stale description", "color": "d73a4a"},
            {"name": "component: cli", "description": "project-specific", "color": "ffffff"},
            {"name": "enhancement", "description": "legacy", "color": "ffffff"},
        ]

        with mock.patch.object(github_labels, "create_label") as create, mock.patch.object(
            github_labels, "update_label"
        ) as update:
            report = github_labels.apply_catalog("gh", None, catalog, hosted)

        create.assert_called_once_with("gh", None, catalog[1])
        update.assert_called_once_with("gh", None, catalog[0])
        self.assertTrue(any("created: type: feature" in line for line in report))
        self.assertTrue(any("updated: type: bug" in line for line in report))
        self.assertTrue(any("legacy label present, not removed: 'enhancement'" in line for line in report))
        self.assertFalse(any("component: cli" in line for line in report))

    def test_cli_check_and_apply_are_mutually_exclusive(self):
        parser = github_labels.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])
        with self.assertRaises(SystemExit):
            parser.parse_args(["--check", "--apply"])

    def test_main_reports_a_clear_error_without_the_github_cli(self):
        with mock.patch.object(shutil, "which", return_value=None):
            result = github_labels.main(["--check", "--catalog", str(GITHUB_LABELS_CATALOG)])
        self.assertEqual(result, 2)

    def test_cli_help_documents_check_and_apply(self):
        result = subprocess.run(
            [sys.executable, str(GITHUB_LABELS_SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ("--check", "--apply", "--catalog", "--repo"):
            self.assertIn(option, result.stdout)

    def test_normal_sync_does_not_require_the_github_cli_or_network(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            with mock.patch.object(shutil, "which", return_value=None):
                actions = sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertTrue(any(action.action == "copy" for action in actions))
            self.assertTrue((target / "AGENTS.md").is_file())


if __name__ == "__main__":
    unittest.main()
