from __future__ import annotations

import contextlib
import importlib.util
import io
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
TOOLING = REPOSITORY_ROOT / "scripts" / "repo-seed.py"
GITHUB_LABELS_CATALOG = PACK_ROOT / "github-labels.json"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_skill_frontmatter(content: str):
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError("SKILL.md frontmatter is not closed") from exc

    fields = {}
    current_key = None
    for line in lines[1:end]:
        if not line.strip():
            continue
        is_continuation = line[:1].isspace()
        if not is_continuation and ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            if key in fields:
                raise AssertionError(f"duplicate frontmatter field: {key}")
            fields[key] = value
            current_key = key
        elif current_key is not None:
            # Fold a multi-line / block / quoted YAML value onto its key.
            fields[current_key] = f"{fields[current_key]} {line.strip()}".strip()
        else:
            raise AssertionError(f"unsupported frontmatter line: {line!r}")
    return fields, "\n".join(lines[end + 1 :]).strip()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sync = load_module("sync_docs", SYNC_SCRIPT)
tooling = load_module("repo_seed_tooling", TOOLING)

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


def schema_2_state(
    profile: str = "app",
    conventions: list[str] | None = None,
    managed_files: dict[str, str] | None = None,
    tombstones: dict[str, str] | None = None,
    pack_version: str = "5.0.0",
) -> dict:
    """A schema-2 state, optionally carrying historical evidence a current
    manifest no longer fully recognizes (a removed convention id, a managed
    path no longer in the manifest).
    """
    return {
        "schema_version": 2,
        "pack_version": pack_version,
        "profile": profile,
        "conventions": list(conventions or []),
        "managed_files": managed_files or {},
        "tombstones": tombstones or {},
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
        self.assertEqual(self.manifest.package_files, ("README.md", "LICENSE", "github-labels.json", "skill-sources.json"))
        for package_file in self.manifest.package_files:
            self.assertTrue((PACK_ROOT / package_file).is_file(), package_file)
        for asset in self.manifest.assets:
            self.assertTrue((PACK_ROOT / "files" / Path(asset.source_path)).is_file(), asset.path)

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
        # 4.2.0 shipped on main before 5.0.0 merged; both are real, distinct releases.
        self.assertIn("## 4.2.0", changelog)

    def test_pack_directory_and_manifest_inventory_match(self):
        files_root = PACK_ROOT / "files"
        actual = {
            path.relative_to(files_root).as_posix()
            for path in files_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        listed = {asset.source_path for asset in self.manifest.assets}
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
        library_profiles = {"library", "app", "game"}
        expected = {
            "AGENTS.md": all_profiles,
            "CLAUDE.md": all_profiles,
            "scripts/sync-docs.py": all_profiles,
            ".agents/guidelines/documentation.md": all_profiles,
            ".agents/guidelines/git.md": all_profiles,
            ".agents/guidelines/ci-cd.md": all_profiles,
            ".agents/guidelines/issues.md": all_profiles,
            ".agents/skills/code-review/SKILL.md": all_profiles,
            ".agents/skills/bug-fix/SKILL.md": all_profiles,
            ".agents/skills/code-simplification/SKILL.md": all_profiles,
            ".agents/skills/code-simplification/NOTICE.md": all_profiles,
            ".agents/skills/refactor/SKILL.md": all_profiles,
            ".agents/skills/dependency-upgrade/SKILL.md": all_profiles,
            ".agents/skills/issue-authoring/SKILL.md": all_profiles,
            ".agents/skills/issue-implementation/SKILL.md": all_profiles,
            ".agents/skills/repository-audit/SKILL.md": all_profiles,
            ".agents/skills/repository-bootstrap/SKILL.md": all_profiles,
            ".agents/skills/repository-upgrade/SKILL.md": all_profiles,
            ".agents/skills/test-driven-development/SKILL.md": all_profiles,
            ".agents/skills/test-driven-development/NOTICE.md": all_profiles,
            ".agents/skills/technical-design/SKILL.md": library_profiles,
            ".agents/skills/documentation-bootstrap/SKILL.md": library_profiles,
            ".agents/skills/architecture-review/SKILL.md": library_profiles,
            ".agents/skills/architecture-review/NOTICE.md": library_profiles,
        }
        # Every skill is installed under both surfaces with the same profiles.
        for path in [path for path in expected if path.startswith(".agents/skills/")]:
            expected[path.replace(".agents/skills/", ".claude/skills/", 1)] = expected[path]
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
        common = {"changelog.template.md", "readme.template.md"}
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
        self.assertEqual(
            assets["docs/templates/architecture.template.md"].scaffold_target,
            "docs/project/architecture.md",
        )

    def test_features_template_is_not_distributed(self):
        # repo-seed does not distribute a standard FEATURES/capability-index
        # template; GitHub Issues and CHANGELOG already cover that need.
        # A project's own FEATURES.md or docs/project/features.md remains
        # project-owned if it already has one.
        self.assertFalse(
            any(asset.path.endswith("features.template.md") for asset in self.manifest.assets)
        )
        self.assertFalse((PACK_ROOT / "files/docs/templates/features.template.md").exists())

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

    def test_only_the_workflows_group_may_target_the_workflows_tree_and_only_inside_it(self):
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        outside = json.loads(json.dumps(raw))
        template = next(a for a in outside["assets"] if a.get("scaffold_group") == "workflows")
        template["scaffold_target"] = ".github/other/repo-seed-audit.yml"
        for manifest in (outside,):
            with tempfile.TemporaryDirectory() as temp:
                pack = Path(temp)
                (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "must be under .github/workflows"):
                    sync.load_manifest(pack, validate_sources=False)
        # The shipped manifest is valid, with exactly one workflows scaffold.
        sync.load_manifest(PACK_ROOT, validate_sources=False)
        workflow_scaffolds = [a for a in raw["assets"] if a.get("scaffold_group") == "workflows"]
        self.assertEqual(sorted(a["scaffold_target"] for a in workflow_scaffolds),
            [".github/workflows/repo-seed-audit.yml", ".github/workflows/repo-seed-sync.yml"],
        )

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
            "native repository skills",
            "scripts/sync-docs.py",
            "Load only the additional guidance relevant to the task",
            "Do not scan `docs/project/` by default",
        ):
            self.assertIn(required, agents)
        self.assertIn("@AGENTS.md", claude)
        self.assertFalse((PACK_ROOT / "files/.agents/base.md").exists())

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

    def test_claude_skills_are_generated_from_the_authored_tree(self):
        manifest = sync.load_manifest(PACK_ROOT)
        raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse((PACK_ROOT / "files/.claude").exists())
        self.assertFalse([a for a in raw["assets"] if a["path"].startswith(".claude/skills/")])
        authored = {a.path: a for a in manifest.assets if a.path.startswith(".agents/skills/")}
        generated = {a.path: a for a in manifest.assets if a.path.startswith(".claude/skills/")}
        self.assertTrue(authored)
        self.assertEqual(
            {p.replace(".agents/skills/", ".claude/skills/", 1) for p in authored}, set(generated)
        )
        for path, asset in generated.items():
            source = authored[path.replace(".claude/skills/", ".agents/skills/", 1)]
            self.assertEqual(asset.source_path, source.path)
            self.assertEqual(asset.profiles, source.profiles)
            self.assertEqual(asset.asset_type, "managed")

    def test_managed_skill_files_have_valid_portable_structure(self):
        manifest = sync.load_manifest(PACK_ROOT)
        skill_assets = [
            asset
            for asset in manifest.assets
            if asset.asset_type == "managed"
            and "/skills/" in asset.path
            and asset.path.endswith("/SKILL.md")
        ]
        self.assertTrue(skill_assets)
        for asset in skill_assets:
            path = PACK_ROOT / "files" / asset.source_path
            fields, body = parse_skill_frontmatter(path.read_text(encoding="utf-8"))
            with self.subTest(path=asset.path):
                self.assertEqual(set(fields), {"name", "description"})
                name = fields["name"]
                description = fields["description"]
                self.assertRegex(name, SKILL_NAME_RE)
                self.assertLessEqual(len(name), 64)
                self.assertEqual(name, path.parent.name)
                self.assertTrue(description)
                self.assertLessEqual(len(description), 1024)
                self.assertTrue(body)

    def test_audited_skills_keep_adopted_workflow_ideas_and_permission_boundaries(self):
        expected = {
            "bug-fix": (
                "Build a feedback loop before theorizing",
                "falsifiable hypotheses",
                "unique greppable marker",
                "If two fix attempts fail",
                "Redact secrets",
                "Do not add temporary production instrumentation without permission",
            ),
            "code-review": (
                "merge-base",
                "diff is non-empty",
                "cite the rule",
                "judgement calls",
            ),
        }
        forbidden = ("git push", "git commit", "gh pr", "gh issue", "sub-agent", "subagent")
        for root in (".agents/skills",):
            for skill, phrases in expected.items():
                content = " ".join(
                    (PACK_ROOT / "files" / root / skill / "SKILL.md").read_text(encoding="utf-8").split()
                )
                for phrase in phrases:
                    with self.subTest(root=root, skill=skill, phrase=phrase):
                        self.assertIn(phrase, content)
                for phrase in forbidden:
                    with self.subTest(root=root, skill=skill, forbidden=phrase):
                        self.assertNotIn(phrase, content)

    def test_code_review_acceptance_review_is_conditional_read_only_and_aligned_with_implementation(self):
        implementation_terms = "satisfied, unsatisfied, or not verifiable"
        for root in (".agents/skills",):
            review = " ".join(
                (PACK_ROOT / "files" / root / "code-review" / "SKILL.md").read_text(encoding="utf-8").split()
            )
            implementation = " ".join(
                (PACK_ROOT / "files" / root / "issue-implementation" / "SKILL.md")
                .read_text(encoding="utf-8")
                .split()
            )
            self.assertIn(implementation_terms, implementation)
            for phrase in (
                "## Acceptance Review",
                "only when the change is issue-driven",
                "do not go looking for an issue",
                "complete issue and relevant discussion",
                "`Done when`",
                implementation_terms,
                "not-verifiable condition is a validation gap, not a defect",
                "concrete implementation gap",
                "scope divergence",
                "material unrelated behavior",
                "contradicts its assumptions",
                "acceptance coverage",
                "Acceptance coverage supplements real defect findings",
                "regression test that failed before the change",
                "issue or pull request state, labels, comments, or other hosted resources",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, review)
            self.assertLess(review.index("## Workflow"), review.index("## Acceptance Review"))
            self.assertLess(review.index("## Acceptance Review"), review.index("## Findings"))

    def test_test_driven_development_skill_is_explicit_only_portable_and_attributed(self):
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        self.assertIn("test-driven-development", [entry["name"] for entry in registry["skills"]])
        for root in (".agents/skills",):
            directory = PACK_ROOT / "files" / root / "test-driven-development"
            content = " ".join((directory / "SKILL.md").read_text(encoding="utf-8").split())
            notice = (directory / "NOTICE.md").read_text(encoding="utf-8")
            for phrase in (
                "explicitly asks for TDD",
                "Do not apply it to every implementation",
                "Normal implementation work stays free to choose",
                "authoritative",
                "Refactor only while everything is green",
                "fails for the expected reason",
                "public interface",
                "independently",
                "only at system boundaries",
                "mutation",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)
            for phrase in ("superpowers:", "GLOSSARY", "Skill tool", "sub-agent", "gh pr", "git commit "):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase, content)
            for phrase in (
                "Copyright (c) 2026 Matt Pocock",
                "49dd158d1076134a641b33efb035946536778336",
                "Permission is hereby granted",
                "Jesse Vincent",
            ):
                with self.subTest(root=root, notice=phrase):
                    self.assertIn(phrase, notice)

    def test_code_simplification_skill_is_behavior_preserving_distinct_and_attributed(self):
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["skills"] if e["name"] == "code-simplification")
        self.assertEqual(entry["license"], "MIT")
        self.assertEqual(entry["adaptation"], "adapted")
        for root in (".agents/skills",):
            directory = PACK_ROOT / "files" / root / "code-simplification"
            content = " ".join((directory / "SKILL.md").read_text(encoding="utf-8").split())
            notice = (directory / "NOTICE.md").read_text(encoding="utf-8")
            for phrase in (
                "Behavior stays identical",
                "differs from `refactor`",
                "use `refactor`",
                "not fewer lines",
                "Understand before touching",
                "conventions",
                "one simplification at a time",
                "Existing tests should pass unmodified",
                "Simplifying code you do not fully understand",
                "replacing one abstraction with another",
                "Speculative cleanup",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase.lower(), content.lower())
            for phrase in ("superpowers:", "simplify-ignore", "CLAUDE.md", "Skill tool", "sub-agent", "gh pr"):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase, content)
            for phrase in ("Copyright (c) 2025 Addy Osmani", entry["source_revision"], "Permission is hereby granted"):
                with self.subTest(root=root, notice=phrase):
                    self.assertIn(phrase, notice)

    def test_architecture_review_skill_is_read_only_evidence_based_and_attributed(self):
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["skills"] if e["name"] == "architecture-review")
        self.assertEqual(entry["license"], "MIT")
        manifest = sync.load_manifest(PACK_ROOT)
        for asset in manifest.assets:
            if "/architecture-review/" in asset.path:
                self.assertEqual(set(asset.profiles), {"library", "app", "game"}, asset.path)
        for root in (".agents/skills",):
            directory = PACK_ROOT / "files" / root / "architecture-review"
            content = " ".join((directory / "SKILL.md").read_text(encoding="utf-8").split())
            notice = (directory / "NOTICE.md").read_text(encoding="utf-8")
            for phrase in (
                "evaluates the system as it is",
                "It is read-only",
                "It does not design a replacement",
                "`technical-design`",
                "Do not re-raise a settled decision",
                "deletion test",
                "Separate what you verified",
                "Do not turn a preference",
                "small set of high-leverage findings",
                "not as a file or a generated report",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)
            for phrase in ("mermaid", "tailwind", "GLOSSARY", "ADR", "Skill tool", "sub-agent", "grilling", "cdn"):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase.lower(), content.lower())
            for phrase in ("Copyright (c) 2026 Matt Pocock", entry["source_revision"], "Permission is hereby granted"):
                with self.subTest(root=root, notice=phrase):
                    self.assertIn(phrase, notice)

    def test_repository_audit_skill_reuses_sync_machinery_and_stays_read_only(self):
        manifest = sync.load_manifest(PACK_ROOT)
        profiles = {
            asset.path: set(asset.profiles) for asset in manifest.assets if "/repository-audit/" in asset.path
        }
        self.assertEqual(
            profiles,
            {
                ".agents/skills/repository-audit/SKILL.md": {"minimal", "library", "app", "game"},
                ".claude/skills/repository-audit/SKILL.md": {"minimal", "library", "app", "game"},
            },
        )
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        self.assertNotIn("repository-audit", [entry["name"] for entry in registry["skills"]])
        for root in (".agents/skills",):
            content = " ".join(
                (PACK_ROOT / "files" / root / "repository-audit" / "SKILL.md").read_text(encoding="utf-8").split()
            )
            for phrase in (
                "The audit is read-only",
                ".repo-seed-state.json",
                "Do not download one without permission",
                "instead of reimplementing its logic",
                "scripts/sync-docs.py --source <pack> --audit",
                "`--dry-run`",
                "Never run without `--audit` or `--dry-run`",
                "**Managed drift**",
                "**Stale artifacts**",
                "**Selection inconsistencies**",
                "**Competing guidance**",
                "**Intentional project-owned differences**",
                "**Unverifiable**",
                "do not recommend overwriting them",
                "overwrites the edit",
                "Never claim a comparison was made when it was not",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)

    def test_repository_audit_commands_named_by_the_skill_exist_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target"
            target.mkdir()
            sync.synchronize(PACK_ROOT, target, "minimal", conventions=frozenset())
            (target / "AGENTS.md").write_text("local edit\n", encoding="utf-8")
            before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
            base = [
                sys.executable,
                str(target / "scripts/sync-docs.py"),
                "--source",
                str(PACK_ROOT),
                "--target",
                str(target),
            ]
            audit = subprocess.run(base + ["--audit"], capture_output=True, text=True, check=False)
            dry_run = subprocess.run(base + ["--dry-run"], capture_output=True, text=True, check=False)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("drift: AGENTS.md", audit.stdout)
            after = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_repository_bootstrap_skill_delegates_to_sync_and_keeps_scaffolding_opt_in(self):
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        self.assertNotIn("repository-bootstrap", [entry["name"] for entry in registry["skills"]])
        for root in (".agents/skills",):
            content = " ".join(
                (PACK_ROOT / "files" / root / "repository-bootstrap" / "SKILL.md")
                .read_text(encoding="utf-8")
                .split()
            )
            for phrase in (
                "`documentation-bootstrap`",
                "only mechanism",
                "Do not download one without permission",
                "Only those values are valid",
                "Inspect the target before choosing any argument",
                "stop and ask rather than assuming",
                "Install none by default and never all of them",
                "Choose scaffolds as opt-in",
                "`AGENTS.md` and `CLAUDE.md` are managed",
                "`.agents/project.md` first",
                "`.github/workflows/`",
                "`--dry-run`",
                "only after the dry run is acceptable",
                "`.repo-seed-state.json` records the intended profile",
                "follow-up run with `--dry-run` is clean",
                "Do not invent project facts",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)

    def test_repository_bootstrap_first_sync_matches_the_documented_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target"
            (target / ".github/workflows").mkdir(parents=True)
            (target / ".github/workflows/ci.yml").write_text("name: project ci\n", encoding="utf-8")
            (target / "README.md").write_text("project readme\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("project instructions\n", encoding="utf-8")
            script = PACK_ROOT / "files/scripts/sync-docs.py"
            args = [
                sys.executable,
                str(script),
                "--source",
                str(PACK_ROOT),
                "--target",
                str(target),
                "--profile",
                "library",
                "--conventions",
                "python",
                "--scaffold-project-files",
            ]
            before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
            dry_run = subprocess.run(args + ["--dry-run"], capture_output=True, text=True, check=False)
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("AGENTS.md (would overwrite managed copy; no recorded baseline)", dry_run.stdout)
            self.assertEqual(before, {p: p.read_bytes() for p in target.rglob("*") if p.is_file()})

            applied = subprocess.run(args, capture_output=True, text=True, check=False)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["profile"], "library")
            self.assertEqual(state["conventions"], ["python"])
            for surface in (".agents", ".claude"):
                self.assertTrue((target / surface / "skills/repository-bootstrap/SKILL.md").is_file())
            self.assertTrue((target / ".agents/conventions/python.md").is_file())
            self.assertFalse((target / ".agents/conventions/csharp.md").exists())
            # Project-owned files survive, including a customized README and the workflows tree.
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "project readme\n")
            self.assertEqual(
                (target / ".github/workflows/ci.yml").read_text(encoding="utf-8"), "name: project ci\n"
            )
            self.assertNotEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "project instructions\n")

            follow_up = subprocess.run(args + ["--dry-run"], capture_output=True, text=True, check=False)
            self.assertEqual(follow_up.returncode, 0, follow_up.stderr)
            self.assertNotIn("would overwrite", follow_up.stdout)
            self.assertNotIn("would create", follow_up.stdout)
            self.assertNotIn("would remove", follow_up.stdout)

    def test_repository_upgrade_skill_orchestrates_the_newer_pack_and_owns_no_migration_rules(self):
        registry = json.loads((PACK_ROOT / "skill-sources.json").read_text(encoding="utf-8"))
        self.assertNotIn("repository-upgrade", [entry["name"] for entry in registry["skills"]])
        for root in (".agents/skills",):
            content = " ".join(
                (PACK_ROOT / "files" / root / "repository-upgrade" / "SKILL.md").read_text(encoding="utf-8").split()
            )
            for phrase in (
                "use `repository-bootstrap` instead",
                "belong to the newer pack's manifest and `sync-docs.py`",
                "Do not download one without permission",
                "Inspect the installed state before changing anything",
                "not the older copy in the target",
                "omit them for a normal upgrade",
                "do not choose for the user",
                "`--dry-run` first",
                "and discard local changes",
                "with `--diff`",
                "Do not force a change to files the script preserves",
                "report its error to the user and ask",
                "do not download a pack without permission",
                "only after the dry run is acceptable",
                "removals happened only for unchanged files repo-seed owned",
                "repeat `--dry-run` is clean or every remaining line is explained",
                "`--audit`",
                "Do not create branches, commit, push, or change hosted state",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)
            # No parallel migration table or version-specific rule lives in the skill.
            for phrase in ("schema_version: 1", "4.1.0", "legacy_targets", "previous_hashes"):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase, content)

    def test_issue_authoring_skill_is_grounded_gated_and_defers_to_issue_guidance(self):
        for root in (".agents/skills",):
            content = " ".join(
                (PACK_ROOT / "files" / root / "issue-authoring" / "SKILL.md").read_text(encoding="utf-8").split()
            )
            for phrase in (
                ".agents/guidelines/issues.md",
                "open and closed issues",
                "open and closed pull requests",
                "already exist",
                "SECURITY.md",
                "Done when",
                "explicit authorization",
                "does not imply it",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)
            # The taxonomy lives only in the canonical guidance.
            for label in ("type: bug", "type: feature", "priority: high"):
                with self.subTest(root=root, label=label):
                    self.assertNotIn(label, content)
            for phrase in ("git push", "git commit", "gh issue create", "gh pr"):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase, content)

    def test_issue_implementation_skill_verifies_delegates_and_gates_permissions(self):
        for root in (".agents/skills",):
            content = " ".join(
                (PACK_ROOT / "files" / root / "issue-implementation" / "SKILL.md")
                .read_text(encoding="utf-8")
                .split()
            )
            for phrase in (
                ".agents/guidelines/issues.md",
                "no open pull request",
                "already exist",
                "blocking decisions",
                "bug-fix",
                "refactor",
                "dependency-upgrade",
                "technical-design",
                "satisfied, unsatisfied, or not verifiable",
                "authorizes the working-tree edits",
                "commit, push, open or update pull requests, merge",
                "does not close the governing issue",
            ):
                with self.subTest(root=root, phrase=phrase):
                    self.assertIn(phrase, content)
            for phrase in ("superpowers:", "/implement", "worktree", "sub-agent", "subagent"):
                with self.subTest(root=root, forbidden=phrase):
                    self.assertNotIn(phrase, content)

    def test_skills_define_substantive_workflows(self):
        for root in (".agents/skills",):
            for skill in sorted((PACK_ROOT / "files" / root).glob("*/SKILL.md")):
                content = skill.read_text(encoding="utf-8")
                _, body = parse_skill_frontmatter(content)
                relative = skill.relative_to(PACK_ROOT / "files")
                workflow_steps = re.findall(r"(?m)^\d+\. ", body)
                with self.subTest(skill=str(relative)):
                    self.assertIn("## Workflow", body)
                    self.assertGreaterEqual(len(workflow_steps), 3)
                    self.assertIn("## Completion", body)

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

    def test_issue_forms_scaffold_verbatim_without_markdown_provenance(self):
        manifest = sync.load_manifest(PACK_ROOT)
        for suffix in (
            "bug-report.template.yml",
            "feature-request.template.yml",
            "tech-debt.template.yml",
            "chore.template.yml",
        ):
            asset = next(a for a in manifest.assets if a.path.endswith(suffix))
            with self.subTest(form=suffix), tempfile.TemporaryDirectory() as temp:
                target = Path(temp)
                action = sync.scaffold_asset(PACK_ROOT, target, asset, dry_run=False)
                content = (target / asset.scaffold_target).read_text(encoding="utf-8")
                self.assertEqual(action.action, "scaffold")
                self.assertEqual(content, sync.template_body(PACK_ROOT / "files" / asset.path))
                self.assertNotIn("<!--", content)

    def test_scaffolded_issue_templates_use_canonical_type_labels(self):
        manifest = sync.load_manifest(PACK_ROOT)
        bug_asset = next(
            asset for asset in manifest.assets if asset.path.endswith("bug-report.template.yml")
        )
        feature_asset = next(
            asset for asset in manifest.assets if asset.path.endswith("feature-request.template.yml")
        )
        bug_rendered = sync.render_scaffold(PACK_ROOT, bug_asset)
        feature_rendered = sync.render_scaffold(PACK_ROOT, feature_asset)
        self.assertIn('labels: ["type: bug"]', bug_rendered)
        self.assertIn('labels: ["type: feature"]', feature_rendered)
        for suffix, label in (("tech-debt.template.yml", "type: tech-debt"), ("chore.template.yml", "type: chore")):
            asset = next(a for a in manifest.assets if a.path.endswith(suffix))
            self.assertIn(f'labels: ["{label}"]', sync.render_scaffold(PACK_ROOT, asset))
        self.assertNotIn("labels: bug", bug_rendered)
        self.assertNotIn("labels: enhancement", feature_rendered)

    def test_issues_guidance_defines_canonical_catalog_and_entry_points(self):
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        for required in (
            "type: bug",
            "type: feature",
            "type: tech-debt",
            "type: chore",
            "priority: critical",
            "priority: high",
            "priority: medium",
            "priority: low",
            "A dependency upgrade is a\n`chore` even when it needs code changes.",
            "Do not establish a mandatory shared `area:*` taxonomy",
            "Priority is optional",
            "Bug Report",
            "Feature Request",
            "starts from a form",
            "blank_issues_enabled: false",
            "GitHub Issue Forms",
            "can bypass them",
            "Do not replace `type:*` labels with GitHub's native issue types",
        ):
            self.assertIn(required, guidance)
        for legacy, replacement in {
            "bug": "type: bug",
            "enhancement": "type: feature",
            "critical": "priority: critical",
            "lowest": "priority: low",
            "type: decision": "re-triage",
            "type: idea": "re-triage",
        }.items():
            self.assertIn(legacy, guidance)
            self.assertIn(replacement, guidance)
        for retired in ("Decision issues", "Idea issues", "blank issue ->"):
            self.assertNotIn(retired, guidance)
        self.assertIn("Chore (`chore.yml`, applies `type: chore`)", guidance)
        self.assertIn("Tech Debt (`tech_debt.yml`, applies `type: tech-debt`)", guidance)

    def test_label_catalog_and_guidance_state_the_same_type_scope(self):
        catalog = {label["name"]: label for label in tooling.load_catalog(GITHUB_LABELS_CATALOG)}
        self.assertNotIn("type: decision", catalog)
        self.assertNotIn("type: idea", catalog)
        self.assertNotIn("maintenance", catalog["type: tech-debt"]["description"].lower())
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        tech_debt_entry = guidance.split("- `type: tech-debt`", 1)[1].split("- `type: chore`", 1)[0]
        self.assertNotIn("maintenance", tech_debt_entry.lower())

    def test_distributed_issue_guidance_is_self_contained_for_target_repositories(self):
        guidance = (PACK_ROOT / "files/.agents/guidelines/issues.md").read_text(encoding="utf-8")
        self.assertNotIn("pack/github-labels.json", guidance)
        self.assertNotIn("scripts/repo-seed.py", guidance)
        self.assertIn("GitHub-Hosted Labels", guidance)
        self.assertIn("verify it\ndirectly through GitHub", guidance)

    def test_no_distributed_file_references_repo_seed_only_tooling_paths(self):
        forbidden = ("pack/github-labels.json", "scripts/repo-seed.py")
        files_root = PACK_ROOT / "files"
        for path in files_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            for needle in forbidden:
                with self.subTest(path=path.relative_to(PACK_ROOT), needle=needle):
                    self.assertNotIn(needle, content)

    def test_manifest_github_scaffolds_are_issue_forms_and_pr_template(self):
        github_scaffolds = {
            asset.scaffold_target
            for asset in sync.load_manifest(PACK_ROOT).assets
            if asset.scaffold_group == "github"
        }
        self.assertEqual(
            github_scaffolds,
            {
                ".github/ISSUE_TEMPLATE/bug_report.yml",
                ".github/ISSUE_TEMPLATE/feature_request.yml",
                ".github/ISSUE_TEMPLATE/tech_debt.yml",
                ".github/ISSUE_TEMPLATE/chore.yml",
                ".github/ISSUE_TEMPLATE/config.yml",
                ".github/pull_request_template.md",
            },
        )

    @staticmethod
    def _form_fields(content):
        """Map each form element's label to whether it is required (stdlib-only parse)."""
        fields = {}
        for chunk in re.split(r"^  - type: ", content, flags=re.MULTILINE)[1:]:
            label = re.search(r"^      label: (.+)$", chunk, re.MULTILINE)
            if label:
                fields[label.group(1).strip()] = "      required: true" in chunk
        return fields

    def test_issue_forms_require_the_minimum_contract_and_nothing_more(self):
        implementation_fields = {
            "Summary": True,
            "Goal": True,
            "Suggested approach": False,
            "Done when": True,
        }
        expected = {
            "bug-report.template.yml": {
                "Summary": True,
                "Steps to Reproduce": True,
                "Expected Behavior": True,
                "Actual Behavior": True,
                "Environment": True,
                "Additional Context": False,
            },
            "feature-request.template.yml": implementation_fields,
            "tech-debt.template.yml": implementation_fields,
            "chore.template.yml": implementation_fields,
        }
        manifest = sync.load_manifest(PACK_ROOT)
        for suffix, fields in expected.items():
            asset = next(a for a in manifest.assets if a.path.endswith(suffix))
            rendered = sync.render_scaffold(PACK_ROOT, asset)
            with self.subTest(form=suffix):
                self.assertEqual(self._form_fields(rendered), fields)
                self.assertNotIn("title:", rendered)
                self.assertNotIn("assignees:", rendered)
                self.assertNotIn("[BUG]", rendered)
                self.assertNotRegex(rendered, r"(?i)priority")
                self.assertNotIn("repo-seed-template", rendered)
                self.assertNotIn("Scaffolded from", rendered)
            repo_form = REPOSITORY_ROOT / ".github/ISSUE_TEMPLATE" / asset.scaffold_target.rsplit("/", 1)[1]
            self.assertEqual(self._form_fields(repo_form.read_text(encoding="utf-8")), fields)

    def test_root_issue_chooser_has_one_issue_form_per_type(self):
        issue_root = REPOSITORY_ROOT / ".github/ISSUE_TEMPLATE"
        self.assertEqual(
            sorted(path.name for path in issue_root.iterdir()),
            ["bug_report.yml", "chore.yml", "config.yml", "feature_request.yml", "tech_debt.yml"],
        )
        for name, label in (
            ("bug_report.yml", "type: bug"),
            ("feature_request.yml", "type: feature"),
            ("tech_debt.yml", "type: tech-debt"),
            ("chore.yml", "type: chore"),
        ):
            content = (issue_root / name).read_text(encoding="utf-8")
            self.assertRegex(content, r"(?m)^name: .+$", name)
            self.assertRegex(content, r"(?m)^description: .+$", name)
            self.assertIn(f'labels: ["{label}"]', content, name)
            self.assertRegex(content, r"(?m)^body:$", name)
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

    def test_pre_5_0_state_is_rejected_with_the_last_converting_release_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".repo-seed-state.json").write_text(json.dumps(schema_1_state()), encoding="utf-8")
            before = (target / ".repo-seed-state.json").read_bytes()

            for conventions in (None, frozenset({"csharp"})):
                with self.subTest(conventions=conventions):
                    with self.assertRaisesRegex(ValueError, re.escape("releases/tag/v5.13.2")):
                        sync.synchronize(PACK_ROOT, target, "app", conventions=conventions)
            with self.assertRaisesRegex(ValueError, "pre-5.0"):
                sync.audit_target(PACK_ROOT, target, "app")

            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), before)
            self.assertEqual(list(target.iterdir()), [target / ".repo-seed-state.json"])

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

    def test_state_parsing_succeeds_when_a_recorded_convention_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            old_tool = target / ".agents/conventions/old-tool.md"
            old_tool.parent.mkdir(parents=True, exist_ok=True)
            old_tool.write_text("old tool convention content\n", encoding="utf-8")
            state = schema_2_state(
                conventions=["csharp", "old-tool"],
                managed_files={".agents/conventions/old-tool.md": sync.managed_file_hash(old_tool)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            manifest = sync.load_manifest(PACK_ROOT)
            parsed = sync.read_managed_state(target, manifest)

            self.assertEqual(parsed.conventions, frozenset({"csharp", "old-tool"}))

    def test_sync_without_conventions_fails_clearly_when_a_recorded_convention_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            old_tool = target / ".agents/conventions/old-tool.md"
            old_tool.parent.mkdir(parents=True, exist_ok=True)
            old_tool.write_text("old tool convention content\n", encoding="utf-8")
            state = schema_2_state(
                conventions=["csharp", "old-tool"],
                managed_files={".agents/conventions/old-tool.md": sync.managed_file_hash(old_tool)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")
            before = (target / ".repo-seed-state.json").read_bytes()

            with self.assertRaisesRegex(ValueError, "no longer available"):
                sync.synchronize(PACK_ROOT, target, "app")

            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), before)
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertEqual(old_tool.read_text(encoding="utf-8"), "old tool convention content\n")

    def test_sync_with_explicit_conventions_resolves_a_removed_convention(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            old_tool = target / ".agents/conventions/old-tool.md"
            old_tool.parent.mkdir(parents=True, exist_ok=True)
            old_tool.write_text("old tool convention content\n", encoding="utf-8")
            state = schema_2_state(
                conventions=["csharp", "old-tool"],
                managed_files={".agents/conventions/old-tool.md": sync.managed_file_hash(old_tool)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))

            self.assertTrue((target / ".agents/conventions/csharp.md").is_file())
            new_state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(new_state["conventions"], ["csharp"])

            # The removed convention's managed file is no longer a manifest
            # asset at all: the existing historical-managed-path mechanism
            # preserves and tombstones it, exactly like any other retired
            # managed asset, with no convention-specific migration logic.
            self.assertTrue(old_tool.is_file())
            self.assertIn(".agents/conventions/old-tool.md", new_state["tombstones"])
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == ".agents/conventions/old-tool.md"
                    and "no longer in the manifest" in action.detail
                    for action in actions
                )
            )

    def test_audit_does_not_crash_on_a_removed_recorded_convention(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            state = schema_2_state(conventions=["csharp", "old-tool"])
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "app")

            self.assertTrue(any("recorded convention unavailable: old-tool" in line for line in report))
            self.assertIn("conventions: unresolved (recorded convention no longer available)", report)
            self.assertFalse(any(line == "conventions: none selected" for line in report))
            self.assertTrue(any("finding(s) reported above" in line for line in report))

    def test_audit_with_explicit_conventions_resolves_the_removed_convention_finding(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            state = schema_2_state(conventions=["csharp", "old-tool"])
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))

            self.assertFalse(any("recorded convention unavailable" in line for line in report))
            self.assertIn("conventions: csharp", report)

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
            self.assertIn("releases/tag/v5.13.2", result.stderr)
            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), before)


class SyncBehaviorTests(unittest.TestCase):
    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--source", str(PACK_ROOT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_non_utf8_managed_file_stops_the_sync_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "AGENTS.md").write_bytes(b"caf\xe9 not utf-8")
            result = self.cli("--target", str(target), "--profile", "minimal")
            self.assertEqual(result.returncode, 2)
            self.assertIn("not valid UTF-8", result.stderr)
            self.assertEqual((target / "AGENTS.md").read_bytes(), b"caf\xe9 not utf-8")
            self.assertFalse((target / ".repo-seed-state.json").exists())
            self.assertFalse((target / "CLAUDE.md").exists())

    def test_overwrite_without_baseline_shows_a_diff_and_a_note(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "AGENTS.md").write_text("my own rules\n", encoding="utf-8")
            dry = self.cli("--target", str(target), "--profile", "minimal", "--dry-run", "--diff")
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("no recorded baseline", dry.stdout)
            self.assertIn("+my own rules", dry.stdout)
            self.assertIn("NOTE:", dry.stdout)
            self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "my own rules\n")
            real = self.cli("--target", str(target), "--profile", "minimal")
            self.assertIn("NOTE:", real.stdout)
            self.assertIn("without a recorded baseline", real.stdout)

    def test_audit_reports_non_utf8_managed_file_as_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            (target / "AGENTS.md").write_bytes(b"\xff\xfe bad")
            result = self.cli("--target", str(target), "--audit")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("drift: AGENTS.md is not valid UTF-8", result.stdout)

    def test_state_that_is_not_an_object_or_too_deep_is_rejected_cleanly(self):
        for content in ("[1, 2]", "[" * 100000):
            with self.subTest(content[:5]), tempfile.TemporaryDirectory() as temp:
                target = Path(temp)
                (target / ".repo-seed-state.json").write_text(content, encoding="utf-8")
                result = self.cli("--target", str(target), "--profile", "minimal", "--dry-run")
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_sync_installs_identical_claude_skills_and_audit_flags_their_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "app")
            authored = sorted((target / ".agents/skills").rglob("*"))
            self.assertTrue(any(p.is_file() for p in authored))
            for path in authored:
                if path.is_file():
                    mirror = target / ".claude/skills" / path.relative_to(target / ".agents/skills")
                    self.assertEqual(mirror.read_bytes(), path.read_bytes())
            (target / ".claude/skills/bug-fix/SKILL.md").write_text("edited\n", encoding="utf-8")
            result = self.cli("--target", str(target), "--audit")
            self.assertIn("drift: .claude/skills/bug-fix/SKILL.md differs", result.stdout)
            self.cli("--target", str(target))
            self.assertEqual(
                (target / ".claude/skills/bug-fix/SKILL.md").read_bytes(),
                (target / ".agents/skills/bug-fix/SKILL.md").read_bytes(),
            )

    def test_discovery_requires_the_sync_script(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp) / "pack"
            shutil.copytree(PACK_ROOT, pack)
            (pack / "files" / "scripts" / "sync-docs.py").unlink()
            with self.assertRaises((ValueError, FileNotFoundError)):
                sync.load_manifest(pack)

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

    def test_state_bootstrap_without_a_state_file_never_infers_ownership(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game")
            (target / ".repo-seed-state.json").unlink()
            unknown = target / "project-owned.txt"
            unknown.write_text("keep\n", encoding="utf-8")

            sync.synchronize(PACK_ROOT, target, "app")

            # No state file means no historical ownership knowledge: a
            # previously-synced asset no longer selected by the new profile
            # must be preserved rather than pruned, exactly like any other
            # unrecognized pre-existing file.
            self.assertTrue((target / "docs/templates/gdd.template.md").exists())
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
                ".github/ISSUE_TEMPLATE/bug_report.yml": "project bug form\n",
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

    def test_customized_issue_forms_and_legacy_markdown_templates_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            issue_root = target / ".github/ISSUE_TEMPLATE"
            issue_root.mkdir(parents=True)
            (issue_root / "bug_report.yml").write_text("name: Our bug form\n", encoding="utf-8")
            (issue_root / "feature_request.md").write_text("our legacy template\n", encoding="utf-8")
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            self.assertEqual((issue_root / "bug_report.yml").read_text(encoding="utf-8"), "name: Our bug form\n")
            self.assertEqual((issue_root / "feature_request.md").read_text(encoding="utf-8"), "our legacy template\n")
            self.assertTrue((issue_root / "feature_request.yml").is_file())

    def test_github_scaffolding_is_explicit_and_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            issue_root = target / ".github/ISSUE_TEMPLATE"
            self.assertFalse(issue_root.exists())
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            for name in ("bug_report.yml", "feature_request.yml", "tech_debt.yml", "chore.yml", "config.yml"):
                self.assertTrue((issue_root / name).is_file(), name)
            self.assertEqual(
                (issue_root / "config.yml").read_text(encoding="utf-8").strip(),
                "blank_issues_enabled: false",
            )

    def test_drift_workflow_scaffold_is_opt_in_pinned_to_the_pack_and_never_overwritten(self):
        workflow = ".github/workflows/repo-seed-audit.yml"
        for profile in ("minimal", "library", "app", "game"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temp:
                target = Path(temp)
                sync.synchronize(PACK_ROOT, target, profile, scaffold_github_templates=True, scaffold_project_files=True)
                self.assertFalse((target / workflow).exists(), "created without the flag")

                preview = sync.synchronize(PACK_ROOT, target, profile, scaffold_workflows=True, dry_run=True)
                self.assertTrue(any(a.path == workflow and a.action == "scaffold" for a in preview))
                self.assertFalse((target / workflow).exists(), "dry run wrote the file")

                sync.synchronize(PACK_ROOT, target, profile, scaffold_workflows=True)
                content = (target / workflow).read_text(encoding="utf-8")
                self.assertIn(
                    f"uses: Trawis/repo-seed/.github/workflows/audit.yml@v{PACK_VERSION}\n", content
                )
                self.assertNotIn("__PACK_VERSION__", content)
                self.assertNotIn("repo-seed-template", content)
                self.assertRegex(content, r"(?m)^      contents: read$")
                self.assertRegex(content, r"(?m)^      issues: write$")

                (target / workflow).write_text("name: mine\n", encoding="utf-8")
                again = sync.synchronize(PACK_ROOT, target, profile, scaffold_workflows=True)
                self.assertEqual((target / workflow).read_text(encoding="utf-8"), "name: mine\n")
                self.assertTrue(any(a.path == workflow and a.action == "skip" for a in again))

    def test_workflows_tree_is_still_never_managed_when_the_scaffold_is_requested(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            workflows = target / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("name: project ci\n", encoding="utf-8")
            actions = sync.synchronize(PACK_ROOT, target, "minimal", scaffold_workflows=True)
            touched = {a.path for a in actions if a.path.startswith(".github/workflows/")}
            self.assertEqual(
                touched, {".github/workflows/repo-seed-audit.yml", ".github/workflows/repo-seed-sync.yml"}
            )
            self.assertEqual((workflows / "ci.yml").read_text(encoding="utf-8"), "name: project ci\n")

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

    def test_state_path_not_in_the_current_manifest_is_preserved_not_rejected(self):
        # A state-recorded path does not need to exist in the current manifest:
        # a future pack may remove a managed asset entirely, and the state file
        # alone is sufficient historical ownership evidence. Reading such state
        # must succeed, and the historical file must never be auto-deleted
        # merely because its hash matches.
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            historical = target / "src/important.py"
            historical.parent.mkdir(parents=True)
            historical.write_text("important = True\n", encoding="utf-8")
            state = {
                "schema_version": 2,
                "pack_version": "5.0.0",
                "profile": "minimal",
                "conventions": [],
                "managed_files": {
                    "src/important.py": sync.managed_file_hash(historical),
                },
                "tombstones": {},
            }
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            actions = sync.synchronize(PACK_ROOT, target, "minimal")

            self.assertEqual(historical.read_text(encoding="utf-8"), "important = True\n")
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == "src/important.py"
                    and "no longer in the manifest" in action.detail
                    for action in actions
                )
            )
            new_state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertIn("src/important.py", new_state["tombstones"])

            # Once the user manually removes the historical file, the tombstone
            # naturally drops on the next sync.
            historical.unlink()
            sync.synchronize(PACK_ROOT, target, "minimal")
            final_state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertNotIn("src/important.py", final_state["tombstones"])

    def test_a_future_manifest_that_removes_a_managed_asset_preserves_its_historical_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            future_pack = root / "future-pack"
            target.mkdir()
            shutil.copytree(PACK_ROOT / "files", future_pack / "files")
            for package_file in ("README.md", "LICENSE", "github-labels.json", "skill-sources.json"):
                shutil.copy2(PACK_ROOT / package_file, future_pack / package_file)

            sync.synchronize(PACK_ROOT, target, "app", conventions=frozenset({"csharp"}))
            state_path = target / ".repo-seed-state.json"
            self.assertIn(".agents/guidelines/ci-cd.md", json.loads(state_path.read_text(encoding="utf-8"))["managed_files"])

            manifest_raw = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))
            manifest_raw["assets"] = [
                asset for asset in manifest_raw["assets"] if asset["path"] != ".agents/guidelines/ci-cd.md"
            ]
            (future_pack / "manifest.json").write_text(json.dumps(manifest_raw), encoding="utf-8")
            (future_pack / "files/.agents/guidelines/ci-cd.md").unlink()

            actions = sync.synchronize(future_pack, target, "app", conventions=frozenset({"csharp"}))

            # The state remains readable, sync proceeds normally, and the removed
            # asset's historical file is preserved rather than auto-deleted.
            self.assertTrue((target / ".agents/guidelines/ci-cd.md").is_file())
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                any(
                    action.action == "preserve"
                    and action.path == ".agents/guidelines/ci-cd.md"
                    and "no longer in the manifest" in action.detail
                    for action in actions
                )
            )
            new_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn(".agents/guidelines/ci-cd.md", new_state["tombstones"])

            (target / ".agents/guidelines/ci-cd.md").unlink()
            sync.synchronize(future_pack, target, "app", conventions=frozenset({"csharp"}))
            final_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn(".agents/guidelines/ci-cd.md", final_state["tombstones"])

    def test_fresh_sync_with_no_state_never_infers_ownership_of_a_matching_file(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            source = PACK_ROOT / "files/.agents/conventions/unity.md"
            preexisting = target / ".agents/conventions/unity.md"
            preexisting.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, preexisting)

            sync.synchronize(PACK_ROOT, target, "app")

            # No .repo-seed-state.json existed, so repo-seed has no historical
            # ownership knowledge: it must not infer ownership of an unselected
            # pre-existing file merely because its bytes match a pack asset.
            self.assertTrue(preexisting.is_file())
            self.assertEqual(preexisting.read_bytes(), source.read_bytes())

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

    def test_audit_reports_a_managed_symlink_even_when_content_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            managed = target / "AGENTS.md"
            copy = target / "agents-copy.md"
            managed.rename(copy)
            try:
                managed.symlink_to(copy)
            except OSError as ex:
                self.skipTest(f"Symbolic links are unavailable: {ex}")

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            self.assertTrue(any(line.startswith("drift:") and "symbolic link" in line for line in report))
            self.assertFalse(any(line.endswith("no drift detected") for line in report))
            self.assertTrue(managed.is_symlink())

    def test_audit_reports_an_existing_tombstone_as_a_finding(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game")
            gdd = target / "docs/templates/gdd.template.md"
            gdd.write_text("local changes\n", encoding="utf-8")
            sync.synchronize(PACK_ROOT, target, "app")
            self.assertTrue(gdd.is_file())
            state_before = (target / ".repo-seed-state.json").read_bytes()

            report = sync.audit_target(PACK_ROOT, target, "app")

            self.assertIn(
                "tombstone: docs/templates/gdd.template.md (preserved stale managed content requires review)",
                report,
            )
            self.assertFalse(any(line.endswith("no drift detected") for line in report))
            self.assertTrue(any("finding(s) reported above" in line for line in report))
            # Audit is read-only: it never touches state, even when it finds
            # something to report.
            self.assertEqual((target / ".repo-seed-state.json").read_bytes(), state_before)

    def test_audit_reports_a_tombstone_that_resolves_outside_the_repository_and_keeps_going(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            sync.synchronize(PACK_ROOT, target, "app")
            outside = root / "outside.txt"
            outside.write_text("not part of the repository\n", encoding="utf-8")
            link = target / "docs/old.md"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available")
            state_path = target / ".repo-seed-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["tombstones"] = {"docs/old.md": "a" * 64}
            state_path.write_text(json.dumps(state), encoding="utf-8")
            state_before = state_path.read_bytes()

            report = sync.audit_target(PACK_ROOT, target, "app")

            self.assertIn("tombstone: docs/old.md (resolves outside the repository; review manually)", report)
            self.assertTrue(any("finding(s) reported above" in line for line in report))
            self.assertEqual(state_path.read_bytes(), state_before)

    def test_audit_reports_a_historical_managed_path_not_yet_tombstoned(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            historical = target / "docs/templates/old-asset.md"
            historical.parent.mkdir(parents=True, exist_ok=True)
            historical.write_text("retired content\n", encoding="utf-8")
            state = schema_2_state(
                profile="app",
                managed_files={"docs/templates/old-asset.md": sync.managed_file_hash(historical)},
            )
            (target / ".repo-seed-state.json").write_text(json.dumps(state), encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "app")

            matching = [
                line
                for line in report
                if line.startswith("tombstone:") and "docs/templates/old-asset.md" in line
            ]
            self.assertEqual(len(matching), 1)

    def test_audit_becomes_clean_after_a_tombstoned_file_is_removed_and_synced(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "game")
            gdd = target / "docs/templates/gdd.template.md"
            gdd.write_text("local changes\n", encoding="utf-8")
            sync.synchronize(PACK_ROOT, target, "app")
            self.assertTrue(any(line.startswith("tombstone:") for line in sync.audit_target(PACK_ROOT, target, "app")))

            gdd.unlink()
            sync.synchronize(PACK_ROOT, target, "app")

            report = sync.audit_target(PACK_ROOT, target, "app")
            self.assertFalse(any(line.startswith("tombstone:") for line in report))
            self.assertTrue(any(line.endswith("no drift detected") for line in report))

    def test_audit_reports_missing_guidance_drift_and_legacy_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            bug_form = target / ".github/ISSUE_TEMPLATE/bug_report.yml"
            bug_form.write_text(
                bug_form.read_text(encoding="utf-8").replace('labels: ["type: bug"]', 'labels: ["bug"]'),
                encoding="utf-8",
            )
            (target / "AGENTS.md").write_text("local edit\n", encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            self.assertTrue(any(line == "info: .agents/project.md not present" for line in report))
            self.assertFalse(any(line.startswith("missing: .agents/project.md") for line in report))
            self.assertTrue(any(line.startswith("drift: AGENTS.md") for line in report))
            self.assertTrue(any("legacy label" in line and "bug_report.yml" in line for line in report))

    def test_audit_flags_legacy_labels_in_forms_and_markdown_templates_but_not_canonical_ones(self):
        legacy = {
            "inline_form.yml": 'name: A\nlabels: ["bug"]\nbody: []\n',
            "bare_form.yml": "name: B\nlabels: enhancement\nbody: []\n",
            "list_form.yaml": 'name: C\nlabels: [ "type: feature", \'enhancement\' ]\nbody: []\n',
            "block_form.yml": 'name: D\nlabels:\n  - "type: bug"\n  - bug  # old\nbody: []\n',
            "old_template.md": "---\nname: E\nabout: x\nlabels: bug\n---\n\nBody\n",
            "retired_idea.yml": 'name: K\nlabels: ["type: idea"]\nbody: []\n',
            "retired_decision.yml": "name: L\nlabels:\n  - 'type: decision'\nbody: []\n",
        }
        clean = {
            "canonical_form.yml": 'name: F\nlabels: ["type: bug"]\nbody: []\n',
            "canonical_block.yml": "name: G\nlabels:\n  - 'type: feature'\nbody: []\n",
            "canonical_template.md": '---\nname: H\nlabels: ["type: bug"]\n---\n',
            "config.yml": "blank_issues_enabled: false\n",
            # `labels` below the top level, or outside Markdown front matter, is not a template label.
            "nested.yml": "name: I\nbody:\n  - type: dropdown\n    attributes:\n      labels: bug\n",
            "body_text.md": "---\nname: J\n---\n\nlabels: bug\n",
            "notes.txt": "labels: bug\n",
        }
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            directory = target / ".github/ISSUE_TEMPLATE"
            directory.mkdir(parents=True)
            for name, text in {**legacy, **clean}.items():
                (directory / name).write_text(text, encoding="utf-8")

            report = sync.audit_target(PACK_ROOT, target, "minimal")

            flagged = {
                line.split(" uses ")[0].rsplit("/", 1)[1]
                for line in report
                if line.startswith("legacy label:")
            }
            self.assertEqual(flagged, set(legacy))
            self.assertIn(
                "legacy label: .github/ISSUE_TEMPLATE/bare_form.yml uses 'enhancement' "
                "instead of a canonical type: label",
                report,
            )
            self.assertFalse(any(line.endswith("no drift detected") for line in report))

    def test_audit_is_clean_for_the_scaffolded_issue_forms_and_survives_unreadable_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_github_templates=True)
            report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("legacy label:") for line in report))
            self.assertTrue(any(line.endswith("no drift detected") for line in report))

            directory = target / ".github/ISSUE_TEMPLATE"
            (directory / "binary.yml").write_bytes(b"\xff\xfe\x00labels: bug\n")
            outside = target / "outside.yml"
            outside.write_text("labels: bug\n", encoding="utf-8")
            try:
                (directory / "link.yml").symlink_to(outside)
            except OSError:
                pass
            (directory / "subdir.yml").mkdir()

            report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("legacy label:") for line in report))

    def test_audit_without_an_issue_template_directory_reports_no_legacy_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            sync.synchronize(PACK_ROOT, target, "minimal")
            report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("legacy label:") for line in report))

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
            readme_asset = next(a for a in manifest.assets if a.path.endswith("readme.template.md"))
            source_body = sync.template_body(PACK_ROOT / "files" / readme_asset.path)

            # Verified current scaffold: exactly what the sync path would produce.
            sync.synchronize(PACK_ROOT, target, "minimal", scaffold_project_files=True)
            current_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("outdated scaffold:") for line in current_report))
            self.assertFalse(any(line.startswith("info:") and "README.md" in line for line in current_report))

            # Locally customized scaffold (provenance present but content has since
            # changed) must never be reported as "outdated"; at most informational.
            readme = target / readme_asset.scaffold_target
            readme.write_text(
                sync.add_source_marker(source_body, readme_asset.path) + "\nSome locally added section.\n",
                encoding="utf-8",
            )
            customized_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any(line.startswith("outdated scaffold:") for line in customized_report))
            self.assertTrue(
                any(
                    line.startswith("info:") and "README.md" in line and "customized" in line
                    for line in customized_report
                )
            )
            self.assertFalse(any("README.md" in line for line in customized_report if line.startswith("drift:")))

            # Fully customized/hand-written scaffold with no repo-seed markers at all:
            # no provenance to evaluate, so no warning of any kind.
            readme.write_text("# Our own readme\n", encoding="utf-8")
            no_provenance_report = sync.audit_target(PACK_ROOT, target, "minimal")
            self.assertFalse(any("README.md" in line for line in no_provenance_report))

            # Invalid/mismatched provenance: source marker points at the wrong template.
            other_asset = next(a for a in manifest.assets if a.path.endswith("changelog.template.md"))
            mismatched = sync.add_source_marker(source_body, other_asset.path)
            readme.write_text(mismatched, encoding="utf-8")
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
            archive = tooling.build_archive(REPOSITORY_ROOT, output)
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
                self.assertNotIn("scripts/repo-seed.py", bundle.namelist())

    def test_extracted_archive_auto_discovers_source_and_syncs_every_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            archive = tooling.build_archive(REPOSITORY_ROOT, temp_root)
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
                core_skills = {
                    "code-review",
                    "bug-fix",
                    "code-simplification",
                    "refactor",
                    "dependency-upgrade",
                    "repository-audit",
                    "repository-bootstrap",
                    "repository-upgrade",
                    "issue-authoring",
                    "issue-implementation",
                    "test-driven-development",
                }
                extended_skills = {"technical-design", "documentation-bootstrap", "architecture-review"}
                expected_skills = core_skills
                if profile != "minimal":
                    expected_skills |= extended_skills
                for root in (".agents/skills",):
                    actual_skills = {
                        path.parent.name
                        for path in (target / root).glob("*/SKILL.md")
                    }
                    self.assertEqual(actual_skills, expected_skills, f"{profile}: {root}")
                self.assertTrue((target / ".editorconfig").is_file())
                self.assertTrue((target / ".github/ISSUE_TEMPLATE/feature_request.yml").is_file())
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
                tooling.contained_file(pack / "files", "linked.md", "Release source")

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
                tooling.build_archive(root, root / "dist")

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
            with self.assertRaisesRegex(ValueError, "Package file does not exist"):
                tooling.build_archive(root, root / "dist")

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
        catalog = tooling.load_catalog(GITHUB_LABELS_CATALOG)
        names = {label["name"] for label in catalog}
        self.assertEqual(
            names,
            {
                "type: bug",
                "type: feature",
                "type: tech-debt",
                "type: chore",
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
                tooling.load_catalog(path)

            path.write_text(json.dumps({"labels": [{"name": "type: bug"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "description"):
                tooling.load_catalog(path)

    def test_catalog_rejects_a_non_object_root(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "labels.json"
            for content in ([], "invalid"):
                path.write_text(json.dumps(content), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "JSON object"):
                    tooling.load_catalog(path)

    def test_label_mutation_failures_raise_a_clear_error(self):
        failed = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr="HTTP 403")
        label = {"name": "type: bug", "description": "x", "color": "d73a4a"}
        for function, operation in ((tooling.create_label, "create"), (tooling.update_label, "edit")):
            with mock.patch.object(subprocess, "run", return_value=failed):
                with self.assertRaisesRegex(RuntimeError, f"gh label {operation} failed for 'type: bug': HTTP 403"):
                    function("gh", None, label)

    def test_main_reports_a_failed_apply_mutation_without_a_traceback(self):
        hosted = subprocess.CompletedProcess(["gh"], 0, stdout="[]", stderr="")
        failed = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr="HTTP 403")
        stderr = io.StringIO()
        with mock.patch.object(shutil, "which", return_value="gh"), mock.patch.object(
            subprocess, "run", side_effect=[hosted, failed]
        ), contextlib.redirect_stderr(stderr):
            result = tooling.main(["labels", "--apply", "--catalog", str(GITHUB_LABELS_CATALOG)])
        self.assertEqual(result, 2)
        self.assertIn("error: gh label create failed for", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

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

        findings = tooling.audit(catalog, hosted)

        self.assertTrue(any(finding == "missing: type: feature" for finding in findings))
        self.assertTrue(any("drift: type: bug" in finding for finding in findings))
        self.assertTrue(any("legacy label: 'bug'" in finding for finding in findings))
        self.assertFalse(any("component: cli" in finding for finding in findings))

    def test_audit_reports_no_findings_for_a_matching_catalog(self):
        catalog = tooling.load_catalog(GITHUB_LABELS_CATALOG)
        # Hosted copies differ in colour case and carry an unrelated project label.
        hosted = [{**label, "color": label["color"].upper()} for label in catalog]
        hosted.append({"name": "component: cli", "description": "project-specific", "color": "ffffff"})
        self.assertEqual(tooling.audit(catalog, hosted), [])

    def test_label_names_match_case_insensitively_and_apply_renames_to_the_catalog_spelling(self):
        catalog = [{"name": "type: bug", "description": "d", "color": "d73a4a"}]
        hosted = [{"name": "Type: Bug", "description": "d", "color": "d73a4a"}]
        self.assertEqual(tooling.audit(catalog, hosted), ["drift: type: bug differs from the canonical catalog"])
        done = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(tooling.subprocess, "run", return_value=done) as run:
            report = tooling.apply_catalog("gh", "o/r", catalog, hosted)
        self.assertEqual(report, ["updated: type: bug"])
        self.assertEqual(
            run.call_args.args[0],
            ["gh", "label", "edit", "Type: Bug", "--description", "d", "--name", "type: bug", "--color", "d73a4a", "--repo", "o/r"],
        )

    def test_a_null_hosted_colour_is_drift_not_a_crash(self):
        catalog = [{"name": "type: bug", "description": "d", "color": "d73a4a"}]
        hosted = [{"name": "type: bug", "description": "d", "color": None}]
        self.assertEqual(tooling.audit(catalog, hosted), ["drift: type: bug differs from the canonical catalog"])

    def test_create_and_update_pass_colour_and_repository_to_gh(self):
        label = {"name": "type: bug", "description": "d", "color": "d73a4a"}
        done = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(tooling.subprocess, "run", return_value=done) as run:
            tooling.create_label("gh", "o/r", label)
            tooling.update_label("gh", None, label)
        created, updated = (call.args[0] for call in run.call_args_list)
        self.assertEqual(created, ["gh", "label", "create", "type: bug", "--description", "d", "--color", "d73a4a", "--repo", "o/r"])
        self.assertEqual(updated, ["gh", "label", "edit", "type: bug", "--description", "d", "--color", "d73a4a"])
        for call in run.call_args_list:
            self.assertEqual(call.kwargs.get("encoding"), "utf-8")

    def test_check_exits_1_on_drift_and_0_when_clean(self):
        catalog = tooling.load_catalog(GITHUB_LABELS_CATALOG)
        for hosted, expected, output in (
            (catalog, 0, "no drift detected"),
            (catalog[1:], 1, "missing: " + catalog[0]["name"]),
        ):
            with self.subTest(expected=expected):
                out = io.StringIO()
                with mock.patch.object(tooling, "require_gh", return_value="gh"), mock.patch.object(
                    tooling, "fetch_hosted_labels", return_value=hosted
                ), contextlib.redirect_stdout(out):
                    code = tooling.main(["labels", "--check", "--catalog", str(GITHUB_LABELS_CATALOG)])
                self.assertEqual(code, expected)
                self.assertIn(output, out.getvalue())

    def test_a_possibly_truncated_label_list_is_refused(self):
        listing = json.dumps([{"name": f"l{i}", "description": "", "color": "ffffff"} for i in range(tooling.LABEL_LIST_LIMIT)])
        done = subprocess.CompletedProcess([], 0, listing, "")
        with mock.patch.object(tooling.subprocess, "run", return_value=done):
            with self.assertRaisesRegex(RuntimeError, "may be truncated"):
                tooling.fetch_hosted_labels("gh", None)

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

        with mock.patch.object(tooling, "create_label") as create, mock.patch.object(
            tooling, "update_label"
        ) as update:
            report = tooling.apply_catalog("gh", None, catalog, hosted)

        create.assert_called_once_with("gh", None, catalog[1])
        update.assert_called_once_with("gh", None, catalog[0], "type: bug")
        self.assertTrue(any("created: type: feature" in line for line in report))
        self.assertTrue(any("updated: type: bug" in line for line in report))
        self.assertTrue(any("legacy label present, not removed: 'enhancement'" in line for line in report))
        self.assertFalse(any("component: cli" in line for line in report))

    def test_cli_check_and_apply_are_mutually_exclusive(self):
        parser = tooling.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["labels"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["labels", "--check", "--apply"])

    def test_main_reports_a_clear_error_without_the_github_cli(self):
        with mock.patch.object(shutil, "which", return_value=None):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                result = tooling.main(["labels", "--check", "--catalog", str(GITHUB_LABELS_CATALOG)])
        self.assertEqual(result, 2)
        self.assertIn("GitHub CLI", err.getvalue())

    def test_cli_help_documents_check_and_apply(self):
        result = subprocess.run(
            [sys.executable, str(TOOLING), "labels", "--help"],
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


class RepositoryUpgradeScenarioTests(unittest.TestCase):
    """Representative upgrades, run the way the repository-upgrade skill directs.

    The newer pack's own sync script runs with no --profile or --conventions
    (recorded selections are reused), first as --dry-run, then for real, then
    as a repeat --dry-run.
    """

    @staticmethod
    def newer_pack(
        root: Path,
        remove: tuple[str, ...] = (),
        edit: dict[str, str] | None = None,
        reprofile: dict[str, list[str]] | None = None,
    ) -> Path:
        pack = root / "newer-pack"
        shutil.copytree(PACK_ROOT, pack, ignore=shutil.ignore_patterns("__pycache__"))
        manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
        manifest["pack_version"] = "9.0.0"
        manifest["assets"] = [a for a in manifest["assets"] if a["path"] not in remove]
        for asset in manifest["assets"]:
            if asset["path"] in (reprofile or {}):
                asset["profiles"] = reprofile[asset["path"]]
        (pack / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for path in remove:
            (pack / "files" / path).unlink()
        for path, text in (edit or {}).items():
            (pack / "files" / path).write_text(text, encoding="utf-8")
        return pack

    @staticmethod
    def run_sync(pack: Path, target: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(pack / "files/scripts/sync-docs.py"), "--source", str(pack), "--target", str(target), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def snapshot(target: Path) -> dict[Path, bytes]:
        return {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}

    def installed(self, root: Path, profile: str = "app", conventions: str = "python") -> Path:
        target = root / "target"
        target.mkdir()
        sync.synchronize(PACK_ROOT, target, profile, conventions=frozenset(conventions.split(",")))
        return target

    def test_current_schema_upgrade_to_the_same_pack_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.installed(root)
            before = self.snapshot(target)

            dry_run = self.run_sync(PACK_ROOT, target, "--dry-run")
            applied = self.run_sync(PACK_ROOT, target)

            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertRegex(dry_run.stdout, r"Removals: 0\. Upgrades: 0\. Managed copies: 0\.")
            self.assertEqual(before, self.snapshot(target))

    def edited_target_and_newer_pack(self, root: Path) -> tuple[Path, Path]:
        """A synced target whose AGENTS.md has a local edit, and a pack that changes only git.md."""
        target = self.installed(root, profile="app", conventions="python")
        with (target / "AGENTS.md").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("local note that the pack does not have\n")
        newer = self.newer_pack(root, edit={".agents/guidelines/git.md": "newer git guidance\n"})
        return target, newer

    def test_dry_run_labels_overwrites_that_discard_local_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target, newer = self.edited_target_and_newer_pack(root)
            before = self.snapshot(target)

            dry_run = self.run_sync(newer, target, "--dry-run")

            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("AGENTS.md (would overwrite managed copy and discard local changes)", dry_run.stdout)
            self.assertIn(".agents/guidelines/git.md (would overwrite managed copy)", dry_run.stdout)
            self.assertNotIn("--- pack/", dry_run.stdout)
            self.assertEqual(before, self.snapshot(target))

    def test_diff_shows_only_the_discarded_local_changes_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target, newer = self.edited_target_and_newer_pack(root)
            before = self.snapshot(target)

            result = self.run_sync(newer, target, "--diff")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry run complete.", result.stdout)
            self.assertIn("--- pack/AGENTS.md", result.stdout)
            self.assertIn("+++ local/AGENTS.md", result.stdout)
            self.assertIn("+local note that the pack does not have", result.stdout)
            self.assertNotIn("pack/.agents/guidelines/git.md", result.stdout)
            self.assertEqual(before, self.snapshot(target))

    def test_a_real_sync_reports_the_local_changes_it_discarded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target, newer = self.edited_target_and_newer_pack(root)

            applied = self.run_sync(newer, target)

            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertIn("AGENTS.md (overwrote managed copy and discarded local changes)", applied.stdout)
            self.assertNotIn("local note", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_changed_managed_content_upgrades_and_keeps_recorded_selections(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.installed(root, profile="app", conventions="python")
            newer = self.newer_pack(root, edit={".agents/guidelines/git.md": "newer git guidance\n"})
            project_file = target / "docs/project/notes.md"
            project_file.parent.mkdir(parents=True, exist_ok=True)
            project_file.write_text("project notes\n", encoding="utf-8")
            before = self.snapshot(target)

            dry_run = self.run_sync(newer, target, "--dry-run")
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn(".agents/guidelines/git.md (would overwrite managed copy)", dry_run.stdout)
            self.assertEqual(before, self.snapshot(target))

            applied = self.run_sync(newer, target)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual((target / ".agents/guidelines/git.md").read_text(encoding="utf-8"), "newer git guidance\n")
            self.assertEqual(project_file.read_text(encoding="utf-8"), "project notes\n")
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["pack_version"], "9.0.0")
            self.assertEqual(state["profile"], "app")
            self.assertEqual(state["conventions"], ["python"])

            repeat = self.run_sync(newer, target, "--dry-run")
            self.assertRegex(repeat.stdout, r"Removals: 0\. Upgrades: 0\. Managed copies: 0\.")
            audit = self.run_sync(newer, target, "--audit")
            self.assertIn("no drift detected", audit.stdout)

    def test_older_state_schema_is_refused_with_the_last_converting_release_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            (target / ".repo-seed-state.json").write_text(json.dumps(schema_1_state(profile="library")), encoding="utf-8")
            before = self.snapshot(target)

            for extra in (("--dry-run",), ("--conventions", "python"), ("--audit",)):
                with self.subTest(args=extra):
                    refused = self.run_sync(PACK_ROOT, target, *extra)
                    self.assertEqual(refused.returncode, 2)
                    self.assertIn("releases/tag/v5.13.2", refused.stderr)
                    self.assertEqual(before, self.snapshot(target))

    def test_assets_the_newer_pack_no_longer_selects_follow_the_ownership_rules(self):
        deselected_unchanged = "docs/templates/tsd.template.md"
        deselected_modified = "docs/templates/architecture.template.md"
        dropped_from_manifest = "docs/templates/user-guide.template.md"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.installed(root, profile="app", conventions="python")
            (target / deselected_modified).write_text("local architecture template edits\n", encoding="utf-8")
            project_readme = target / "README.md"
            project_readme.write_text("project readme\n", encoding="utf-8")
            newer = self.newer_pack(
                root,
                remove=(dropped_from_manifest,),
                reprofile={deselected_unchanged: ["game"], deselected_modified: ["game"]},
            )

            dry_run = self.run_sync(newer, target, "--dry-run")
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn(f"remove         {deselected_unchanged}", dry_run.stdout)
            self.assertTrue((target / deselected_unchanged).is_file())

            applied = self.run_sync(newer, target)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertFalse((target / deselected_unchanged).exists())
            self.assertEqual(
                (target / deselected_modified).read_text(encoding="utf-8"), "local architecture template edits\n"
            )
            self.assertTrue((target / dropped_from_manifest).is_file())
            self.assertEqual(project_readme.read_text(encoding="utf-8"), "project readme\n")
            state = json.loads((target / ".repo-seed-state.json").read_text(encoding="utf-8"))
            self.assertIn(deselected_modified, state["tombstones"])
            self.assertIn(dropped_from_manifest, state["tombstones"])
            self.assertNotIn(deselected_unchanged, state["tombstones"])
            self.assertEqual(state["profile"], "app")
            self.assertEqual(state["conventions"], ["python"])

            audit = self.run_sync(newer, target, "--audit")
            self.assertIn(f"tombstone: {deselected_modified}", audit.stdout)
            self.assertIn(f"tombstone: {dropped_from_manifest}", audit.stdout)


if __name__ == "__main__":
    unittest.main()
