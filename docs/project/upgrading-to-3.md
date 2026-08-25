# Migrating from Version 1 or 2

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

The current pack replaces the conflict-heavy 1.x/2.x synchronizer with a
self-contained pack and predictable managed-file synchronization. Version 3
introduced this model; version 4 retains the legacy migration path.

Version note: sync script `1.7.0` shipped with pack `1.31.0`. Check
`.agent-guidelines-version` or `PACK_VERSION` in the old script when identifying
an installation. Repositories can upgrade directly to the current pack without
installing intermediate releases.

## Before Upgrading

1. Commit or back up the target repository.
2. Review local changes to files previously managed by repo-seed.
3. Download and extract the latest `repo-seed-pack-<version>.zip`.
4. Run the new script with `--dry-run`.

Version 3 reads the legacy version and hash manifest before updating selected
managed guidance and templates. Dry-run output lists safe removals, verified
scaffold upgrades, and files preserved for review.

Current syncs create `.repo-seed-state.json`. Commit this small ownership file:
it records active managed hashes and tombstones for modified stale assets.

## Ownership Changes

- Root `AGENTS.md` and `CLAUDE.md` remain managed and are updated when pack content differs.
- `.agents/`, `docs/templates/`, and `scripts/sync-docs.py` contain the new managed files.
- Root `README.md`, `CHANGELOG.md`, `.gitignore`, and `.editorconfig` are project-owned.
- `docs/project/` contains live project documentation.
- Existing pull-request and issue templates are project-owned; scaffolding creates
  missing issue files and may upgrade verified unchanged Markdown issue files.

If a 1.x repository has root `FEATURES.md`, review and merge relevant content into `docs/project/features.md` when that document is useful. Do not delete project content merely because its old location is no longer scaffolded.

## Legacy Cleanup

The synchronizer removes these legacy pack paths only when their current content matches the hash recorded by the old synchronizer:

```text
.agent-guidelines-version
scripts/sync-agent-guidelines.py
.agents/ci-cd-guidelines.md
docs/*-template.md
docs/coding-conventions-*.md
docs/ci-cd-guidelines.md
```

Locally modified files, paths missing from the legacy manifest, symbolic links, and non-file paths are preserved and reported. The old manifest remains until every retired path is resolved.

Legacy conflict output is never deleted automatically. Unknown files and live
project documentation are preserved. Existing `.gitignore`, `.editorconfig`,
and pull-request templates are explicitly reported as protected project-owned
files; existing issue templates are also preserved.

Known untouched 1.31 project scaffolds and files with valid repo-seed provenance markers can be upgraded when their scaffold group is requested. Modified project documents remain unchanged.

Changing to a smaller profile removes current managed assets only when their
content still matches the recorded pack hash. Modified stale assets are
preserved and remain tombstoned in `.repo-seed-state.json`.

## Run the Current Pack

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --dry-run
```

Choose the appropriate profile and review the output. Add scaffold flags for
project-owned files you want to create or verify for a safe Markdown upgrade:

```text
--scaffold-project-files
--scaffold-github-templates
--scaffold-editorconfig
```

Rerun without `--dry-run` after reviewing removals, preservation warnings,
managed updates, state changes, and scaffold destinations.

After the first current-pack sync, follow
[Update an Existing Project](../../README.md#update-an-existing-project).
