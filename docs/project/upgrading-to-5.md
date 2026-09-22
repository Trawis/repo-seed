# Upgrading to Version 5

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

Version 5 is a deliberate compatibility reset, not an accidental regression.
The active repository fleet already uses `.repo-seed-state.json`, so
pre-4.x legacy migration support (`.agent-guidelines-manifest.json` and
friends, retired-path tables, ancient scaffold-upgrade tables) has been
removed rather than carried forward indefinitely.

## What Changed

- The manifest moved from `schema_version: 2` to `schema_version: 3`; a 5.0
  sync script cannot read an older manifest, and an older script cannot read
  a 5.0 manifest.
- The `full` profile is gone. Use `minimal`, `library`, `app`, or `game`.
- Pre-4.x legacy migration (any mechanism older than
  `.repo-seed-state.json`) is no longer supported. A target with no state
  file is simply a fresh install.
- Automatic convention detection is gone. Conventions
  (`csharp`, `python`, `scripts`, `shell`, `unity`) are always explicit.

## Upgrading a Pre-5.0 Target

A target's existing `.repo-seed-state.json` already records its profile and
managed-file hashes, so nothing needs to be rediscovered:

1. Commit or back up the target repository.
2. Decide which conventions the project actually uses (see
   [README](../../README.md#profiles-conventions-and-scaffolds) for
   examples).
3. Run the 5.0 `sync-docs.py` with the existing profile and an explicit
   `--conventions`:

   ```bash
   python pack/files/scripts/sync-docs.py \
     --target /path/to/project \
     --profile app \
     --conventions csharp \
     --dry-run
   ```

   Omitting `--conventions` on a pre-5.0 (`schema_version: 1`) state fails
   clearly and writes nothing:

   ```text
   This repository uses a pre-5.0 repo-seed state without explicit conventions.
   Rerun with --conventions <list>.
   ```
4. Review the output, then rerun without `--dry-run`.

Project-owned files (README, CHANGELOG, `docs/project/`, issue templates,
the PR template, `.agents/project.md`, child `AGENTS.md` files) are
preserved exactly as before; only managed files update. Once the sync
succeeds, `.repo-seed-state.json` is `schema_version: 2` and later syncs
need no `--conventions` unless changing the selection.

This is a per-repository decision: each active project chooses its own
profile and conventions when it is upgraded. Repo-seed does not infer or
hard-code them.
