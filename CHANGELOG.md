# Changelog

**Document role**: `repo-seed` repository documentation

**Sync behavior**: Never copied into target repositories

All meaningful user-facing and developer-facing changes should be documented in this file.

Use newest entries first. Do not dump raw git commits here.

## 2.0.1 - 2026-07-04

### Changed

- Reduced the generic gitignore scaffold to pack-owned conflict artifacts only.
- Removed the deprecated project-doc alias from normal CLI and README documentation while retaining compatibility.
- Consolidated deferred ideas in `docs/project/features.md` to keep 2.0 stabilization feature-frozen.

### Fixed

- Prevented Python and release-output ignore rules from leaking into unrelated target repositories.

## 2.0.0 - 2026-07-04

### Added
- Added `pack-manifest.json` as the shared inventory for sync, profiles, scaffolding, migration, and release bundles.
- Added focused managed guidance for documentation, Git, and CI/CD work.
- Added content-hash provenance and non-failing review warnings for scaffolded project documents.
- Added explicit project-file and GitHub issue-template scaffolding.
- Added a manifest-driven release-bundle builder and sync regression suite.

### Changed
- Replaced the oversized distributed `AGENTS.md` with concise, self-contained core rules and task-specific routing.
- Moved managed supporting guidance and conventions under target `.agents/`.
- Moved all reference templates under `docs/templates/`; live non-root project documentation now belongs under `docs/project/`.
- Made template and scaffold selection profile-specific.
- Kept managed template filenames and relative structure unchanged during sync, including GitHub references under `docs/templates/.github/`.
- Added a managed gitignore reference template that scaffolds target `.gitignore` only when missing.
- Clarified that distributed AGENTS/CLAUDE files are always synced from `pack/`, while source root documents are repo-seed-only.
- Changed automatic branch selection to prefer existing `develop`/`dev` branches and fall back to `main`/`master`.
- Made obsolete managed-file cleanup hash-safe for migrations and profile reductions.
- Changed release packaging and version discovery to consume the manifest.
- Bumped the pack and sync script to 2.0.0 for the breaking layout and CLI changes.

### Fixed
- Repo-seed root documents can no longer be confused with target sync sources.
- Managed templates no longer overwrite or masquerade as live project documentation.
- Missing sources, unsafe paths, malformed manifests, invalid templates, and managed conflicts now fail clearly.
- The distributed pull-request template no longer assumes Git Flow.

### Removed
- Removed the redundant roadmap; future work now lives in `docs/project/features.md`.
- Removed project-document force overwrite behavior and the temporary `.agents/base.md` design.

### Deprecated
- Deprecated `--include-project-docs` in favor of `--scaffold-project-files`.

### Security
-

## 1.31.0 - 2026-07-02

### Added
- Added `docs/readme-template.md`, `docs/changelog-template.md`, and `docs/features-template.md`: generic starter content for target repos, copied by `--include-project-docs` in `scripts/sync-agent-guidelines.py`.

### Changed
- `PROJECT_DOC_TEMPLATES` in `scripts/sync-agent-guidelines.py` now maps each `docs/*-template.md` source to its target root filename (`README.md`, `CHANGELOG.md`, `FEATURES.md`) instead of copying this repo's own root docs. `repo-seed`'s root `README.md`, `CHANGELOG.md`, and `FEATURES.md` describe this pack itself and are no longer used as sync sources.
- Bumped sync script to v1.7.0, pack reference to v1.31.0.

## 1.30.0 - 2026-06-25

### Added
- Added `.github/workflows/release.yml`: triggers on every push to `main`, reads version from `.agent-guidelines-version`, skips if the release already exists, builds one ZIP per profile (`minimal`, `library`, `app`, `game`, `full`), and creates a tagged GitHub Release with all ZIPs attached.
- Added GitHub issue templates: bug report (`.github/ISSUE_TEMPLATE/bug_report.md`) and feature request (`.github/ISSUE_TEMPLATE/feature_request.md`).
- Added `docs/coding-conventions-unity.md` covering MonoBehaviour conventions, lifecycle order, serialized fields, component caching, coroutines, physics, tags/layers, events, ScriptableObjects, editor scripts, asset naming, and performance guidance.
- Unity conventions are included in the `game` and `full` sync profiles.

### Changed
- Bumped sync script pack reference to v1.30.0.

## 1.29.0 - 2026-06-23

### Added
- Added `--profile` flag to `scripts/sync-agent-guidelines.py` with five options: `minimal`, `library`, `app`, `game`, and `full` (default). Allows syncing only the files relevant to the target project type.
- Added profile selection table to the sync section in `AGENTS.md`.

### Changed
- Default `--base-branch` changed from `develop` to `main` to match GitHub Flow.
- "Next steps" message now references the actual base branch instead of hardcoded `develop`.
- Bumped sync script to v1.6.0, pack reference to v1.29.0.

## 1.28.0 - 2026-06-23

### Changed
- Restructured Git Workflow section to present Git Flow and GitHub Flow as explicit, documented options with a decision table.
- Git Flow: `main`/`master` + `develop`/`dev`, with `feature/*`, `release/*`, and `hotfix/*` branch families. Recommended for applications with formal release cycles.
- GitHub Flow: `main`/`master` only, all work via `feature/*` branches. Recommended for docs, seed/template repos, libraries, and solo projects.
- This repository uses GitHub Flow.
- Unified PR target table showing both models.

## 1.27.0 - 2026-06-23

### Changed
- Overridden Git Flow for this repository: `main` is the only long-lived branch; no `develop` branch exists or should be created.
- All branch families (`feature/*`, `release/*`, `hotfix/*`) now base from `main` and target `main`.
- Updated preflight merge check to use `origin/main` instead of `origin/develop`.
- Removed back-merge requirements to `develop` from `release/*` and `hotfix/*` PR targets.

## 1.26.0 - 2026-06-23

### Added
- Added `docs/architecture-template.md` for documenting system context, components, tech stack, data flow, design decisions, deployment, integrations, security, and constraints.
- Added `docs/user-guide-template.md` for GUI and client-facing apps, covering navigation, key workflows, settings, troubleshooting, FAQ, and glossary.
- Added architecture and user guide guidance in `AGENTS.md`, including when to create and update each document.
- Added architecture and user guide update checks to the agent completion checklist.

### Fixed
- Noted missing version 1.20 (skipped, not released) in version history.

## 1.25.0 - 2026-06-19

### Added
- Added CI/CD and workflow automation guidance.
- Added `docs/ci-cd-guidelines.md` for safe CI/CD changes, validation, and staged adoption.
- Added CI/CD completion checklist guidance.

### Changed
- Clarified that CI/CD workflow, deployment, secret, permission, and release automation changes require explicit task scope.
- Updated README links and sync metadata for pack version `1.25.0`.

## 1.24.0 - 2026-06-19

### Added
- Added comment discipline guidance for code, scripts, public API documentation, and generated documentation.
- Added summary discipline guidance for task summaries, PR summaries, and agent completion notes.
- Added examples showing useful comments versus obvious/noisy comments.

### Changed
- Updated completion and PR checklists to include concise comments/summaries.
- Bumped sync script metadata to pack version `1.24.0`.

## 1.23.0 - 2026-06-19

### Added
- Added mandatory Git/PR preflight guidance before agents create branches, start duplicate work, or open pull requests.
- Added duplicate-work protection for changes already merged into `develop` or already covered by an existing open PR.
- Added generic-example guidance so shared templates avoid project-specific enum/domain names.

### Changed
- Updated sync script metadata to pack version `1.23.0` and added remote fetch/prune during branch preparation unless skipped.
- Updated C# examples to use the generic `OrderStatusEnum` example instead of project-specific terminal enums.

## 1.22.0 - 2026-06-19

### Changed
- Renamed the repo-seed sync script from a versioned filename to the stable path `scripts/sync-agent-guidelines.py` so Git history tracks script changes cleanly.
- Clarified script filename/versioning guidance: scripts committed to a repository should use stable filenames, while distributed standalone copies, generated output files, and archive artifacts may use semantic-version suffixes.
- Updated sync examples, README links, and managed-file manifest paths to use the stable sync script name.

## 1.21.0 - 2026-06-19

### Added
- Added `scripts/sync-agent-guidelines.py` for syncing this pack from `repo-seed` into other repositories.
- Added `.agent-guidelines-version` to track the synced pack version in target repositories.
- Added repo-seed sync workflow guidance.
- Added managed-file hash tracking through `.agent-guidelines-manifest.json`.
- Added conservative conflict behavior that writes incoming versions under `.agent-guidelines-conflicts/`.
- Added separated Python and shell script convention files.

### Changed
- Replaced mixed branch type policy with strict Git Flow branch families: `feature/*`, `release/*`, and `hotfix/*`.
- Set `develop` as the default integration branch, normal PR target, and recommended hosted default branch for Git Flow repositories.
- Clarified that normal documentation, tests, refactors, chores, and non-emergency bug fixes use `feature/*` branches under strict Git Flow.
- Renamed the central guideline source example from `project-seed` to `repo-seed`.

## 1.20.0

> Skipped — this version number was not released.

## 1.19.0 - 2026-06-19

### Added
- Added unified branch type table and branch naming policy.
- Added explicit PR creation/proposal policy so agents do not randomly skip pull requests.
- Added fallback PR reporting requirements when PR creation is unavailable.

### Changed
- Clarified when to use `feature`, `bugfix`, `docs`, `test`, `refactor`, `chore`, `release`, and `hotfix` branches.
- Updated PR checklist to verify branch type, branch naming, and PR target.

## 1.18.0 - 2026-06-18

### Changed
- Clarified C# control-flow convention: single-statement guard clauses may omit braces when the controlled statement is on the next line.
- Updated `.editorconfig` to prefer braces only for multiline control blocks.
- Replaced project-specific terminal/output examples with generic examples.

## 1.17.0 - 2026-06-18

### Added
- Added C# spacing convention requiring a blank line after a completed control block before the next independent statement.
- Added examples for spacing between an `if` block and a following `return` statement.

### Changed
- Updated C# quick reference and agent checklist to include completed-control-block spacing.

## 1.16.0 - 2026-06-18

### Added
- Added rule to preserve existing user-facing text/output style, including ASCII vs Unicode punctuation and decorative separators.
- Added C# and script convention examples for plain ASCII separators versus Unicode/box-drawing separators.

### Changed
- Updated agent checklist and convention docs to check terminal/UI/output string consistency.

## 1.15.0 - 2026-06-18

### Added
- Added explicit C# control-flow convention forbidding inline guard statements such as `if (...) return ...;`.
- Added examples showing `return` and `throw` on their own line instead of inline after the condition.

### Changed
- Updated C# quick reference to mention no inline control-flow statements.

## 1.14.0 - 2026-06-15

### Added
- Added `MUST` / `SHOULD` / `MAY` instruction strictness levels.
- Added rule to avoid AI assistant, tool, provider, or model names in branch names, commits, PR text, changelog entries, release notes, and generated helper text.
- Added indentation preservation guidance: use spaces when the existing file/repository uses spaces and tabs when it uses tabs.

### Changed
- Softened Git Flow and PR wording for solo/local repositories while keeping branch isolation and no auto-merge.
- Updated C# and script convention docs to preserve existing indentation style before applying defaults.

## 1.13.0 - 2026-06-12

### Added
- Added `CLAUDE.md` compatibility wrapper for Claude Code.

### Changed
- Updated `AGENTS.md` to version 1.13.
- Collapsed early version-history churn into a clean `1.12.0` baseline entry.
- Softened PR workflow wording for solo/local repositories where hosted PRs are unavailable.

## 1.12.0 - 2026-06-12

### Added
- Baseline public starter pack.
- Included `AGENTS.md`, `README.md`, `CHANGELOG.md`, `FEATURES.md`, `.editorconfig`, `.github/pull_request_template.md`, coding convention docs, and FSD/TSD/GDD templates.
