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
        block = re.search(r"(?ms)^on:\n(.*?)^\S", self.text + "\nx")
        self.assertIsNotNone(block, "audit.yml has no top-level on: block")
        self.assertEqual(re.findall(r"^  (\w+):", block.group(1), re.M), ["workflow_call"])
        self.assertNotIn("pull_request_target", self.text)

    def test_permissions_are_limited_to_reading_contents_and_writing_issues(self):
        granted = set(re.findall(r"^\s+(\w[\w-]*): (read|write)$", self.text, re.M))
        self.assertEqual(granted, {("contents", "read"), ("issues", "write")})

    def test_the_download_is_verified_and_the_audit_changes_no_files(self):
        self.assertIn("sha256sum --check", self.text)
        # The only invocation of the script is a read-only audit of the caller.
        self.assertEqual(self.text.count('/sync-docs.py"'), 1)
        self.assertIn('--target "$GITHUB_WORKSPACE" --audit', self.text)

    def test_the_checkout_does_not_persist_the_token_and_runs_are_serialized(self):
        checkout = re.search(r"uses: actions/checkout@\S+\n((?:\s+.+\n)+)", self.text)
        self.assertIsNotNone(checkout, "audit.yml has no checkout step")
        self.assertIn("persist-credentials: false", checkout.group(1))
        self.assertRegex(self.text, r"(?m)^concurrency:\n  group: .*github\.repository.*\n  cancel-in-progress: false$")

    def test_a_repository_without_state_or_issues_is_skipped_not_failed(self):
        self.assertIn("-f .repo-seed-state.json", self.text)
        self.assertIn("hasIssuesEnabled", self.text)
        self.assertIn("--limit 1000", self.text)

    def test_the_release_is_tagged_at_the_tested_commit(self):
        release = (REPOSITORY_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn('--target "$GITHUB_SHA"', release)

    def test_the_readme_caller_matches_the_workflow_path(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Trawis/repo-seed/.github/workflows/audit.yml@v", readme)
        self.assertIn("issues: write", readme)


if __name__ == "__main__":
    unittest.main()
