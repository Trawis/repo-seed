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

Prefer the script from the newly extracted pack so the newest validation runs
before any target file is inspected or changed:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --dry-run
```

A recorded `minimal`, `library`, `app`, or `game` profile is reused when
`--profile` is omitted. The `full` catalog must always be selected explicitly.
The copied target script remains available for compatible packs, but it cannot
cross manifest-schema changes and may not contain the newest preflight fixes.

## Upgrade from Version 3

Version 3 scripts cannot read the version 4 manifest. Run the new pack's script
for the first version 4 sync:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --profile app \
  --dry-run
```

For complete documentation, visit [repo-seed on GitHub](https://github.com/Trawis/repo-seed).

## License

This pack is distributed under the MIT License. See `LICENSE`.
