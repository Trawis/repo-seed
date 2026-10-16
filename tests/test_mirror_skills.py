from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "mirror-skills.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mirror_skills", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mirror = load_module()


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mirror.main(list(args))
    return code, out.getvalue(), err.getvalue()


class MirrorSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name)
        self.source = self.pack / ".agents/skills"
        self.mirror = self.pack / ".claude/skills"

    def test_repository_skill_trees_match(self):
        code, output, _ = run("--check")
        self.assertEqual(code, 0, output)

    def test_check_reports_missing_different_and_stale_without_changing_files(self):
        write(self.pack, ".agents/skills/a/SKILL.md", "a\n")
        write(self.pack, ".agents/skills/b/SKILL.md", "b new\n")
        write(self.pack, ".claude/skills/b/SKILL.md", "b old\n")
        write(self.pack, ".claude/skills/gone/SKILL.md", "gone\n")
        code, output, _ = run("--pack-files", str(self.pack), "--check")
        self.assertEqual(code, 1)
        self.assertIn("missing: a/SKILL.md", output)
        self.assertIn("different: b/SKILL.md", output)
        self.assertIn("stale: gone/SKILL.md", output)
        self.assertFalse((self.mirror / "a/SKILL.md").exists())
        self.assertEqual((self.mirror / "b/SKILL.md").read_text(encoding="utf-8"), "b old\n")
        self.assertTrue((self.mirror / "gone/SKILL.md").exists())

    def test_apply_makes_the_mirror_identical_and_leaves_the_source_alone(self):
        write(self.pack, ".agents/skills/a/SKILL.md", "a\n")
        write(self.pack, ".agents/skills/a/NOTICE.md", "notice\r\n")
        write(self.pack, ".claude/skills/a/SKILL.md", "stale\n")
        write(self.pack, ".claude/skills/gone/SKILL.md", "gone\n")
        code, _, _ = run("--pack-files", str(self.pack), "--apply")
        self.assertEqual(code, 0)
        self.assertEqual((self.mirror / "a/SKILL.md").read_bytes(), b"a\n")
        self.assertEqual((self.mirror / "a/NOTICE.md").read_bytes(), b"notice\r\n")
        self.assertFalse((self.mirror / "gone").exists())
        self.assertEqual((self.source / "a/SKILL.md").read_bytes(), b"a\n")
        code, output, _ = run("--pack-files", str(self.pack), "--check")
        self.assertEqual((code, output.strip()), (0, "skill trees match"))

    def test_apply_is_idempotent(self):
        write(self.pack, ".agents/skills/a/SKILL.md", "a\n")
        run("--pack-files", str(self.pack), "--apply")
        code, output, _ = run("--pack-files", str(self.pack), "--apply")
        self.assertEqual(code, 0)
        self.assertIn("already match", output)

    def test_missing_source_tree_is_an_error(self):
        code, _, error = run("--pack-files", str(self.pack), "--check")
        self.assertEqual(code, 2)
        self.assertIn("Source skill tree not found", error)

    def test_symlinks_are_rejected(self):
        write(self.pack, ".agents/skills/a/SKILL.md", "a\n")
        link = self.source / "a/link.md"
        try:
            link.symlink_to(self.source / "a/SKILL.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not available")
        code, _, error = run("--pack-files", str(self.pack), "--check")
        self.assertEqual(code, 2)
        self.assertIn("Symlinks are not supported", error)

    def test_mode_is_required(self):
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            mirror.main([])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
