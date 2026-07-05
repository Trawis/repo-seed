# Upgrading 1.x or 2.x to Version 3

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

Version 3 replaces the stateful 1.x/2.x synchronizer with a self-contained pack and predictable managed-file copying.

Version note: sync script `1.7.0` shipped with pack `1.31.0`. Check `.agent-guidelines-version` or `PACK_VERSION` in the old script when identifying an installation. Repositories can upgrade directly to version 3 without installing intermediate releases.

## Before Upgrading

1. Commit or back up the target repository.
2. Review local changes to files previously managed by repo-seed.
3. Download and extract the latest `repo-seed-pack-<version>.zip`.
4. Run the new script with `--dry-run`.

Version 3 overwrites selected managed guidance and templates. It does not migrate, delete, or back up legacy files.

## Ownership Changes

- Root `AGENTS.md` and `CLAUDE.md` remain managed and are overwritten.
- `.agents/`, `docs/templates/`, and `scripts/sync-docs.py` contain the new managed files.
- Root `README.md`, `CHANGELOG.md`, `.gitignore`, and `.editorconfig` are project-owned.
- `docs/project/` contains live project documentation.
- Existing pull-request and issue templates are project-owned; scaffolding creates only missing issue files.

If a 1.x repository has root `FEATURES.md`, review and merge relevant content into `docs/project/features.md` when that document is useful. Do not delete project content merely because its old location is no longer scaffolded.

## Review Legacy Files

After comparing local changes, remove these paths only when they came from repo-seed and contain no project-specific content:

```text
.agent-guidelines-version
.agent-guidelines-manifest.json
.agent-guidelines-conflicts/
scripts/sync-agent-guidelines.py
.agents/ci-cd-guidelines.md
docs/*-template.md
docs/coding-conventions-*.md
docs/ci-cd-guidelines.md
```

Do not remove unknown files, live project documentation, customized templates, or an existing `.editorconfig` without reviewing them.

## Run Version 3

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --dry-run
```

Choose the appropriate profile and review the output. Add scaffold flags only for missing project-owned files:

```text
--scaffold-project-files
--scaffold-github-templates
--scaffold-editorconfig
```

Rerun without `--dry-run` after reviewing the managed overwrites and scaffold destinations.

For later updates, follow [Update an Existing Project](../../README.md#update-an-existing-project).
