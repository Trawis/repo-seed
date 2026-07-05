# Upgrading to Version 3

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

Version 3 replaces the stateful 2.x synchronizer with a self-contained pack and unconditional managed-file copying.

## Before Upgrading

1. Commit or back up the target repository.
2. Review local changes to managed files.
3. Download and extract the latest `repo-seed-pack-<version>.zip`.
4. Run the new script with `--dry-run`.

The new synchronizer does not migrate, delete, or back up old files.

## Remove Obsolete 2.x Tooling

After reviewing the repository, remove these obsolete paths when they came from repo-seed and are no longer needed:

```text
.agent-guidelines-version
.agent-guidelines-manifest.json
.agent-guidelines-conflicts/
scripts/sync-agent-guidelines.py
```

Do not remove project-owned files merely because an older pack once managed them. In version 3, `.editorconfig`, `.gitignore`, root `README.md`, root `CHANGELOG.md`, and `docs/project/` are project-owned.

## Run Version 3

From the extracted archive:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile full \
  --dry-run
```

Review the output, then rerun without `--dry-run`.

Use the optional scaffold flags only for missing project-owned files:

```text
--scaffold-project-files
--scaffold-github-templates
--scaffold-editorconfig
```

Future updates can run the managed `scripts/sync-docs.py` in the target repository with `--source /path/to/extracted/pack`.
