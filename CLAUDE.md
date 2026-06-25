# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## What This Repository Is

`repo-seed` is a centralized source for AI coding agent guidelines. Its purpose is to be synced into other repositories — it is not itself an application. There is no build step, no test suite, and no runtime beyond the sync script.

The authoritative agent rules live in `AGENTS.md`. `CLAUDE.md` (this file) imports them and adds Claude Code-specific context.

## Key Commands

```bash
# Preview what would change when syncing into a target repo
python scripts/sync-agent-guidelines.py --target /path/to/target --dry-run

# Sync with a specific profile
python scripts/sync-agent-guidelines.py --source . --target /path/to/target --profile minimal
python scripts/sync-agent-guidelines.py --source . --target /path/to/target --profile library
python scripts/sync-agent-guidelines.py --source . --target /path/to/target --profile app
python scripts/sync-agent-guidelines.py --source . --target /path/to/target --profile game
python scripts/sync-agent-guidelines.py --source . --target /path/to/target  # full (default)

# Exclude a file (e.g. skip overwriting .editorconfig)
python scripts/sync-agent-guidelines.py --target /path/to/target --skip-editorconfig

# Copy project doc templates only when absent in the target
python scripts/sync-agent-guidelines.py --target /path/to/target --include-project-docs

# See all options
python scripts/sync-agent-guidelines.py --help
```

## Architecture

### Profile and file-list system

`scripts/sync-agent-guidelines.py` defines four private file lists (`_BASE_FILES`, `_CONVENTION_FILES`, `_SPEC_FILES`, `_GAME_FILES`) combined into a `PROFILES` dict. The `release.yml` workflow duplicates these lists to build profile ZIPs — both must be kept in sync when adding or removing managed files.

| Profile | Contents |
|---------|----------|
| `minimal` | `_BASE_FILES` only |
| `library` | + `_CONVENTION_FILES` |
| `app` | + `_SPEC_FILES` |
| `game` | + `_GAME_FILES` (no spec files) |
| `full` | all four lists (default) |

### Conflict detection via manifest

When the script runs against a target repo it writes `.agent-guidelines-manifest.json` into that target, recording the SHA-256 of every file it placed there. On the next sync run it compares hashes: if a target file has been locally modified since the last sync, the incoming version is written to `.agent-guidelines-conflicts/` instead of overwriting.

### Version sources

The pack version is tracked in three places that must stay in sync on every release:

1. `.agent-guidelines-version` — plain text, read by `release.yml` to name the GitHub release tag
2. `PACK_VERSION` in `scripts/sync-agent-guidelines.py` — embedded in `.agent-guidelines-manifest.json` written to target repos
3. The version header and version history table in `AGENTS.md`

`CHANGELOG.md` and `FEATURES.md` should also be updated on every release.

### Release workflow

Pushing to `main` triggers `.github/workflows/release.yml`. It reads `.agent-guidelines-version`, skips if that tag already exists on GitHub, builds one ZIP per profile into `dist/`, and creates a tagged GitHub Release with all ZIPs attached.

## Syncing Into Another Repository

```bash
# From the target repo:
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target . --dry-run --profile <profile>
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target . --profile <profile>
# Then: review diff → resolve .agent-guidelines-conflicts/ if any → commit → push → PR to main
```

The script creates a `feature/sync-agent-guidelines-<version>` branch automatically. It never commits, pushes, or opens a PR.
