from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_top_changelog_entry_matches_the_pack_version(self):
        manifest = json.loads((REPOSITORY_ROOT / "pack/manifest.json").read_text(encoding="utf-8"))
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        top = re.search(r"(?m)^## .+$", changelog)
        self.assertIsNotNone(top, "CHANGELOG.md has no version headings")
        match = re.fullmatch(r"## (\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}", top.group(0))
        self.assertIsNotNone(match, f"Top changelog heading is not 'X.Y.Z - YYYY-MM-DD': {top.group(0)}")
        self.assertEqual(match.group(1), manifest["pack_version"])


if __name__ == "__main__":
    unittest.main()
