from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "changelog-notes.py"

SAMPLE = """# Changelog

Intro text.

## 2.0.0 - 2026-02-01

Newest entry.

Second paragraph.

## 1.1.0 - 2026-01-15

Middle entry.

## 1.0.0 - 2026-01-01

Oldest entry.
"""


def load_module():
    spec = importlib.util.spec_from_file_location("changelog_notes", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


notes = load_module()


class ChangelogNotesTests(unittest.TestCase):
    def test_returns_only_the_requested_entry_body(self):
        self.assertEqual(notes.entry_for(SAMPLE, "2.0.0"), "Newest entry.\n\nSecond paragraph.")
        self.assertEqual(notes.entry_for(SAMPLE, "1.1.0"), "Middle entry.")
        self.assertEqual(notes.entry_for(SAMPLE, "1.0.0"), "Oldest entry.")

    def test_a_version_prefix_is_not_a_match(self):
        with self.assertRaisesRegex(ValueError, "no entry for version 2.0"):
            notes.entry_for(SAMPLE.replace("## 2.0.0", "## 2.0.01"), "2.0.0")

    def test_a_heading_line_inside_a_code_fence_does_not_end_the_entry(self):
        text = "## 1.0.0 - 2026-01-01\n\nBefore\n\n```md\n## not a heading\n```\n\nAfter\n\n## 0.9.0 - 2025-12-01\n\nold\n"
        self.assertEqual(notes.entry_for(text, "1.0.0"), "Before\n\n```md\n## not a heading\n```\n\nAfter")
        tilde = text.replace("```", "~~~")
        self.assertIn("After", notes.entry_for(tilde, "1.0.0"))

    def test_missing_empty_and_malformed_versions_are_errors(self):
        with self.assertRaisesRegex(ValueError, "no entry"):
            notes.entry_for(SAMPLE, "9.9.9")
        with self.assertRaisesRegex(ValueError, "empty"):
            notes.entry_for("## 1.0.0 - 2026-01-01\n\n## 0.9.0 - 2025-12-01\nx\n", "1.0.0")
        with self.assertRaisesRegex(ValueError, "MAJOR.MINOR.PATCH"):
            notes.entry_for(SAMPLE, "v1.0.0")

    def test_the_command_line_prints_the_entry_or_fails_with_exit_code_2(self):
        changelog = REPOSITORY_ROOT / "CHANGELOG.md"
        version = json.loads((REPOSITORY_ROOT / "pack/manifest.json").read_text(encoding="utf-8"))["pack_version"]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = notes.main([version, "--changelog", str(changelog)])
        self.assertEqual(code, 0, err.getvalue())
        self.assertTrue(out.getvalue().strip())
        self.assertNotIn("\n## ", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(notes.main(["0.0.0", "--changelog", str(changelog)]), 2)

    def test_the_current_pack_version_always_has_a_non_empty_entry(self):
        version = json.loads((REPOSITORY_ROOT / "pack/manifest.json").read_text(encoding="utf-8"))["pack_version"]
        text = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(notes.entry_for(text, version))


if __name__ == "__main__":
    unittest.main()
