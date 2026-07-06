# Repo Seed Pack

Package-only instructions for the downloadable documentation pack. This file and `LICENSE` are included in the archive but are never synchronized into target repositories.

## First Sync

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --dry-run
```

Choose `minimal`, `library`, `app`, or `game`. The `full` profile synchronizes
the complete reference catalog but cannot scaffold project files. Add only the
scaffolding you need:

```text
--scaffold-project-files
--scaffold-github-templates
--scaffold-editorconfig
```

Review the dry-run output, commit or back up the target repository, then rerun
without `--dry-run`. Unchanged legacy-managed files with recorded hashes may be
removed, managed guidance is updated when different, and modified or unverified
project files are preserved.

Commit the generated `.repo-seed-state.json`. It records managed ownership so a
smaller profile can remove unchanged stale assets while retaining modified files
as tombstones for review.

## Update an Existing Project

Use the sync script already copied into the target with a newer extracted pack:

```bash
python scripts/sync-docs.py \
  --source /path/to/extracted/pack \
  --target . \
  --dry-run
```

The recorded profile is reused when `--profile` is omitted. Pass an explicit
profile to change it.

For complete documentation, visit [repo-seed on GitHub](https://github.com/Trawis/repo-seed).

## License

This pack is distributed under the MIT License. See `LICENSE`.
