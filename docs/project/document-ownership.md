# Document Ownership

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

This document defines ownership only. Usage belongs in `README.md`; migration
belongs in `upgrading-to-3.md` and `upgrading-to-4.md`.

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
- scaffolded GitHub issue files and `.github/pull_request_template.md`

`pack/manifest.json` is the sole distributed inventory. Template files remain read-only references; agents update the corresponding project-owned document instead.

## Claude Code Wrapper

`AGENTS.md` is the canonical, cross-agent instruction file. `CLAUDE.md`
stays a minimal Claude Code compatibility wrapper (`@AGENTS.md`, a real
Claude Code import) rather than a second policy source, because current
Claude Code loads a project's `CLAUDE.md` instead of separately loading
`AGENTS.md` when both are present. Modern Claude Code can also load
`AGENTS.md` natively, but the wrapper is kept for configurations where
`CLAUDE.md` takes precedence or native `AGENTS.md` support is unavailable.
Do not add other `@` imports to `CLAUDE.md`; that would expand specialized
guidance into every session's context and defeat the demand-driven model in
`AGENTS.md`. To verify the import is loaded, run `/context` in Claude Code
and confirm `CLAUDE.md` appears under Memory files.

## `.agents/project.md` Content

`.agents/project.md` holds only information specific to the target
repository: project purpose, architecture notes, supported runtimes or
versions, important paths, build and test commands, validation
expectations, branch or release workflow, documentation rules, compatibility
requirements, and unusual project constraints. Do not copy generic repo-seed
instructions into it; that guidance already lives in the managed files
above.

## Canonical Issue and Label Catalog

`.agents/guidelines/issues.md` is the single canonical source for issue
creation, labels, and lightweight issue structure. Scaffolded issue
templates and other guidance agree with it instead of defining a competing
list. `pack/github-labels.json` is the machine-readable label catalog it
describes. Repository files can only represent the intended label catalog;
they cannot prove which labels are actually configured in the GitHub
repository. Reconcile hosted labels explicitly with
`scripts/sync-github-labels.py` (see [README](../../README.md)); this is
separate from normal file synchronization and from the local `--audit`
diagnostics, neither of which needs GitHub network access.

Some templates, such as the TSD, are reference-only and have no automatic
scaffold target. Agents copy them to the suggested project-owned path only when
the document is needed.

`.editorconfig` and non-Markdown GitHub configuration are missing-only
scaffolds. `.gitignore` is fully project-owned and is not scaffolded; manage it
with the tooling of the project's stack. Markdown scaffolds are upgraded only
when their repo-seed provenance or an approved legacy content hash proves they
are unchanged; otherwise they are preserved and reported.

The managed state file should be committed. It allows later syncs to distinguish
pack-owned files from unknown project files and to retry safe removal of stale
managed files after profile or inventory changes.

Untouched scaffolds and documents containing only placeholders are not approved
requirements merely because they are located under `docs/project/`.
