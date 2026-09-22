# Repo Seed Pack

Package-only instructions for the downloadable documentation pack. This file and `LICENSE` are included in the archive but are never synchronized into target repositories.

## First Sync

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --conventions csharp \
  --dry-run
```

Choose `minimal`, `library`, `app`, or `game`. Select any language/tool
conventions your project actually uses (`csharp`, `python`, `scripts`,
`shell`, `unity`) with `--conventions`; a fresh sync installs none if
omitted. Add only the scaffolding you need:

```text
--scaffold-project-files          # baseline README/CHANGELOG
--scaffold-github-templates       # bug/feature issue templates
--scaffold-editorconfig           # .editorconfig
--scaffold <name>                 # one on-demand document: architecture, fsd, gdd, user-guide
```

Review the dry-run output, commit or back up the target repository, then rerun
without `--dry-run`. Managed guidance is updated only when different, and
modified or unverified project files are preserved.

The `.github/workflows/` tree is always project-owned and cannot be managed,
scaffolded, or deleted by this pack.

Commit the generated `.repo-seed-state.json`. It records managed ownership so a
smaller profile or a changed convention selection can remove unchanged stale
assets while retaining modified files as tombstones for review.

## Update an Existing Project

Prefer the script from the newly extracted pack so the newest validation runs
before any target file is inspected or changed:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --dry-run
```

A recorded `minimal`, `library`, `app`, or `game` profile and its convention
selection are reused when `--profile` / `--conventions` are omitted. The
copied target script remains available for compatible packs, but it cannot
cross manifest-schema changes and may not contain the newest preflight fixes.

## Upgrading a Pre-5.0 Target

Version 5 is a compatibility reset: its manifest and state schemas are not
compatible with older packs. A target with a `.repo-seed-state.json` written
before explicit conventions existed requires one `--conventions <list>` sync
to convert:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --profile app \
  --conventions csharp \
  --dry-run
```

For complete documentation, visit [repo-seed on GitHub](https://github.com/Trawis/repo-seed).

## License

This pack is distributed under the MIT License. See `LICENSE`.
