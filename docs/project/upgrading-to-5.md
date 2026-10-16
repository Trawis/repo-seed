# Upgrading to Version 5

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

Version 5 is a deliberate compatibility reset. Targets already use
`.repo-seed-state.json`, so pre-4.x migration support is removed.

## What Changed

- The manifest moved to `schema_version: 3`. Older and newer scripts cannot read
  each other's manifests.
- The `full` profile is gone. Use `minimal`, `library`, `app`, or `game`.
- Pre-4.x migration is removed. A target with no state file is a fresh install.
- Convention detection is gone. Conventions (`csharp`, `python`, `scripts`,
  `shell`, `unity`) are always explicit.

## Upgrading a Pre-5.0 Target

The existing `.repo-seed-state.json` already records the profile and managed
hashes.

1. Commit or back up the target repository.
2. Decide which conventions the project uses (see
   [README](../../README.md#profiles-conventions-and-scaffolds)).
3. Run the 5.13.2 `sync-docs.py` (the last pack that converts schema 1; later
   packs refuse a `schema_version: 1` state) with the existing profile and
   `--conventions`:

   ```bash
   python pack/files/scripts/sync-docs.py \
     --target /path/to/project \
     --profile app \
     --conventions csharp \
     --dry-run
   ```

   Without `--conventions`, a `schema_version: 1` state fails and writes
   nothing.
4. Review the output, then rerun without `--dry-run`.

Project-owned files (README, CHANGELOG, `docs/project/`, issue templates, the
PR template, `.agents/project.md`, child `AGENTS.md` files) are kept. Only
managed files update. Afterwards the state is `schema_version: 2`, and later
syncs need no `--conventions` unless the selection changes.

Each project chooses its own profile and conventions. Repo-seed does not infer
them.
