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


SYNC_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "sync.yml"
SYNC_TEMPLATE = REPOSITORY_ROOT / "pack" / "files" / "docs" / "templates" / ".github" / "repo-seed-sync.template.yml"


class SyncWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = SYNC_WORKFLOW.read_text(encoding="utf-8")

    def test_it_is_only_a_reusable_workflow(self):
        block = re.search(r"(?ms)^on:\n(.*?)^\S", self.text + "\nx")
        self.assertIsNotNone(block)
        self.assertEqual(re.findall(r"^  (\w+):", block.group(1), re.M), ["workflow_call"])
        self.assertNotIn("pull_request_target", self.text)

    def test_permissions_are_limited_to_contents_and_pull_requests(self):
        granted = set(re.findall(r"^\s+(\w[\w-]*): (read|write)$", self.text, re.M))
        self.assertEqual(granted, {("contents", "read"), ("contents", "write"), ("pull-requests", "write")})

    def test_the_download_is_verified_and_no_scaffold_or_selection_flag_is_passed(self):
        self.assertIn("sha256sum --check", self.text)
        self.assertEqual(self.text.count('/sync-docs.py"'), 2)
        for flag in ("--scaffold", "--profile", "--conventions"):
            self.assertNotIn(flag + " ", self.text.replace("# Neither step passes", ""))

    def test_the_script_never_runs_with_the_write_token(self):
        checkout = re.search(r"uses: actions/checkout@\S+\n((?:\s+.+\n)+)", self.text)
        self.assertIn("persist-credentials: false", checkout.group(1))
        run_step = re.search(r"- name: Preview and apply the sync\n(.*?)\n      - name:", self.text, re.S).group(1)
        self.assertNotIn("GH_TOKEN", run_step)
        self.assertIn("secrets.token || github.token", self.text)

    def test_it_owns_one_branch_and_never_duplicates_the_pull_request(self):
        self.assertIn("SYNC_BRANCH: chore/repo-seed-sync", self.text)
        self.assertIn("gh pr list --head", self.text)
        self.assertIn("gh pr edit", self.text)
        self.assertIn("gh pr create", self.text)
        self.assertIn("gh pr close", self.text)
        self.assertRegex(self.text, r"(?m)^concurrency:\n  group: .*github\.repository.*\n  cancel-in-progress: false$")

    def test_a_repository_without_state_or_off_the_default_branch_is_skipped(self):
        self.assertIn("-f .repo-seed-state.json", self.text)
        self.assertIn("defaultBranchRef", self.text)

    def test_the_pinned_version_is_validated_before_use(self):
        self.assertIn("PACK_VERSION_INPUT", self.text)
        self.assertIn("[0-9]+\\.[0-9]+\\.[0-9]+", self.text)

    def test_the_caller_template_matches_the_workflow(self):
        template = SYNC_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("Trawis/repo-seed/.github/workflows/sync.yml@v__PACK_VERSION__", template)
        self.assertIn("contents: write", template)
        self.assertIn("pull-requests: write", template)
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Trawis/repo-seed/.github/workflows/sync.yml@v", readme)


if __name__ == "__main__":
    unittest.main()
