from __future__ import annotations

import importlib.util
import json
import re
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
        self.assertEqual(self.manifest.schema_version, 1)
        self.assertEqual(self.manifest.pack_version, "3.2.1")
        self.assertEqual(self.manifest.default_profile, "full")
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
            "gitignore.template",
            "readme.template.md",
        }
        expected = {
            "minimal": common,
            "library": common,
            "app": common
            | {
                "architecture.template.md",
                "features.template.md",
                "fsd.template.md",
                "tsd.template.md",
                "user-guide.template.md",
            },
            "game": common | {"features.template.md", "gdd.template.md"},
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
                if asset.asset_type == "template" and asset.scaffold_group == "project"
            }
            self.assertEqual(actual_names, expected_names, profile)

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
                "schema_version": 1,
                "pack_version": "3.2.1",
                "default_profile": "minimal",
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
                "schema_version": 1,
                "pack_version": "3.2.1",
                "default_profile": "minimal",
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
                "schema_version": 1,
                "pack_version": "3.2.1",
                "default_profile": "minimal",
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

    def test_every_template_has_valid_metadata_and_a_body(self):
        for asset in sync.load_manifest(PACK_ROOT).assets:
            if asset.asset_type == "template":
                body = sync.template_body(PACK_ROOT / "files" / asset.path)
                self.assertTrue(body.strip(), asset.path)
                self.assertNotIn(sync.TEMPLATE_METADATA_START, body)
                self.assertNotIn(sync.TEMPLATE_METADATA_END, body)

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
    def test_managed_files_and_templates_are_always_overwritten(self):
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

    def test_project_scaffolding_excludes_editorconfig(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app", scaffold_project_files=True)
            expected = {
                "README.md",
                "CHANGELOG.md",
                ".gitignore",
                "docs/project/features.md",
                "docs/project/architecture.md",
                "docs/project/user-guide.md",
                "docs/project/fsd.md",
                "docs/project/tsd.md",
            }
            for relative in expected:
                self.assertTrue((target / relative).is_file(), relative)
            self.assertFalse((target / ".editorconfig").exists())
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("<!-- Scaffolded from: docs/templates/readme.template.md -->", readme)
            self.assertNotIn(sync.TEMPLATE_METADATA_START, readme)

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
                ".github/ISSUE_TEMPLATE/bug_report.md": "project bug form\n",
            }
            for relative, content in existing.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            sync.synchronize(
                PACK_ROOT,
                target,
                "full",
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
            )
            for relative, content in existing.items():
                self.assertEqual((target / relative).read_text(encoding="utf-8"), content)

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
                "full",
                scaffold_project_files=True,
                scaffold_github_templates=True,
                scaffold_editorconfig=True,
                dry_run=True,
            )
            self.assertTrue(actions)
            self.assertEqual(list(target.iterdir()), [])

    def test_profile_reduction_never_deletes_files(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "full")
            gdd = target / "docs/templates/gdd.template.md"
            self.assertTrue(gdd.is_file())
            sync.synchronize(PACK_ROOT, target, "minimal")
            self.assertTrue(gdd.is_file())

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
    def test_universal_archive_contains_exact_manifest_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            archive = bundle_builder.build_archive(REPOSITORY_ROOT, output)
            self.assertEqual(archive.name, "repo-seed-pack-3.2.1.zip")
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
                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--target",
                        str(target),
                        "--profile",
                        profile,
                        "--scaffold-project-files",
                        "--scaffold-github-templates",
                        "--scaffold-editorconfig",
                    ],
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
                "schema_version": 1,
                "pack_version": "3.2.1",
                "default_profile": "minimal",
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
                "schema_version": 1,
                "pack_version": "3.2.1",
                "default_profile": "minimal",
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
