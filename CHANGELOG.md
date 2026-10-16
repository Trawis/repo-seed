# Changelog

**Document role**: `repo-seed` repository documentation

**Sync behavior**: Never copied into target repositories

All meaningful user-facing and developer-facing changes should be documented in
this file.

Use newest entries first. Do not dump raw git commits here.

## 5.13.0 - 2026-10-16

Removed the `type: decision` label from the issue convention, the label
catalog, and the `issue-authoring` skill. An unresolved choice that blocks
implementation is now recorded in a `type: idea` issue, and the Decision issue
structure is gone. `sync-github-labels.py` and `issues.md` list `type: decision`
as a legacy label that maps to `type: idea`. Tightened the `type: tech-debt`
and `type: chore` definitions: tech-debt changes the structure of the project's
own source, chore covers the tooling, configuration, and documentation around
it. Added a tie-breaker rule, and aligned the label catalog descriptions with
`issues.md`.

## 5.12.4 - 2026-10-16

Added merge rules, release and hotfix flow, and commit message format to
`git.md`. Feature branches are squashed. Release and hotfix branches and
merge-backs to `develop` use merge commits, never squash. Releases are tagged on
`main`. Merged short-lived branches are deleted.

## 5.12.3 - 2026-10-16

Changed `AGENTS.md`, the Git, CI/CD, documentation, and issue guidelines, and
the convention files to shorter sentences, without changing any rule. Shortened
comments, docstrings, and help text in the Python scripts, with no behavior
change.

## 5.12.2 - 2026-10-16

Added a short pull request template, scaffolded to
`.github/pull_request_template.md` with `--scaffold-github-templates`. It is
created only when missing, so existing templates are kept. Changed changelog
guidance and the changelog template to short prose entries ordered added,
changed, fixed, removed.

## 5.12.1 - 2026-10-16

Fixed `--audit` not reporting legacy `bug`/`enhancement` labels in Issue Forms.
It now checks every `.md`, `.yml`, and `.yaml` file in `.github/ISSUE_TEMPLATE/`
(#100).

## 5.12.0 - 2026-10-15

Added the `repository-upgrade` skill. It upgrades a repo-seed install with the
newer pack's own `sync-docs.py`, starting with a dry run and ending with an
audit. It stops and asks when an older state needs an explicit selection.

## 5.11.0 - 2026-10-15

Added the `repository-bootstrap` skill. It applies repo-seed to a repository
with `sync-docs.py`, after a dry run, and checks the result. It warns that an
existing `AGENTS.md` and `CLAUDE.md` are replaced, and moves project content to
`.agents/project.md` first, with the user's agreement.

## 5.10.0 - 2026-10-15

Added the read-only `repository-audit` skill. It reports drift, stale files, and
competing agent guidance using the repository's own `sync-docs.py --audit`.

## 5.9.0 - 2026-10-15

Added the read-only `architecture-review` skill for `library`, `app`, and `game`
profiles. It reports a small ranked set of evidence-backed architecture
problems. Adapted from Matt Pocock's `improve-codebase-architecture` (MIT).

## 5.8.0 - 2026-10-15

Added the `code-simplification` skill. It simplifies code without changing
behavior and hands behavior changes to `refactor`. Adapted from Addy Osmani's
`code-simplification` (MIT). Turned off the `issue-authoring`,
`issue-implementation`, and `test-driven-development` wrappers in repo-seed's
own `.claude/settings.json`.

## 5.7.0 - 2026-10-15

Added the `test-driven-development` skill. It applies only when TDD is
requested. Adapted from Matt Pocock's `tdd` (MIT), with ideas from Superpowers'
`test-driven-development`.

## 5.6.0 - 2026-10-15

Added an acceptance review to `code-review`. When an issue or acceptance
criteria exist, each `Done when` condition is marked satisfied, unsatisfied, or
not verifiable. It also checks bug fixes for regression tests.

## 5.5.0 - 2026-10-15

Added the `issue-implementation` skill. It checks the issue against the current
repository and tracker before editing, and checks every acceptance condition
afterwards.

## 5.4.0 - 2026-10-15

Added the `issue-authoring` skill. It drafts issues from repository evidence,
checks for duplicates, and creates hosted issues only with permission.

## 5.3.0 - 2026-10-15

Changed `bug-fix` to start from a reliable reproduction and test one hypothesis
at a time. Changed `code-review` to validate the comparison base, cite
repository rules, and report standards findings separately. Audit decisions are
in `docs/project/skill-audit.md`.

## 5.2.0 - 2026-10-15

Added provenance tracking for skills derived from upstream repositories:
`pack/skill-sources.json` (shipped in the archive, never synced), a per-skill
`NOTICE.md`, and `scripts/validate-skill-sources.py`. The registry is empty for
now. Syncing stays offline. Maintainer steps are in
`docs/project/upstream-skills.md`.

## 5.1.0 - 2026-10-15

Added GitHub Issue Forms (`bug_report.yml`, `feature_request.yml`) in place of
the Markdown issue templates. They are scaffolded when missing. Existing `.md`
templates are not removed, so delete them after adopting the forms or GitHub
lists both.

## 5.0.0 - 2026-09-23

Breaking release. Added `--conventions` selection (`csharp`, `python`,
`scripts`, `shell`, `unity`), independent of profile; a fresh sync installs
none. Added `--audit`, a read-only drift report. Added `--scaffold <name>` for
`architecture`, `fsd`, `gdd`, and `user-guide`; `--scaffold-project-files` now
creates only README and CHANGELOG. Added the label catalog
`pack/github-labels.json` with `scripts/sync-github-labels.py` (`--check`,
`--apply`, needs the GitHub CLI), and issue guidance in
`.agents/guidelines/issues.md`. Changed the manifest to `schema_version: 3`,
which older and newer scripts cannot read from each other. Changed `CLAUDE.md` to
a plain `@AGENTS.md` import, issue labels to `type: bug` and `type: feature`,
and skills to the `minimal`, `library`, `app`, and `game` profiles. A state file
from before explicit conventions (schema 1) fails without `--conventions <list>`
and converts to schema 2 with it; see `docs/project/upgrading-to-5.md`. Removed
the `full` profile, pre-4.x migration (a target with no state file is a fresh
install), convention auto-detection, legacy scaffold markers (older unmarked
scaffolds are now project-owned), and `previous_hashes`.

## 4.2.0 - 2026-08-26

Added Codex and Claude Code skills for code review, bug fixing, refactoring,
dependency upgrades, technical design, and documentation bootstrap. `minimal`
gets the core skills, and other profiles also get technical design and
documentation bootstrap.

## 4.1.0 - 2026-08-26

Changed agent guidance so agents read only the documentation relevant to the
task, and check branch models only for Git and pull request work.

## 4.0.5 - 2026-07-08

Clarified branch-model discovery before branch and pull request work. Added
code convention checks before completion.

## 4.0.4 - 2026-07-07

Added guidance against decision-diary wording in documentation. Changed
templates to describe current state only.

## 4.0.3 - 2026-07-07

Changed metadata fields in the FSD, GDD, architecture, technical design, and
user-guide templates to lists.

## 4.0.2 - 2026-07-07

Fixed templates for non-ASCII punctuation, long lines, visible scaffold
instructions, and placeholder `Unreleased` headings.

## 4.0.1 - 2026-07-06

Fixed unknown pack paths in `.repo-seed-state.json` being accepted, and
protected the whole `.github/workflows/` tree from management. Corrected the
version 3 to 4 update command to run the new pack's script.

## 4.0.0 - 2026-07-06

Added existing-project bootstrap guidance for agents. Changed architecture to
the current system overview and TSD to a reference template for substantial
changes. Required an explicit profile on first sync, reused on later syncs, and
moved the manifest to schema version 2. `full` became a reference-only profile
that rejects project scaffolding. Removed the features template from normal
profiles and the generic `docs/project/tsd.md` scaffold.

## 3.4.1 - 2026-07-06

Changed existing `.gitignore` files to be reported as project-owned.

## 3.4.0 - 2026-07-06

Added a non-functional requirements section to the FSD template, a date column
to the architecture decision log, and a release note to the changelog template.
Removed the `.gitignore` scaffold; it is fully project-owned. Targets synced
with 3.3.0 or later drop the retired `docs/templates/gitignore.template`
automatically. Older ones can delete it by hand.

## 3.3.0 - 2026-07-06

Added `.repo-seed-state.json` to track managed files and tombstones, and
provenance hashes for Markdown scaffolds. Legacy files with local changes are
kept and reported. Profile reductions remove only unchanged stale files.
Protected `.editorconfig` and the pull request template as project-owned.
Unchanged managed files are no longer rewritten.

## 3.2.3 - 2026-07-05

Changed the version 3 migration guide to cover 1.x and 2.x installs.

## 3.2.2 - 2026-07-05

Clarified that Git Flow repositories keep merge commits across long-lived
branches.

## 3.2.1 - 2026-07-05

Added package instructions and the MIT license to the release archive, without
syncing them into targets.

## 3.2.0 - 2026-07-05

Changed guidance and conventions to be shorter, and templates to have one
purpose each. Fixed template review guidance to match stateless sync.

## 3.1.0 - 2026-07-05

Added contribution, security, license, install, and 2.x migration docs, a pull
request CI job, release checksums, and `--scaffold-editorconfig`. Added a
pre-copy check that fails on directory or symlink paths, and hardening against
unsafe source links and path collisions. Changed `library` to include general
coding conventions, Git guidance to be branching-model neutral, and the release
builder name to `scripts/build-release-bundle.py`. Removed the redundant
features document.

## 3.0.0 - 2026-07-04

Added a generic GitHub issue config template and made `.editorconfig` an
optional missing-only scaffold. Replaced stateful sync with plain managed-file
copying and missing-only scaffolding, moved all assets under `pack/`, renamed
the sync tool to `scripts/sync-docs.py`, and shipped one universal archive.
Removed managed-file hashes, target state, conflict copies, drift tracking,
migration cleanup, and Git branch operations.

## 2.0.1 - 2026-07-04

Changed the gitignore scaffold to cover only pack artifacts, and moved deferred
ideas into `docs/project/features.md`. Fixed Python and release ignore rules
leaking into target repositories.

## 2.0.0 - 2026-07-04

Added `pack-manifest.json` as the single inventory. Added focused guidance for
documentation, Git, and CI/CD, explicit project-file and issue-template
scaffolding, and a release builder with sync tests. Changed `AGENTS.md` to short
core rules with task routing, moved guidance and conventions under `.agents/`,
templates to `docs/templates/`, and project docs to `docs/project/`. Branch
selection now prefers `develop`/`dev`, then `main`/`master`. Fixed templates
masquerading as live docs, the pull request template assuming Git Flow, and
unsafe paths or bad manifests not failing clearly. Removed the roadmap (future
work is in `docs/project/features.md`), forced project doc overwrite, and
`.agents/base.md`. Deprecated `--include-project-docs` for
`--scaffold-project-files`.

## 1.31.0 - 2026-07-02

Added README, changelog, and features starter templates for target repos. Fixed
repo-seed's own root docs being used as sync sources.

## 1.30.0 - 2026-06-25

Added a release workflow that builds one ZIP per profile. Added bug report and
feature request issue templates, and Unity conventions for the `game` and `full`
profiles.

## 1.29.0 - 2026-06-23

Added a `--profile` flag with `minimal`, `library`, `app`, `game`, and `full`
(the default). Changed the default base branch from `develop` to `main`.

## 1.28.0 - 2026-06-23

Changed Git guidance to present Git Flow and GitHub Flow with a decision table.
This repository uses GitHub Flow.

## 1.27.0 - 2026-06-23

Changed this repository to GitHub Flow: `main` is the only long-lived branch and
all branches target it.

## 1.26.0 - 2026-06-23

Added architecture and user-guide templates, with guidance on when to create and
update them.

## 1.25.0 - 2026-06-19

Added CI/CD guidance. CI/CD changes now need explicit task scope.

## 1.24.0 - 2026-06-19

Added guidance on useful comments and concise task and PR summaries.

## 1.23.0 - 2026-06-19

Added pre-flight checks before creating branches or pull requests, to avoid
duplicate work, and generic-example guidance for templates. The sync script now
fetches and prunes remotes during branch preparation unless skipped.

## 1.22.0 - 2026-06-19

Renamed the sync script to the stable path `scripts/sync-agent-guidelines.py`.

## 1.21.0 - 2026-06-19

Added `scripts/sync-agent-guidelines.py` with version and hash tracking and
conflict copies, plus separate Python and shell conventions. Changed branching
to strict Git Flow families `feature/*`, `release/*`, and `hotfix/*`, with
`develop` as the default integration and PR target.

## 1.20.0

Skipped. This version was not released.

## 1.19.0 - 2026-06-19

Added a branch type table, branch naming policy, and pull request policy with
fallback reporting.

## 1.18.0 - 2026-06-18

Changed the C# rule to allow single-statement guard clauses without braces.
Replaced project-specific examples with generic ones.

## 1.17.0 - 2026-06-18

Added a C# rule for a blank line after a completed control block.

## 1.16.0 - 2026-06-18

Added a rule to keep the existing style of user-facing text, such as ASCII
versus Unicode punctuation.

## 1.15.0 - 2026-06-18

Added a C# rule against inline guards such as `if (...) return ...;`.

## 1.14.0 - 2026-06-15

Added `MUST`/`SHOULD`/`MAY` strictness levels, a rule against AI tool names in
repository text, and indentation preservation guidance. Softened Git Flow and PR
wording for solo repositories.

## 1.13.0 - 2026-06-12

Added the `CLAUDE.md` wrapper for Claude Code. Softened PR wording for local
repositories.

## 1.12.0 - 2026-06-12

Baseline starter pack with `AGENTS.md`, README, changelog, features file,
`.editorconfig`, a pull request template, conventions, and FSD, TSD, and GDD
templates.
