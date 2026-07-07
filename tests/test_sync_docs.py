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

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPOSITORY_ROOT / "pack"
SYNC_SCRIPT = PACK_ROOT / "files" / "scripts" / "sync-docs.py"
BUILD_SCRIPT = REPOSITORY_ROOT / "scripts" / "build-release-bundle.py"
EXPECTED_PACK_VERSION = "4.0.3"
LEGACY_131_FIXTURES = REPOSITORY_ROOT / "tests" / "fixtures" / "legacy-1.31"
PACK_330_FIXTURES = REPOSITORY_ROOT / "tests" / "fixtures" / "pack-3.3.0"
PACK_341_FIXTURES = REPOSITORY_ROOT / "tests" / "fixtures" / "pack-3.4.1"


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


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = sync.load_manifest(PACK_ROOT)

    def test_manifest_is_versioned_and_complete(self):
        self.assertEqual(self.manifest.schema_version, 2)
        self.assertEqual(self.manifest.pack_version, EXPECTED_PACK_VERSION)
        self.assertEqual(self.manifest.state_file, ".repo-seed-state.json")
        self.assertEqual(self.manifest.profiles, ("minimal", "library", "app", "game", "full"))
        self.assertEqual(self.manifest.package_files, ("README.md", "LICENSE"))
        for package_file in self.manifest.package_files:
            self.assertTrue((PACK_ROOT / package_file).is_file(), package_file)
        for asset in self.manifest.assets:
            self.assertTrue((PACK_ROOT / "files" / Path(asset.path)).is_file(), asset.path)

    def test_versions_are_consistent(self):
        agents = (PACK_ROOT / "files/AGENTS.md").read_text(encoding="utf-8")
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(sync.SCRIPT_VERSION, self.manifest.pack_version)
        self.assertIn(f"**Version**: {self.manifest.pack_version}", agents)
        self.assertIn(f"## {self.manifest.pack_version} -", changelog)

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
        forbidden = {"id", "source", "target", "role", "legacy_targets"}
        for asset in raw["assets"]:
            self.assertFalse(forbidden.intersection(asset), asset)

    def test_migration_metadata_is_versioned_and_protects_project_files(self):
        migration = self.manifest.migration
        self.assertIsNotNone(migration)
        self.assertEqual(migration.legacy_manifest, ".agent-guidelines-manifest.json")
        self.assertIn(".editorconfig", migration.protected_paths)
        self.assertIn(".gitignore", migration.protected_paths)
        self.assertIn(".github/pull_request_template.md", migration.protected_paths)
        retired_assets = {
            asset.path: set(asset.content_hashes)
            for asset in migration.retired_assets
        }
        self.assertEqual(
            retired_assets,
            {
                "docs/templates/gitignore.template": {
                    "0190836cc1deb2681f7b0952fe5be4103be77453d2a360611c0a9c0305310057"
                }
            },
        )
        self.assertEqual(migration.retired_path_sets[0].through_version, "2.0.1")
        retired = {
            path
            for retired_set in migration.retired_path_sets
            for path in retired_set.paths
        }
        self.assertNotIn(".editorconfig", retired)
        self.assertNotIn(".gitignore", retired)
        self.assertNotIn(".github/pull_request_template.md", retired)
        self.assertIn("scripts/sync-agent-guidelines.py", retired)
        scaffold_upgrades = {
            upgrade.legacy_target: upgrade
            for upgrade in migration.scaffold_upgrades
        }
        for legacy_target, expected_hashes in {
            "README.md": {
                "492c961b06ed45642a58ce62500d214ef6716f4134f19cda43e493fa3aa16918",
                "5ce5183514b090fc115125cbe50308f031f76b8667b03cacf44eaed4126800c9",
            },
            "CHANGELOG.md": {
                "3c850e2bfae60d6d59e760d45a89be96859f1d7d59781efaf36e40c67431edf1",
                "c571c769c9da7a6f47fa43bb2cbf3d1a3ca16e1c5bff2cce67fdafd827c0b013",
            },
        }.items():
            self.assertEqual(
                scaffold_upgrades[legacy_target].from_versions,
                ("1.30.0", "1.31.0"),
            )
            self.assertEqual(
                set(scaffold_upgrades[legacy_target].content_hashes),
                expected_hashes,
            )

    def test_invalid_migration_paths_and_hashes_are_rejected(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        unsafe = json.loads(json.dumps(raw["migration"]))
        unsafe["retired_path_sets"][0]["paths"][0] = "../outside"
        with self.assertRaises(ValueError):
            sync.load_migration(unsafe, self.manifest.assets)

        invalid_hash = json.loads(json.dumps(raw["migration"]))
        invalid_hash["scaffold_upgrades"][0]["content_hashes"][0] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            sync.load_migration(invalid_hash, self.manifest.assets)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            bundle_builder.validate_migration(
                invalid_hash,
                {asset.path: asset.asset_type for asset in self.manifest.assets},
            )

        invalid_retired_hash = json.loads(json.dumps(raw["migration"]))
        invalid_retired_hash["retired_assets"][0]["content_hashes"][0] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            sync.load_migration(invalid_retired_hash, self.manifest.assets)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            bundle_builder.validate_migration(
                invalid_retired_hash,
                {asset.path: asset.asset_type for asset in self.manifest.assets},
            )

        scaffold_collision = json.loads(json.dumps(raw["migration"]))
        scaffold_collision["retired_assets"][0]["path"] = "README.md"
        with self.assertRaisesRegex(ValueError, "scaffold"):
            sync.load_migration(scaffold_collision, self.manifest.assets)
        with self.assertRaisesRegex(ValueError, "scaffold"):
            bundle_builder.validate_migration(
                scaffold_collision,
                {asset.path: asset.asset_type for asset in self.manifest.assets},
                {"README.md"},
            )

        protected_collision = json.loads(json.dumps(raw["migration"]))
        protected_collision["protected_paths"].append("AGENTS.md")
        with self.assertRaisesRegex(ValueError, "managed paths cannot also be protected"):
            sync.load_migration(protected_collision, self.manifest.assets)
        with self.assertRaisesRegex(ValueError, "managed paths cannot also be protected"):
            bundle_builder.validate_migration(
                protected_collision,
                {asset.path: asset.asset_type for asset in self.manifest.assets},
            )

    def test_managed_guidance_matches_profile_scope(self):
        all_profiles = {"minimal", "library", "app", "game", "full"}
        library_profiles = {"library", "app", "game", "full"}
        expected = {
            "AGENTS.md": all_profiles,
            "CLAUDE.md": all_profiles,
            "scripts/sync-docs.py": all_profiles,
            ".agents/guidelines/documentation.md": all_profiles,
            ".agents/guidelines/git.md": all_profiles,
            ".agents/guidelines/ci-cd.md": all_profiles,
            ".agents/conventions/csharp.md": library_profiles,
            ".agents/conventions/scripts.md": library_profiles,
            ".agents/conventions/python.md": library_profiles,
            ".agents/conventions/shell.md": library_profiles,
            ".agents/conventions/unity.md": {"game", "full"},
        }
        actual = {
            asset.path: set(asset.profiles)
            for asset in self.manifest.assets
            if asset.asset_type == "managed"
        }
        self.assertEqual(actual, expected)

    def test_profiles_select_only_relevant_project_templates(self):
        common = {
            "changelog.template.md",
            "readme.template.md",
        }
        expected = {
            "minimal": common,
            "library": common | {"architecture.template.md", "tsd.template.md"},
            "app": common
            | {
                "architecture.template.md",
                "fsd.template.md",
                "tsd.template.md",
                "user-guide.template.md",
            },
            "game": common
            | {
                "architecture.template.md",
                "gdd.template.md",
                "tsd.template.md",
            },
            "full": common
            | {
                "architecture.template.md",
                "features.template.md",
                "fsd.template.md",
                "gdd.template.md",
                "tsd.template.md",
                "user-guide.template.md",
            },
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
                "schema_version": 2,
                "pack_version": EXPECTED_PACK_VERSION,
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

    def test_package_files_must_be_safe_and_present(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp)
            managed = pack / "files/AGENTS.md"
            managed.parent.mkdir(parents=True)
            managed.write_text("# Managed\n", encoding="utf-8")
            manifest = {
                "schema_version": 2,
                "pack_version": EXPECTED_PACK_VERSION,
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
                "schema_version": 2,
                "pack_version": EXPECTED_PACK_VERSION,
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

        retired = json.loads(json.dumps(raw))
        retired["migration"]["retired_path_sets"][0]["paths"][0] = (
            ".github/workflows/legacy.yml"
        )
        assert_rejected(retired)


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
            ".agents/conventions/",
            "scripts/sync-docs.py",
        ):
            self.assertIn(required, agents)
        self.assertIn("@AGENTS.md", claude)
        self.assertFalse((PACK_ROOT / "files/.agents/base.md").exists())

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

    def test_update_docs_prefer_the_new_pack_script(self):
        for path in (REPOSITORY_ROOT / "README.md", PACK_ROOT / "README.md"):
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                "python /path/to/extracted/pack/files/scripts/sync-docs.py",
                content,
            )
            self.assertNotIn(
                "python scripts/sync-docs.py \\\n  --source /path/to/extracted/pack",
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


class SyncBehaviorTests(unittest.TestCase):
    def test_legacy_131_migration_upgrades_scaffolds_and_preserves_project_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in ("README.md", "CHANGELOG.md", "FEATURES.md"):
                shutil.copyfile(LEGACY_131_FIXTURES / name, target / name)
            legacy_files = {
                ".agent-guidelines-version": "1.31.0\n",
                "scripts/sync-agent-guidelines.py": "legacy sync script\n",
                ".editorconfig": "root = false\n",
                ".gitignore": "project-specific-output/\n",
                ".github/pull_request_template.md": "project pull request template\n",
            }
            for relative, content in legacy_files.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            conflicts = target / ".agent-guidelines-conflicts"
            conflicts.mkdir()
            (conflicts / "saved-conflict.md").write_text("review me\n", encoding="utf-8")
            hashes = {
                relative: sync.file_hash(target / relative)
                for relative in legacy_files
            }
            (target / ".agent-guidelines-manifest.json").write_text(
                json.dumps(
                    {
                        "files": hashes,
                        "pack_version": "1.31.0",
                        "sync_script": "sync-agent-guidelines.py",
                        "sync_script_version": "1.7.0",
                    }
                ),
                encoding="utf-8",
            )

            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "app",
                scaffold_project_files=True,
            )

            self.assertFalse((target / ".agent-guidelines-version").exists())
            self.assertFalse((target / ".agent-guidelines-manifest.json").exists())
            self.assertFalse((target / "scripts/sync-agent-guidelines.py").exists())
            self.assertTrue((target / "FEATURES.md").is_file())
            self.assertFalse((target / "docs/project/features.md").exists())
            self.assertIn(
                "Scaffolded content SHA-256:",
                (target / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Scaffolded content SHA-256:",
                (target / "CHANGELOG.md").read_text(encoding="utf-8"),
            )
            for relative in (".editorconfig", ".gitignore", ".github/pull_request_template.md"):
                content = legacy_files[relative]
                self.assertEqual((target / relative).read_text(encoding="utf-8"), content)
                self.assertTrue(
                    any(
                        action.action == "preserve"
                        and action.path == relative
                        and "project-owned" in action.detail
                        for action in actions
                    )
                )
            self.assertTrue((conflicts / "saved-conflict.md").is_file())
            self.assertEqual(
                {action.action for action in actions if action.path in {"README.md", "CHANGELOG.md", "FEATURES.md"}},
                {"upgrade"},
            )

    def test_legacy_migration_dry_run_reports_hash_safe_removals(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            version_file = target / ".agent-guidelines-version"
            version_file.write_text("1.31.0\n", encoding="utf-8")
            old_script = target / "scripts/sync-agent-guidelines.py"
            old_script.parent.mkdir()
            old_script.write_text("legacy\n", encoding="utf-8")
            state = target / ".agent-guidelines-manifest.json"
            state.write_text(
                json.dumps(
                    {
                        "pack_version": "1.31.0",
                        "files": {
                            ".agent-guidelines-version": sync.file_hash(version_file),
                            "scripts/sync-agent-guidelines.py": sync.file_hash(old_script),
                        },
                    }
                ),
                encoding="utf-8",
            )

            actions = sync.synchronize(PACK_ROOT, target, "minimal", dry_run=True)

            self.assertTrue(version_file.is_file())
            self.assertTrue(old_script.is_file())
            self.assertTrue(state.is_file())
            removed = {action.path for action in actions if action.action == "remove"}
            self.assertEqual(
                removed,
                {
                    ".agent-guidelines-version",
                    ".agent-guidelines-manifest.json",
                    "scripts/sync-agent-guidelines.py",
                },
            )

    def test_legacy_version_file_missing_from_manifest_is_still_retired(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            version_file = target / ".agent-guidelines-version"
            version_file.write_text("1.31.0\n", encoding="utf-8")
            state = target / ".agent-guidelines-manifest.json"
            state.write_text(
                json.dumps({"pack_version": "1.31.0", "files": {}}),
                encoding="utf-8",
            )

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertFalse(version_file.exists())
            self.assertFalse(state.exists())
            removed = {action.path for action in actions if action.action == "remove"}
            self.assertIn(".agent-guidelines-version", removed)
            self.assertIn(".agent-guidelines-manifest.json", removed)

    def test_modified_or_untracked_legacy_files_are_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            version_file = target / ".agent-guidelines-version"
            version_file.write_text("1.31.0\n", encoding="utf-8")
            modified = target / "docs/coding-conventions-csharp.md"
            modified.parent.mkdir(parents=True)
            modified.write_text("local changes\n", encoding="utf-8")
            untracked = target / "docs/readme-template.md"
            untracked.write_text("project-owned template\n", encoding="utf-8")
            state = target / ".agent-guidelines-manifest.json"
            state.write_text(
                json.dumps(
                    {
                        "pack_version": "1.31.0",
                        "files": {
                            ".agent-guidelines-version": sync.file_hash(version_file),
                            "docs/coding-conventions-csharp.md": "0" * 64,
                        },
                    }
                ),
                encoding="utf-8",
            )

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertTrue(modified.is_file())
            self.assertTrue(untracked.is_file())
            self.assertTrue(state.is_file())
            preserved = {action.path for action in actions if action.action == "preserve"}
            self.assertIn("docs/coding-conventions-csharp.md", preserved)
            self.assertIn("docs/readme-template.md", preserved)
            self.assertIn(".agent-guidelines-manifest.json", preserved)

    def test_newer_unknown_legacy_version_is_not_retired(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            version_file = target / ".agent-guidelines-version"
            version_file.write_text("2.0.2\n", encoding="utf-8")
            state = target / ".agent-guidelines-manifest.json"
            state.write_text(
                json.dumps(
                    {
                        "pack_version": "2.0.2",
                        "files": {
                            ".agent-guidelines-version": sync.file_hash(version_file),
                        },
                    }
                ),
                encoding="utf-8",
            )

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertTrue(version_file.is_file())
            self.assertTrue(state.is_file())
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == ".agent-guidelines-manifest.json"
                    and "newer than supported" in action.detail
                    for action in actions
                )
            )

    def test_verified_scaffold_is_upgraded_but_local_changes_are_preserved(self):
        asset = next(
            asset
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.path.endswith("bug-report.template.md")
        )
        source = PACK_ROOT / "files" / asset.path
        old_render = sync.add_source_path_marker(sync.template_body(source), asset.path)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            issue = target / asset.scaffold_target
            issue.parent.mkdir(parents=True)
            issue.write_text(old_render, encoding="utf-8")

            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )

            self.assertTrue(any(action.action == "upgrade" for action in actions))
            self.assertIn("Scaffolded content SHA-256:", issue.read_text(encoding="utf-8"))
            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )
            self.assertTrue(
                any(action.action == "skip" and action.path == asset.scaffold_target for action in actions)
            )
            issue.write_text(issue.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )
            self.assertTrue(
                any(action.action == "preserve" and action.path == asset.scaffold_target for action in actions)
            )

    def test_version_2_provenance_marker_allows_untouched_scaffold_upgrade(self):
        asset = next(
            asset
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.path.endswith("bug-report.template.md")
        )
        source = PACK_ROOT / "files" / asset.path
        legacy_body = sync.template_body(source).rstrip()
        legacy_marker = (
            '<!-- repo-seed-template id="github-bug-template" '
            f'sha256="{sync.content_hash(legacy_body)}" -->'
        )
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            issue = target / asset.scaffold_target
            issue.parent.mkdir(parents=True)
            issue.write_text(f"{legacy_body}\n\n{legacy_marker}\n", encoding="utf-8")

            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )

            self.assertTrue(
                any(action.action == "upgrade" and action.path == asset.scaffold_target for action in actions)
            )
            content = issue.read_text(encoding="utf-8")
            self.assertIn(f"<!-- Scaffolded from: {asset.path} -->", content)
            self.assertIn("Scaffolded content SHA-256:", content)
            self.assertNotIn("repo-seed-template id=", content)

    def test_version_2_provenance_from_wrong_template_is_preserved(self):
        asset = next(
            asset
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.path.endswith("bug-report.template.md")
        )
        legacy_body = sync.template_body(PACK_ROOT / "files" / asset.path).rstrip()
        wrong_marker = (
            '<!-- repo-seed-template id="github-feature-template" '
            f'sha256="{sync.content_hash(legacy_body)}" -->'
        )
        original = f"{legacy_body}\n\n{wrong_marker}\n"
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            issue = target / asset.scaffold_target
            issue.parent.mkdir(parents=True)
            issue.write_text(original, encoding="utf-8")

            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )

            self.assertEqual(issue.read_text(encoding="utf-8"), original)
            self.assertTrue(
                any(action.action == "preserve" and action.path == asset.scaffold_target for action in actions)
            )

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
            self.assertFalse((target / ".agent-guidelines-manifest.json").exists())
            self.assertFalse((target / ".agent-guidelines-conflicts").exists())
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "LICENSE").exists())

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
                if action.path in {
                    asset.path
                    for asset in sync.assets_for_profile(sync.load_manifest(PACK_ROOT), "minimal")
                }
            ]
            self.assertTrue(managed)
            self.assertEqual({action.action for action in managed}, {"unchanged"})
            self.assertTrue(
                any(
                    action.action == "unchanged"
                    and action.path == ".repo-seed-state.json"
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

    def test_project_scaffolding_excludes_editorconfig(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", scaffold_project_files=True)
            expected = {
                "README.md",
                "CHANGELOG.md",
                "docs/project/architecture.md",
                "docs/project/user-guide.md",
                "docs/project/fsd.md",
            }
            for relative in expected:
                self.assertTrue((target / relative).is_file(), relative)
            self.assertFalse((target / ".editorconfig").exists())
            self.assertFalse((target / ".gitignore").exists())
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("<!-- Scaffolded from: docs/templates/readme.template.md -->", readme)
            self.assertNotIn(sync.TEMPLATE_METADATA_START, readme)

    def test_each_project_profile_scaffolds_only_its_living_documents(self):
        expected = {
            "minimal": {"README.md", "CHANGELOG.md"},
            "library": {
                "README.md",
                "CHANGELOG.md",
                "docs/project/architecture.md",
            },
            "app": {
                "README.md",
                "CHANGELOG.md",
                "docs/project/architecture.md",
                "docs/project/fsd.md",
                "docs/project/user-guide.md",
            },
            "game": {
                "README.md",
                "CHANGELOG.md",
                "docs/project/architecture.md",
                "docs/project/gdd.md",
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for profile, expected_paths in expected.items():
                target = root / profile
                target.mkdir()
                sync.synchronize(
                    PACK_ROOT,
                    target,
                    profile,
                    scaffold_project_files=True,
                )
                actual = {
                    path.relative_to(target).as_posix()
                    for path in target.rglob("*")
                    if path.is_file()
                    and (
                        path.name in {"README.md", "CHANGELOG.md"}
                        or "docs/project" in path.as_posix()
                    )
                }
                self.assertEqual(actual, expected_paths, profile)

    def test_editorconfig_scaffolding_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_editorconfig=True)
            content = (target / ".editorconfig").read_text(encoding="utf-8")
            self.assertIn("root = true", content)
            self.assertNotIn(sync.TEMPLATE_METADATA_START, content)

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
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == ".gitignore"
                    and "project-owned" in action.detail
                    for action in actions
                )
            )

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
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
                dry_run=True,
            )
            self.assertTrue(actions)
            self.assertEqual(list(target.iterdir()), [])

    def test_full_profile_rejects_project_scaffolding_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            with self.assertRaisesRegex(ValueError, "reference catalog"):
                sync.synchronize(
                    PACK_ROOT,
                    target,
                    "full",
                    scaffold_project_files=True,
                )
            self.assertEqual(list(target.iterdir()), [])

    def test_profile_reduction_removes_unchanged_stale_managed_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            unity = target / ".agents/conventions/unity.md"
            gdd = target / "docs/templates/gdd.template.md"
            self.assertTrue(unity.is_file())
            self.assertTrue(gdd.is_file())
            actions = sync.synchronize(PACK_ROOT, target, "app")

            self.assertFalse(unity.exists())
            self.assertFalse(gdd.exists())
            removed = {action.path for action in actions if action.action == "remove"}
            self.assertIn(".agents/conventions/unity.md", removed)
            self.assertIn("docs/templates/gdd.template.md", removed)
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["profile"], "app")
            self.assertEqual(state["tombstones"], {})
            self.assertNotIn(".agents/conventions/unity.md", state["managed_files"])
            self.assertNotIn("docs/templates/gdd.template.md", state["managed_files"])

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
            expected = {
                ci: ci.read_bytes(),
                release: release.read_bytes(),
            }

            sync.synchronize(
                PACK_ROOT,
                target,
                "full",
                scaffold_github_templates=True,
            )
            actions = sync.synchronize(
                PACK_ROOT,
                target,
                "minimal",
                scaffold_github_templates=True,
            )

            for path, content in expected.items():
                self.assertEqual(path.read_bytes(), content)
            self.assertFalse(
                any(
                    action.path.startswith(".github/workflows/")
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
            )
            project_tsd = target / "docs/project/tsd.md"
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

    def test_modified_stale_asset_remains_tombstoned_until_safe_to_remove(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            gdd = target / "docs/templates/gdd.template.md"
            original = (PACK_ROOT / "files/docs/templates/gdd.template.md").read_bytes()
            gdd.write_text("local changes\n", encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app")

            self.assertTrue(gdd.is_file())
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == "docs/templates/gdd.template.md"
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
                    action.action == "remove"
                    and action.path == "docs/templates/gdd.template.md"
                    for action in actions
                )
            )

            sync.synchronize(PACK_ROOT, target, "app")
            self.assertFalse(gdd.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("docs/templates/gdd.template.md", state["tombstones"])

    def test_profile_expansion_reactivates_tombstoned_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            gdd = target / "docs/templates/gdd.template.md"
            gdd.write_text("local changes\n", encoding="utf-8")
            sync.synchronize(PACK_ROOT, target, "app")

            actions = sync.synchronize(PACK_ROOT, target, "full")

            self.assertEqual(
                gdd.read_bytes(),
                (PACK_ROOT / "files/docs/templates/gdd.template.md").read_bytes(),
            )
            self.assertTrue(
                any(
                    action.action == "copy"
                    and action.path == "docs/templates/gdd.template.md"
                    for action in actions
                )
            )
            self.assertFalse(
                any(
                    action.action in {"remove", "preserve"}
                    and action.path == "docs/templates/gdd.template.md"
                    for action in actions
                )
            )
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertIn("docs/templates/gdd.template.md", state["managed_files"])
            self.assertNotIn("docs/templates/gdd.template.md", state["tombstones"])

    def test_state_bootstrap_prunes_known_current_assets_but_not_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            gdd = target / "docs/templates/gdd.template.md"
            (target / ".repo-seed-state.json").unlink()
            unknown = target / "project-owned.txt"
            unknown.write_text("keep\n", encoding="utf-8")

            sync.synchronize(PACK_ROOT, target, "app")

            self.assertFalse((target / ".agents/conventions/unity.md").exists())
            self.assertFalse((target / "docs/templates/gdd.template.md").exists())
            self.assertEqual(unknown.read_text(encoding="utf-8"), "keep\n")

    def test_state_releases_reclassified_project_owned_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            editorconfig = target / ".editorconfig"
            editorconfig.write_text("root = false\n", encoding="utf-8")
            state_path = target / ".repo-seed-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["managed_files"][".editorconfig"] = sync.file_hash(editorconfig)
            state_path.write_text(json.dumps(state), encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertEqual(editorconfig.read_text(encoding="utf-8"), "root = false\n")
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == ".editorconfig"
                    and "project-owned" in action.detail
                    for action in actions
                )
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn(".editorconfig", state["managed_files"])
            self.assertNotIn(".editorconfig", state["tombstones"])

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
                "schema_version": 1,
                "pack_version": "4.0.0",
                "profile": "minimal",
                "managed_files": {
                    "src/important.py": sync.managed_file_hash(important),
                },
                "tombstones": {},
            }
            (target / ".repo-seed-state.json").write_text(
                json.dumps(state),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unknown pack-owned path"):
                sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertEqual(important.read_text(encoding="utf-8"), "important = True\n")
            self.assertFalse((target / "AGENTS.md").exists())

    def test_known_retired_asset_is_removed_only_with_a_recognized_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            retired = target / "docs/templates/gitignore.template"
            retired.parent.mkdir(parents=True)
            shutil.copy2(PACK_330_FIXTURES / "gitignore.template", retired)
            expected_hash = sync.managed_file_hash(retired)
            self.assertEqual(
                expected_hash,
                "0190836cc1deb2681f7b0952fe5be4103be77453d2a360611c0a9c0305310057",
            )
            state = {
                "schema_version": 1,
                "pack_version": "3.3.0",
                "profile": "minimal",
                "managed_files": {
                    "docs/templates/gitignore.template": expected_hash,
                },
                "tombstones": {},
            }
            state_path = target / ".repo-seed-state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertFalse(retired.exists())
            self.assertTrue(
                any(
                    action.action == "remove"
                    and action.path == "docs/templates/gitignore.template"
                    for action in actions
                )
            )

            retired.parent.mkdir(parents=True, exist_ok=True)
            retired.write_text("project content\n", encoding="utf-8")
            state["managed_files"]["docs/templates/gitignore.template"] = (
                sync.managed_file_hash(retired)
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not recognized for retired asset"):
                sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertEqual(retired.read_text(encoding="utf-8"), "project content\n")

    def test_new_pack_script_upgrades_a_3_4_1_target(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            features_reference = target / "docs/templates/features.template.md"
            features_reference.parent.mkdir(parents=True)
            shutil.copy2(PACK_341_FIXTURES / "features.template.md", features_reference)
            copied_script = target / "scripts/sync-docs.py"
            copied_script.parent.mkdir(parents=True)
            copied_script.write_text("# version 3.4.1 script placeholder\n", encoding="utf-8")
            live_documents = {
                "docs/project/features.md": "# Project capabilities\n",
                "docs/project/tsd.md": "# Existing project technical document\n",
            }
            for relative, content in live_documents.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            state = {
                "schema_version": 1,
                "pack_version": "3.4.1",
                "profile": "app",
                "managed_files": {
                    "docs/templates/features.template.md": sync.managed_file_hash(
                        features_reference
                    ),
                    "scripts/sync-docs.py": sync.managed_file_hash(copied_script),
                },
                "tombstones": {},
            }
            state_path = target / ".repo-seed-state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--target",
                    str(target),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("profile        app", result.stdout)
            self.assertFalse(features_reference.exists())
            self.assertEqual(copied_script.read_bytes(), SYNC_SCRIPT.read_bytes())
            for relative, content in live_documents.items():
                self.assertEqual((target / relative).read_text(encoding="utf-8"), content)
            updated_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_state["pack_version"], EXPECTED_PACK_VERSION)
            self.assertEqual(updated_state["profile"], "app")

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


class BundleAndCliTests(unittest.TestCase):
    def test_first_sync_requires_an_explicit_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--target",
                    str(target),
                    "--dry-run",
                ],
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
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--target",
                    str(target),
                    "--profile",
                    "library",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            repeat = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--target",
                    str(target),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(repeat.returncode, 0, repeat.stderr)
            self.assertIn("profile        library", repeat.stdout)

    def test_recorded_full_profile_is_not_implicitly_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--target",
                    str(target),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("pass --profile", result.stderr)

    def test_universal_archive_contains_exact_manifest_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            archive = bundle_builder.build_archive(REPOSITORY_ROOT, output)
            self.assertEqual(archive.name, f"repo-seed-pack-{EXPECTED_PACK_VERSION}.zip")
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

    def test_extracted_archive_auto_discovers_source_and_syncs_every_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            archive = bundle_builder.build_archive(REPOSITORY_ROOT, temp_root)
            extract_root = temp_root / "extracted"
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extract_root)
            script = extract_root / "pack/files/scripts/sync-docs.py"
            for profile in ("minimal", "library", "app", "game", "full"):
                target = temp_root / f"target-{profile}"
                target.mkdir()
                command = [
                    sys.executable,
                    str(script),
                    "--target",
                    str(target),
                    "--profile",
                    profile,
                    "--scaffold-github-templates",
                    "--scaffold-editorconfig",
                ]
                if profile != "full":
                    command.append("--scaffold-project-files")
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
                if profile == "full":
                    self.assertFalse((target / "README.md").exists())
                else:
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
                "schema_version": 2,
                "pack_version": EXPECTED_PACK_VERSION,
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
                "schema_version": 2,
                "pack_version": EXPECTED_PACK_VERSION,
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
            "--scaffold-project-files",
            "--scaffold-github-templates",
            "--scaffold-editorconfig",
            "--dry-run",
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


if __name__ == "__main__":
    unittest.main()
