from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "audit.yml"


class AuditWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_it_is_only_a_reusable_workflow(self):
        triggers = re.search(r"(?ms)^on:\n(.*?)^\S", self.text + "\nx").group(1)
        self.assertEqual(re.findall(r"^  (\w+):", triggers, re.M), ["workflow_call"])
        self.assertNotIn("pull_request_target", self.text)

    def test_permissions_are_limited_to_reading_contents_and_writing_issues(self):
        granted = set(re.findall(r"^\s+(\w[\w-]*): (read|write)$", self.text, re.M))
        self.assertEqual(granted, {("contents", "read"), ("issues", "write")})

    def test_the_download_is_verified_and_the_audit_changes_no_files(self):
        self.assertIn("sha256sum --check", self.text)
        # The only invocation of the script is a read-only audit of the caller.
        self.assertEqual(self.text.count('/sync-docs.py"'), 1)
        self.assertIn('--target "$GITHUB_WORKSPACE" --audit', self.text)

    def test_the_readme_caller_matches_the_workflow_path(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Trawis/repo-seed/.github/workflows/audit.yml@v", readme)
        self.assertIn("issues: write", readme)


if __name__ == "__main__":
    unittest.main()
