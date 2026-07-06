# Upgrading to Version 4

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

Version 4 clarifies documentation lifecycles and removes the implicit `full`
profile default.

## Before Upgrading

1. Commit or back up the target repository.
2. Run the new script with an explicit `minimal`, `library`, `app`, or `game`
   profile and `--dry-run`.
3. Review managed-template removals and additions.
4. Rerun without `--dry-run`.

Existing project-owned files are preserved. Version 4 never automatically
deletes, renames, or rewrites populated `docs/project/architecture.md`,
`docs/project/tsd.md`, or `docs/project/features.md`.

## Documentation Model

- FSD describes accepted application behavior.
- GDD describes accepted gameplay intent.
- Architecture describes the verified current technical system.
- A TSD describes one substantial technical change and lives under
  `docs/project/designs/`.
- User guides describe current user workflows.

The architecture document remains the stable technical entry point as a project
grows. Move detail under `docs/project/architecture/` only when necessary and
link it from the overview.

## Existing TSD and Features Files

Review existing project-owned documents manually:

- keep a populated project-wide TSD when it remains useful, or merge verified
  current-state content into architecture;
- move a change-specific TSD under `docs/project/designs/` only after review;
- keep `features.md` when a public capability index adds value, otherwise merge
  accepted scope into FSD or GDD and keep planned work in issues.

No manual classification is required before syncing because these live files
remain project-owned.

## Profile Behavior

The first version 4 sync requires an explicit profile:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --dry-run
```

Later syncs may omit `--profile`; the script reuses the valid profile recorded
in `.repo-seed-state.json`. Pass a profile explicitly to change it.

`full` synchronizes the complete template catalog for review. It is not a
project type and cannot be used with `--scaffold-project-files`.
