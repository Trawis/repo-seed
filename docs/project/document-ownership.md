# Document Ownership

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

This document defines ownership only. Usage belongs in `README.md`; upgrading
belongs in `upgrading-to-5.md`.

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

## Profiles, Conventions, and Scaffolds

These are three independent concepts and should not be conflated:

- **Profile** (`minimal`, `library`, `app`, `game`) selects project-shape
  assets: which core guidance and which reference document templates a
  target may draw from. It says nothing about programming language. There is
  no "install everything" profile; the release archive already contains the
  complete pack, and the manifest/catalog can be tested directly.
- **Conventions** (`csharp`, `python`, `scripts`, `shell`, `unity`) select
  which `.agents/conventions/*.md` language/tool guidance files are actually
  installed, chosen explicitly with `--conventions` and persisted in
  `.repo-seed-state.json`. A convention file is available under every
  profile; nothing selects one automatically. A fresh install has none until
  `--conventions` is passed. The one exception is converting a pre-5.0
  (`schema_version: 1`) state, which requires `--conventions` once, explicitly
  chosen by whoever runs the sync, never inferred from the filesystem; see
  `upgrading-to-5.md`.
- **Scaffolds** are optional project documents created from a template only
  on request. `README.md` and `CHANGELOG.md` remain the baseline, created by
  `--scaffold-project-files`. `architecture.md`, `fsd.md`, `gdd.md`, and
  `user-guide.md` are on-demand: their templates are available for the
  applicable profile, but creating them requires
  `--scaffold <name>` (for example `--scaffold architecture`). Being
  available for a profile never implies a document must exist.

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
creation, labels, and lightweight issue structure, and is the only part of
this catalog distributed to target repositories. `pack/github-labels.json`
and `scripts/sync-github-labels.py` are repo-seed-side maintainer tooling,
never synced into a target: the machine-readable catalog backing the
distributed convention, and the optional, explicitly invoked reconciler for
it (see [README](../../README.md)). Repository files can only represent the
intended label catalog; they cannot prove which labels are actually
configured in the GitHub repository. Hosted-label reconciliation is
separate from normal file synchronization and from the local `--audit`
diagnostics, neither of which needs GitHub network access.

Some templates, such as the TSD, are reference-only and have no automatic
scaffold target. Agents copy them to the suggested project-owned path only when
the document is needed.

`.editorconfig` and non-Markdown GitHub configuration are missing-only
scaffolds. `.gitignore` is fully project-owned and is not scaffolded; manage it
with the tooling of the project's stack. A Markdown scaffold is upgraded only
when its current repo-seed provenance markers prove it is unchanged; a
scaffold with no provenance, or with provenance that does not match, is
treated as project-owned and preserved without further identification.

The managed state file should be committed. It allows later syncs to distinguish
pack-owned files from unknown project files and to retry safe removal of stale
managed files after profile or inventory changes.

Untouched scaffolds and documents containing only placeholders are not approved
requirements merely because they are located under `docs/project/`.
