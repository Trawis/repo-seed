# Document Ownership

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

This document defines ownership only. Usage belongs in `README.md`; migration belongs in `upgrading-to-3.md`.

## Ownership Classes

| Class | Location | Lifecycle |
|---|---|---|
| Repository-only | Repo-seed root and `docs/project/` | Maintained only for repo-seed |
| Package-only | `pack/README.md` and `pack/LICENSE` | Included in releases; never synced |
| Managed | Listed path under `pack/files/` | Updated when pack content differs |
| Managed template | `pack/files/docs/templates/` | Updated as a read-only reference when content differs |
| Managed state | `.repo-seed-state.json` in a target | Records active managed hashes and unresolved tombstones |
| Project-owned scaffold | Template destination | Created when missing; verified unchanged Markdown scaffolds may be upgraded |
| Unmapped | Any unlisted target path | Never touched |

## Managed Target Paths

- `AGENTS.md` and `CLAUDE.md`
- `.agents/guidelines/` and selected `.agents/conventions/`
- `docs/templates/`
- `scripts/sync-docs.py`
- `.repo-seed-state.json` generated in each target repository

## Project-Owned Target Paths

- `.agents/project.md` and child `AGENTS.md` files
- root `README.md`, `CHANGELOG.md`, `.gitignore`, and `.editorconfig`
- `docs/project/`
- scaffolded GitHub issue files

`pack/manifest.json` is the sole distributed inventory. Template files remain read-only references; agents update the corresponding project-owned document instead.

`.editorconfig`, `.gitignore`, and non-Markdown GitHub configuration are
missing-only scaffolds. Markdown scaffolds are upgraded only when their
repo-seed provenance or an approved legacy content hash proves they are
unchanged; otherwise they are preserved and reported.

The managed state file should be committed. It allows later syncs to distinguish
pack-owned files from unknown project files and to retry safe removal of stale
managed files after profile or inventory changes.
