import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPOSITORY_ROOT / "scripts" / "sync-agent-guidelines.py"
BUILD_SCRIPT = REPOSITORY_ROOT / "scripts" / "build-release-bundles.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sync = load_module("sync_agent_guidelines", SYNC_SCRIPT)
bundles = load_module("build_release_bundles", BUILD_SCRIPT)


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = sync.load_pack_manifest(REPOSITORY_ROOT)

    def test_manifest_is_versioned_and_all_sources_exist(self):
        self.assertEqual(self.manifest.pack_version, "2.0.0")
        self.assertEqual(self.manifest.schema_version, 1)
        self.assertEqual(
            (REPOSITORY_ROOT / ".agent-guidelines-version").read_text(encoding="utf-8").strip(),
            self.manifest.pack_version,
        )
        for asset in self.manifest.assets:
            with self.subTest(asset=asset.asset_id):
                self.assertTrue((REPOSITORY_ROOT / asset.source).is_file())

    def test_repo_only_documents_are_not_sync_sources(self):
        sources = {asset.source for asset in self.manifest.assets}
        self.assertFalse({"README.md", "CHANGELOG.md", "AGENTS.md", "CLAUDE.md"} & sources)

    def test_profiles_have_only_their_document_templates(self):
        expected_project_templates = {
            "minimal": {"readme-template", "changelog-template"},
            "library": {"readme-template", "changelog-template"},
            "app": {
                "readme-template",
                "changelog-template",
                "features-template",
                "architecture-template",
                "user-guide-template",
                "fsd-template",
                "tsd-template",
            },
            "game": {"readme-template", "changelog-template", "features-template", "gdd-template"},
            "full": {
                "readme-template",
                "changelog-template",
                "features-template",
                "architecture-template",
                "user-guide-template",
                "fsd-template",
                "tsd-template",
                "gdd-template",
            },
        }
        for profile, expected in expected_project_templates.items():
            selected = sync.assets_for_profile(self.manifest, profile)
            actual = {
                asset.asset_id
                for asset in selected
                if asset.role == "template" and asset.scaffold_group == "project"
            }
            self.assertEqual(actual, expected)

    def test_templates_sync_without_renaming(self):
        templates = [asset for asset in self.manifest.assets if asset.role == "template"]
        for asset in templates:
            with self.subTest(asset=asset.asset_id):
                self.assertEqual(asset.source, asset.target)
        github_sources = {asset.source for asset in templates if asset.scaffold_group == "github"}
        self.assertEqual(
            github_sources,
            {
                "docs/templates/.github/bug-report.template.md",
                "docs/templates/.github/feature-request.template.md",
            },
        )

    def test_manifest_rejects_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data = {
                "schema_version": 1,
                "pack_version": "2.0.0",
                "default_profile": "minimal",
                "profiles": ["minimal"],
                "assets": [
                    {
                        "id": "unsafe",
                        "source": "../outside.md",
                        "target": "AGENTS.md",
                        "role": "managed",
                        "profiles": ["minimal"],
                    }
                ],
            }
            (root / "pack-manifest.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsafe relative path"):
                sync.load_pack_manifest(root, validate_sources=False)

    def test_manifest_rejects_missing_and_invalid_template_sources(self):
        base = {
            "schema_version": 1,
            "pack_version": "2.0.0",
            "default_profile": "minimal",
            "profiles": ["minimal"],
            "assets": [
                {
                    "id": "template",
                    "source": "docs/templates/example.template.md",
                    "target": "docs/templates/example.template.md",
                    "role": "template",
                    "profiles": ["minimal"],
                    "scaffold_group": "project",
                    "scaffold_target": "docs/project/example.md",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pack-manifest.json").write_text(json.dumps(base), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source does not exist"):
                sync.load_pack_manifest(root)

            source = root / "docs/templates/example.template.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Missing markers\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata markers"):
                sync.load_pack_manifest(root)


class AgentGuidanceTests(unittest.TestCase):
    def test_root_agent_file_is_concise_and_self_sufficient(self):
        content = (REPOSITORY_ROOT / "pack/AGENTS.md").read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertGreaterEqual(len(lines), 150)
        self.assertLessEqual(len(lines), 250)
        self.assertIn("docs/project/", content)
        self.assertIn("docs/templates/", content)
        self.assertIn(".agents/project.md", content)
        self.assertIn(".agents/guidelines/documentation.md", content)
        self.assertIn(".agents/guidelines/git.md", content)
        self.assertNotIn(".agents/base.md", content)

    def test_every_markdown_asset_is_labeled(self):
        manifest = sync.load_pack_manifest(REPOSITORY_ROOT)
        for asset in manifest.assets:
            if asset.source.endswith(".md"):
                with self.subTest(asset=asset.asset_id):
                    content = (REPOSITORY_ROOT / asset.source).read_text(encoding="utf-8")
                    self.assertIn("Document role", content)

    def test_every_repository_markdown_file_is_labeled(self):
        for path in REPOSITORY_ROOT.rglob("*.md"):
            if ".git" in path.parts or ".agent-guidelines-conflicts" in path.parts:
                continue
            with self.subTest(path=path.relative_to(REPOSITORY_ROOT)):
                self.assertIn("Document role", path.read_text(encoding="utf-8"))

    def test_repo_document_links_resolve(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        paths = [
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "AGENTS.md",
            *sorted((REPOSITORY_ROOT / "docs/project").glob("*.md")),
        ]
        for path in paths:
            for link in link_pattern.findall(path.read_text(encoding="utf-8")):
                if "://" in link or link.startswith("#"):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(path=path.name, link=link):
                    self.assertTrue(target.exists())

    def test_repository_text_files_are_utf8(self):
        extensions = {".md", ".py", ".json", ".yml", ".yaml"}
        for path in REPOSITORY_ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix in extensions or path.name == ".agent-guidelines-version":
                with self.subTest(path=path.relative_to(REPOSITORY_ROOT)):
                    path.read_text(encoding="utf-8")


class TemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = sync.load_pack_manifest(REPOSITORY_ROOT)
        cls.assets = {asset.asset_id: asset for asset in cls.manifest.assets}

    def test_render_strips_labels_and_adds_hash_provenance(self):
        asset = self.assets["features-template"]
        rendered = sync.render_template(asset, REPOSITORY_ROOT / asset.source)
        self.assertTrue(rendered.startswith("# Features"))
        self.assertNotIn(sync.TEMPLATE_METADATA_START, rendered)
        self.assertNotIn("Document role", rendered)
        self.assertRegex(rendered, sync.PROVENANCE_PATTERN)

    def test_github_scaffold_preserves_frontmatter(self):
        asset = self.assets["github-bug-template"]
        rendered = sync.render_template(asset, REPOSITORY_ROOT / asset.source)
        self.assertTrue(rendered.startswith("---\nname: Bug report"))

    def test_scaffold_never_overwrites_existing_file(self):
        asset = self.assets["features-template"]
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            target = target_root / asset.scaffold_target
            target.parent.mkdir(parents=True)
            target.write_text("# Local\n", encoding="utf-8")
            action = sync.scaffold_asset(REPOSITORY_ROOT, target_root, asset, dry_run=False)
            self.assertEqual(action.action, "skipped")
            self.assertEqual(target.read_text(encoding="utf-8"), "# Local\n")

    def test_template_drift_is_reported_without_modifying_live_doc(self):
        asset = self.assets["features-template"]
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            sync.scaffold_asset(REPOSITORY_ROOT, target_root, asset, dry_run=False)
            target = target_root / asset.scaffold_target
            content = target.read_text(encoding="utf-8")
            content = re.sub(r'sha256="[0-9a-f]{64}"', f'sha256="{"0" * 64}"', content)
            target.write_text(content, encoding="utf-8")
            before = target.read_bytes()
            action = sync.template_drift_action(REPOSITORY_ROOT, target_root, asset)
            self.assertEqual(action.action, "review-needed")
            self.assertEqual(target.read_bytes(), before)


class ManagedFileTests(unittest.TestCase):
    def test_preferred_base_branch_uses_develop_before_main(self):
        existing = {"develop", "main"}
        with patch.object(sync, "branch_exists", side_effect=lambda _, name: name in existing):
            with patch.object(sync, "remote_branch_exists", return_value=False):
                self.assertEqual(sync.preferred_base_branch(REPOSITORY_ROOT), "develop")

    def test_preferred_base_branch_falls_back_to_main(self):
        with patch.object(sync, "branch_exists", side_effect=lambda _, name: name == "main"):
            with patch.object(sync, "remote_branch_exists", return_value=False):
                self.assertEqual(sync.preferred_base_branch(REPOSITORY_ROOT), "main")

    def test_local_managed_edit_creates_conflict(self):
        manifest = sync.load_pack_manifest(REPOSITORY_ROOT)
        asset = next(asset for asset in manifest.assets if asset.asset_id == "agent-instructions")
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            target = target_root / asset.target
            target.write_text("# Local rules\n", encoding="utf-8")
            action = sync.sync_asset(
                REPOSITORY_ROOT,
                target_root,
                asset,
                previous_hashes={},
                new_hashes={},
                dry_run=False,
            )
            self.assertEqual(action.action, "conflict")
            self.assertEqual(target.read_text(encoding="utf-8"), "# Local rules\n")
            self.assertTrue((target_root / sync.CONFLICT_DIR).is_dir())

    def test_obsolete_unchanged_file_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            obsolete = target_root / "docs/old-template.md"
            obsolete.parent.mkdir(parents=True)
            obsolete.write_text("# Old\n", encoding="utf-8")
            actions = sync.prune_obsolete_files(
                target_root,
                {"docs/old-template.md": sync.file_hash(obsolete)},
                selected_targets=set(),
                dry_run=False,
            )
            self.assertEqual(actions[0].action, "removed")
            self.assertFalse(obsolete.exists())

    def test_obsolete_local_edit_and_root_document_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            local = target_root / "docs/old-template.md"
            local.parent.mkdir(parents=True)
            local.write_text("# Local\n", encoding="utf-8")
            readme = target_root / "README.md"
            readme.write_text("# Project\n", encoding="utf-8")
            actions = sync.prune_obsolete_files(
                target_root,
                {
                    "docs/old-template.md": "not-current",
                    "README.md": sync.file_hash(readme),
                },
                selected_targets=set(),
                dry_run=False,
            )
            self.assertEqual({action.action for action in actions}, {"preserved"})
            self.assertTrue(local.exists())
            self.assertTrue(readme.exists())

    def test_cli_dry_run_does_not_write_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(REPOSITORY_ROOT),
                    "--target",
                    str(target_root),
                    "--profile",
                    "minimal",
                    "--no-branch",
                    "--dry-run",
                    "--scaffold-project-files",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(list(target_root.iterdir()), [])

    def test_cli_migrates_legacy_paths_and_protects_root_docs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            legacy = target_root / "docs/coding-conventions-csharp.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("# Legacy convention\n", encoding="utf-8")
            readme = target_root / "README.md"
            readme.write_text("# Existing project\n", encoding="utf-8")
            state = {
                "pack_version": "1.31.0",
                "files": {
                    "docs/coding-conventions-csharp.md": sync.file_hash(legacy),
                    "README.md": sync.file_hash(readme),
                },
            }
            (target_root / sync.STATE_FILE).write_text(json.dumps(state), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(REPOSITORY_ROOT),
                    "--target",
                    str(target_root),
                    "--profile",
                    "library",
                    "--no-branch",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(legacy.exists())
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Existing project\n")
            self.assertTrue((target_root / ".agents/conventions/csharp.md").is_file())

    def test_excluded_managed_file_is_not_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            editorconfig = target_root / ".editorconfig"
            editorconfig.write_text("root = true\n", encoding="utf-8")
            state = {
                "files": {
                    ".editorconfig": sync.file_hash(editorconfig),
                }
            }
            (target_root / sync.STATE_FILE).write_text(json.dumps(state), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_SCRIPT),
                    "--source",
                    str(REPOSITORY_ROOT),
                    "--target",
                    str(target_root),
                    "--profile",
                    "minimal",
                    "--no-branch",
                    "--skip-editorconfig",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(editorconfig.read_text(encoding="utf-8"), "root = true\n")


class BundleSmokeTests(unittest.TestCase):
    def test_every_profile_bundle_syncs_into_an_empty_target(self):
        expected_docs = {
            "minimal": set(),
            "library": set(),
            "app": {"features.md", "architecture.md", "user-guide.md", "fsd.md", "tsd.md"},
            "game": {"features.md", "gdd.md"},
            "full": {
                "features.md",
                "architecture.md",
                "user-guide.md",
                "fsd.md",
                "tsd.md",
                "gdd.md",
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            archive_dir = temp_root / "archives"
            archives = bundles.build_archives(REPOSITORY_ROOT, archive_dir)
            self.assertEqual(len(archives), 5)

            for archive in archives:
                profile = archive.stem.split("_")[-2]
                extract_root = temp_root / f"bundle-{profile}"
                target_root = temp_root / f"target-{profile}"
                target_root.mkdir()
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(extract_root)

                bundle_manifest = sync.load_pack_manifest(extract_root)
                self.assertEqual(bundle_manifest.profiles, (profile,))
                self.assertEqual(bundle_manifest.default_profile, profile)

                result = subprocess.run(
                    [
                        sys.executable,
                        str(extract_root / "scripts/sync-agent-guidelines.py"),
                        "--source",
                        str(extract_root),
                        "--target",
                        str(target_root),
                        "--no-branch",
                        "--scaffold-project-files",
                        "--scaffold-github-templates",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((target_root / "AGENTS.md").is_file())
                self.assertFalse((target_root / ".agents/base.md").exists())
                self.assertTrue((target_root / "README.md").is_file())
                self.assertTrue((target_root / "CHANGELOG.md").is_file())
                self.assertTrue((target_root / ".github/ISSUE_TEMPLATE/bug_report.md").is_file())
                actual_docs = {
                    path.name
                    for path in (target_root / "docs/project").glob("*.md")
                } if (target_root / "docs/project").exists() else set()
                self.assertEqual(actual_docs, expected_docs[profile])


if __name__ == "__main__":
    unittest.main()
