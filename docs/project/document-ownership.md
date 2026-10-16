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

## Upstream-Derived Skills

`pack/skill-sources.json` and `scripts/validate-skill-sources.py` are
repo-seed-side tooling and never synced. Derived skills ship through
`pack/manifest.json` like other managed skills, with a `NOTICE.md`. See
[Upstream-derived skills](upstream-skills.md).

## Profiles, Conventions, and Scaffolds

Three independent concepts:

- **Profile** (`minimal`, `library`, `app`, `game`) selects project-shape
  assets: which reference templates a target may use. It says nothing about
  language. There is no "install everything" profile.
- **Conventions** (`csharp`, `python`, `scripts`, `shell`, `unity`) select
  which `.agents/conventions/*.md` files are installed. They are chosen with
  `--conventions` and saved in `.repo-seed-state.json`. Nothing selects one
  automatically, and a fresh install has none. Converting a pre-5.0 state
  needs `--conventions` once; see `upgrading-to-5.md`.
- **Scaffolds** are optional project documents created from a template on
  request. `--scaffold-project-files` creates the baseline `README.md` and
  `CHANGELOG.md`. `architecture`, `fsd`, `gdd`, and `user-guide` need
  `--scaffold <name>`. Availability for a profile never means a document must
  exist.

## Claude Code Wrapper

`AGENTS.md` is the canonical instruction file. `CLAUDE.md` is only a wrapper
(`@AGENTS.md`), because Claude Code loads `CLAUDE.md` in place of `AGENTS.md`
when both exist. Do not add other `@` imports to it. They would load
specialized guidance into every session. To verify, run `/context` in Claude
Code and check that `CLAUDE.md` is listed under Memory files.

## `.agents/project.md` Content

`.agents/project.md` holds only facts specific to the target repository:
purpose, architecture notes, supported runtimes, important paths, build and test
commands, validation expectations, branch or release workflow, documentation
rules, compatibility requirements, and unusual constraints. Do not copy generic
repo-seed instructions into it.

## Canonical Issue and Label Catalog

`.agents/guidelines/issues.md` is the only source for issue creation, labels,
and issue structure, and the only part of this catalog sent to targets.
`pack/github-labels.json` and `scripts/sync-github-labels.py` are
maintainer-side: the label catalog and its optional reconciler (see
[README](../../README.md)). Repository files cannot prove which labels exist in
GitHub. Label reconciliation is separate from file sync and from `--audit`,
neither of which needs network access.

Some templates, such as the TSD, are reference-only with no scaffold target.
Agents copy them to a project-owned path only when needed.

`.editorconfig` and non-Markdown GitHub configuration are missing-only
scaffolds. `.gitignore` is fully project-owned and not scaffolded. A Markdown
scaffold is upgraded only when its provenance markers prove it is unchanged.
One with no or mismatched provenance is treated as project-owned and kept.

Commit the managed state file. It lets later syncs tell pack-owned files from
project files and retry safe removal of stale managed files.

Untouched scaffolds and placeholder-only documents under `docs/project/` are not
approved requirements.
