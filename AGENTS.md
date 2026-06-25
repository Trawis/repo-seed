# AGENTS.md

Repository-level instructions for AI coding agents.

**Version**: 1.30  
**Status**: Active  
**Last Updated**: 2026-06-25

**Recent changes**:
- Added GitHub issue templates (bug report, feature request) under `.github/ISSUE_TEMPLATE/`.
- Added `docs/coding-conventions-unity.md` for Unity/C# projects.
- Added Unity conventions to the `game` and `full` sync profiles.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.30 | 2026-06-25 | Added GitHub issue templates and `docs/coding-conventions-unity.md`; Unity conventions included in `game` and `full` sync profiles. |
| 1.29 | 2026-06-23 | Added profile-based sync (`--profile minimal|library|app|game|full`) to the sync script. |
| 1.28 | 2026-06-23 | Restructured Git Workflow: Git Flow and GitHub Flow as explicit options with a decision table; this repository uses GitHub Flow. |
| 1.27 | 2026-06-23 | Overridden Git Flow for this repository: no `develop` branch, all branches target `main`. |
| 1.26 | 2026-06-23 | Added architecture documentation template and user guide template for GUI/client-facing apps. |
| 1.25 | 2026-06-19 | Added CI/CD and workflow automation guidance, safety boundaries, and `docs/ci-cd-guidelines.md`. |
| 1.24 | 2026-06-19 | Added comment and summary discipline for code, scripts, PRs, and agent completion notes. |
| 1.23 | 2026-06-19 | Added Git/PR preflight checks, duplicate-work protection, and generic-example guidance. |
| 1.22 | 2026-06-19 | Renamed the repo-seed sync script to a stable filename and clarified script filename/versioning guidance. |
| 1.21 | 2026-06-19 | Enforced strict Git Flow branch families and added repo-seed sync workflow/script guidance. |
| 1.20 | — | Skipped — not released. |
| 1.19 | 2026-06-19 | Unified branch prefix selection, PR creation/proposal behavior, and fallback PR reporting. |
| 1.18 | 2026-06-18 | Clarified that single-statement C# guards may omit braces when the statement is on the next line; replaced project-specific terminal examples with generic examples. |
| 1.17 | 2026-06-18 | Added C# spacing rule requiring a blank line after a completed control block before the next independent statement. |
| 1.16 | 2026-06-18 | Added UI/output text style preservation rule for Unicode/ASCII punctuation and decorative separators. |
| 1.15 | 2026-06-18 | Added C# control-flow convention forbidding inline guard statements such as `if (...) return ...;`. |
| 1.14 | 2026-06-15 | Added instruction strictness levels, no-AI-name Git artifact rules, indentation preservation guidance, and clearer solo/local workflow handling. |
| 1.13 | 2026-06-12 | Added Claude Code compatibility through `CLAUDE.md`, cleaned version history, and softened PR workflow wording for solo/local repositories. |
| 1.12 | 2026-06-12 | Baseline public starter pack with `AGENTS.md`, `README.md`, `CHANGELOG.md`, `FEATURES.md`, `.editorconfig`, PR template, coding convention docs, and FSD/TSD/GDD templates. |

---

## Instruction Strictness

Use these levels when applying this file:

- `MUST`: mandatory safety, correctness, repository hygiene, or user-instruction rule. Do not ignore it unless the user explicitly overrides it in the current task or it is impossible in the environment.
- `SHOULD`: preferred default. Follow it when practical, but preserve existing repository conventions when they clearly differ.
- `MAY`: optional guidance for mature projects, larger repositories, or future improvements.

Defaults:

- Safety, secrets, destructive commands, branch protection, no auto-merge, and honesty about validation are `MUST`.
- Code style, formatting preferences, and documentation updates are usually `SHOULD` unless the repository makes them mandatory. Git Flow branch family and PR-target rules are `MUST` when this pack is used as the repository workflow source of truth.
- New child `AGENTS.md` files, new convention files, extra templates, and stricter automation are `MAY` unless requested.

When a rule is too strict for a solo/local repository, keep the intent: isolate the change, document the intended branch/PR, validate what is practical, and never pretend unavailable workflow steps were completed.

---

## Purpose

This file is the source of truth for AI coding agents working in this repository.

Use it as operational guidance, not as a general programming tutorial. Follow these instructions unless a more specific instruction exists in a closer `AGENTS.md` file or the user explicitly overrides them in the current task.

This root file is intentionally generic. Add project-specific details in this file or in nested `AGENTS.md` files as individual repositories mature.

---

## Claude Code Compatibility

`AGENTS.md` is the primary source of truth for this pack.

For Claude Code, use the included `CLAUDE.md` wrapper. It imports this file so the same rules can be shared without duplicating instructions.

Do not copy all rules into `CLAUDE.md`. Keep `CLAUDE.md` short and use it only for Claude-Code-specific notes or imports.

---

## Instruction Scope and Precedence

Use the most specific trusted instructions available for the files being changed.

Precedence order:

1. Current user instructions for the task.
2. The closest `AGENTS.md` in the target repository or subdirectory.
3. Parent `AGENTS.md` files, moving upward toward the repository root.
4. This local/generic `AGENTS.md` as fallback guidance when the repository has no own instructions.
5. General coding knowledge and existing local code style.

Rules:

- If an upstream or cloned repository already has its own `AGENTS.md`, use that repository's instructions for modifying its scripts, code, tests, docs, and workflows.
- Do not override upstream project rules with this generic file unless the upstream instructions are missing, incomplete, unsafe, or clearly unrelated to the touched files.
- In multi-purpose repositories, use parent/child `AGENTS.md` layering:
  - root `AGENTS.md` contains repo-wide rules
  - child `AGENTS.md` files contain subproject, language, framework, game/mod, script, or tooling-specific rules
  - the nearest child `AGENTS.md` applies to files under that directory
- Child `AGENTS.md` files should override or extend parent rules only where needed. Do not duplicate the whole parent file.
- When editing files in multiple subprojects, check the applicable instructions for each changed path.
- When moving files across instruction boundaries, check both the source and destination rules.
- If applicable `AGENTS.md` files conflict, follow the most specific file for the touched path and report meaningful conflicts.
- If no repo-specific instructions exist, use this file and preserve the existing local style of the repository.
- Do not create or modify `AGENTS.md` files unless the task asks for agent-instruction updates or the change is clearly about repository guidance. If a missing child file would help, recommend it.

For playground, sandbox, monorepo, or multi-purpose repositories, prefer this structure over one oversized root file:

```text
AGENTS.md
src/project-a/AGENTS.md
src/project-b/AGENTS.md
scripts/AGENTS.md
games/example-game/AGENTS.md
```

---

## Minimal Context Rule

- Apply only the rules relevant to the files touched by the task.
- Do not rewrite existing code only to satisfy style preferences unless the task asks for cleanup.
- Do not make broad architecture, formatting, dependency, or naming changes as a side effect.
- Prefer the smallest safe change that solves the requested problem.
- When in doubt, preserve the existing local style of the file being edited.
- Preserve existing indentation style in touched files: use spaces if the file/repo uses spaces, and tabs if it uses tabs.
- Preserve existing user-facing text style in touched files, including ASCII vs Unicode punctuation, decorative separators, quote style, symbols, labels, and terminal/UI output formatting.
- Do not add obvious comments, noisy summaries, or broad explanatory text that does not help maintainers understand intent, risk, tradeoffs, or non-obvious behavior.

---

## Agent Operating Rules

- Understand the task and inspect the relevant files before editing.
- Check for applicable upstream, repository-level, parent, or child `AGENTS.md` files before modifying specific code paths.
- Check for applicable convention files under `docs/` before editing code, scripts, docs, games, or tooling.
- Run Git/PR preflight before creating a branch, starting duplicate work, or opening a PR when the repository has Git remotes or hosted PR tooling available.
- If an FSD, TSD, GDD, product brief, issue, ticket, or acceptance criteria are provided, read them before implementation and use them as requirements input.
- Prefer small, targeted changes over broad rewrites.
- Do not reformat unrelated files.
- Preserve existing indentation style in modified files. Do not convert spaces to tabs or tabs to spaces unless the task is explicitly formatting/style cleanup.
- Preserve existing punctuation and text formatting style in modified user-facing strings. Do not mix Unicode box/em-dash separators with plain ASCII dash separators unless the task explicitly asks for a style change.
- Do not rename public APIs, files, projects, branches, packages, or namespaces unless the task requires it.
- Do not add new production dependencies unless the task clearly requires them.
- Preserve existing architecture, project boundaries, and naming patterns.
- Add or update unit tests when feasible, especially for behavior changes, bug fixes, validation logic, and edge cases.
- If tests are not added, explain why they were not practical or useful for the change.
- Keep comments purposeful. Explain why something exists, non-obvious behavior, tradeoffs, edge cases, or external constraints; do not comment obvious code.
- Keep task summaries, PR summaries, and generated documentation concise. Do not pad with broad explanations, repeated points, or generic praise.
- Always try to build the project when a build command exists and the change affects buildable code.
- Always try to run relevant tests when test commands or test projects exist.
- Run smoke tests or quick manual checks when the project exposes a runnable app, CLI, script, game scene, or service entry point and doing so is practical in the environment.
- Recheck the implemented behavior against the task, FSD/TSD/GDD, acceptance criteria, and changed files before finishing.
- If checks cannot be run, state exactly why.
- If the implementation is uncertain, requirements are ambiguous, or validation cannot prove the behavior, ask or clearly report the uncertainty instead of pretending it is complete.
- Report what changed, what was validated, and any remaining risks.
- Do not include AI assistant, tool, or model names in branch names, commit messages, PR titles, PR descriptions, changelog entries, release notes, generated helper text, or user-facing documentation unless the task is explicitly about AI tooling or these agent-guideline files.
- Never hide failing tests, build errors, skipped checks, or uncertainty.

Ask before:

- broad refactors
- changing architecture
- replacing libraries/frameworks
- changing project structure
- renaming public APIs
- changing persistence models or database schema
- changing CI/CD, deployment, or infrastructure behavior
- adding or changing workflow jobs, deployment steps, repository secrets, or release automation
- applying a new pattern across the codebase

---

## Repository Setup and Validation Commands

Before finishing work, run the narrowest relevant checks available in the repository.

Validation priority:

1. Build the affected project when a build command exists.
2. Run relevant automated tests when they exist.
3. Run lint/format checks when configured.
4. Run a smoke test or quick manual check for runnable apps, CLIs, scripts, games, or services when practical.
5. Recheck changed behavior against the task and any provided FSD/TSD/GDD/acceptance criteria.

### .NET / C# Defaults

Prefer, when available:

```bash
dotnet format --verify-no-changes
dotnet build
dotnet test
```

If formatting changes are expected, run:

```bash
dotnet format
```

Then re-run build/tests if code was changed.

If the solution or project file is not obvious, inspect the repository and choose the narrowest relevant command.

### Other Stacks

If this repository uses other languages or frameworks, add the exact commands here or in a child `AGENTS.md`.

Suggested placeholders:

```bash
# JavaScript / TypeScript
npm install
npm run lint
npm run test
npm run build

# Python
python -m pytest
ruff check .
ruff format --check .

# Go
go test ./...
go fmt ./...

# Rust
cargo fmt --check
cargo test
cargo clippy -- -D warnings
```

Smoke-test examples when practical:

```bash
# CLI/script
python script-name_1.0.0.py --help
./script-name_1.0.0.sh --help

# Web/API/service
# Start the app using the documented command and verify the touched route/flow manually.
```

Do not add or run irrelevant commands for stacks that are not present in the repository.

---

## Syncing This Pack from `repo-seed`

For multiple repositories, keep the latest approved guideline pack in a central repository such as `repo-seed`, then sync a committed snapshot into each target repository.

Rules:

- The target repository must contain local committed copies of the applicable guideline files before agents begin work.
- Do not rely on agents dynamically fetching instructions at task runtime.
- Use `repo-seed` as the central source of truth for this generic pack unless a target repository has more specific local rules.
- Syncing must not auto-commit, auto-push, create a PR, or auto-merge.
- Syncing should be done on a normal task branch and reviewed through the repository PR workflow.
- Do not overwrite project-specific `README.md`, `CHANGELOG.md`, or `FEATURES.md` during routine sync unless explicitly requested.
- Do not overwrite child `AGENTS.md` files in subdirectories. Root `AGENTS.md` is the synced baseline; child files remain project/module-specific.
- Track the synced pack version in `.agent-guidelines-version`.

Recommended sync command from a target repository:

```bash
# Dry run first to preview changes
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target . --dry-run --profile <profile>

# Then sync with the appropriate profile
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target . --profile <profile>
```

Available profiles:

| Profile | Use for | Files included |
|---------|---------|---------------|
| `minimal` | Bare agent config only | AGENTS.md, CLAUDE.md, .editorconfig, PR template |
| `library` | Libraries, DLLs, packages | Minimal + coding conventions + CI/CD guidelines |
| `app` | Full applications | Library + FSD/TSD templates, architecture doc, user guide |
| `game` | Games and mods | Library + GDD template |
| `full` | Everything (default) | All files |

Recommended branch for syncing this pack into another repository:

```text
feature/sync-agent-guidelines-1-24-0
```

Recommended PR title:

```text
Sync agent guidelines 1.24.0
```


## Project Structure

Document project-specific structure here when known.

Recommended items:

- solution file location
- source project folders
- test project folders
- startup/API project
- CLI, worker, or desktop/mobile app entry point
- infrastructure/database project
- generated-code folders
- migration folders
- public API contract files
- files that should not be edited manually

Generic defaults:

- Prefer editing source files over generated output.
- Prefer narrow changes in the relevant project instead of cross-solution rewrites.
- If multiple projects are affected, explain why.

---

## Requirements and Specifications

If provided, use these documents as requirements input before editing code:

- FSD: Functional Specification Document
- TSD: Technical Specification Document
- GDD: Game Design Document
- product brief, issue, ticket, or acceptance criteria

Rules:

- Read the relevant FSD/TSD/GDD sections before implementation.
- Treat the FSD as the source of truth for user-facing behavior and acceptance criteria.
- Treat the TSD as the source of truth for architecture, technical constraints, integrations, data flow, and implementation details.
- Treat the GDD as the source of truth for gameplay intent, mechanics, progression, player experience, level/content rules, balancing goals, narrative constraints, and game-specific acceptance criteria.
- If the FSD, TSD, GDD, ticket, or acceptance criteria conflict, stop and report the conflict instead of guessing.
- Do not implement features outside the provided scope unless the user explicitly asks for them.
- Map meaningful code/content changes back to the relevant requirement, acceptance criterion, design rule, or technical constraint.
- If the implementation requires changing behavior described in the FSD/TSD/GDD, report it and update the document only if asked.
- If no FSD/TSD/GDD exists, infer requirements from the task and keep the change narrow.
- When no FSD/TSD/GDD exists and the task requires specification work, use the templates under `docs/` as the starting point:
  - `docs/fsd-template.md`
  - `docs/tsd-template.md`
  - `docs/gdd-template.md`
  - `docs/architecture-template.md`
  - `docs/user-guide-template.md`

---

## Repository Documentation

Keep project documentation aligned with behavior, setup, commands, public features, and versioned output.

Rules:

- If the repository contains `README.md`, `CHANGELOG.md`, `FEATURES.md`, `ROADMAP.md`, or `docs/`, update the relevant file when the task changes setup, commands, public behavior, user-facing features, versioned output, or documented limitations.
- If these files do not exist, recommend creating them when they would materially improve the repository.
- Do not create documentation files as busywork.
- Prefer updating existing documentation over creating duplicates.
- Keep documentation factual, current, and scoped to the change.

### README.md

`README.md` is the human entry point for the project.

Update it when changing:

- setup or install steps
- build, test, run, or smoke-test commands
- configuration
- CLI arguments or examples
- public behavior
- supported platforms
- screenshots, examples, or usage flows
- known limitations

### CHANGELOG.md

`CHANGELOG.md` records meaningful user-facing or developer-facing changes.

Rules:

- Do not dump git commits into the changelog.
- Use newest version first.
- Group entries by `Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`, and `Security` when useful.
- Include dates when a release/version is known.
- For unreleased work, use an `Unreleased` section.

### FEATURES.md

`FEATURES.md` tracks implemented, planned, maybe-later, and rejected/out-of-scope features.

Use it for product-like repositories, apps, games, CLIs, scripts, SaaS ideas, and tools.

Do not duplicate detailed requirements from FSD/TSD/GDD. Link to those documents when they exist.

Suggested structure:

```markdown
# Features

## Implemented
- 

## Planned
- 

## Maybe Later
- 

## Rejected / Out of Scope
- 
```

### Architecture Documentation

Use `docs/architecture-template.md` as the starting point when a repository needs architecture documentation.

Update architecture docs when changing:

- system components, layers, or service boundaries
- technology stack or key dependencies
- data flow, integration points, or external APIs
- deployment topology or environments
- authentication/authorization patterns
- significant design decisions with architectural impact

Keep it factual and current. Do not document planned or aspirational architecture as if it exists.

### User Guide

Use `docs/user-guide-template.md` as the starting point for GUI applications, desktop apps, web apps, or any client-facing product with a user-facing interface.

Create or update the user guide when changing:

- navigation structure, screens, or views
- key user workflows or task flows
- settings or configuration accessible to end users
- visible error messages or troubleshooting steps

Do not write user guide content for internal tools, CLIs, or developer-facing libraries unless the task explicitly requires it.

### docs/

Use `docs/` for documentation that would make `README.md` too long.

Prefer linking from `README.md` to deeper docs instead of bloating the README.

### Documentation Safety

Do not invent:

- project status
- implemented features
- roadmap dates
- performance claims
- benchmark numbers
- compatibility guarantees
- deployment instructions
- screenshots or UI behavior
- third-party support claims

If documentation cannot be verified from code, tests, provided specs, or existing docs, mark it as unknown, omit it, or ask.

When a task comes from an issue, ticket, FSD, TSD, GDD, or feature entry, reference it in the PR description when practical.

---

## CI/CD and Workflow Automation

CI/CD changes are safety-sensitive because they can affect builds, releases, deployments, secrets, and production behavior.

Rules:

- Do not create, modify, remove, or rename CI/CD workflows unless the task explicitly asks for CI/CD work.
- Preserve the existing CI/CD provider and structure. Do not switch between GitHub Actions, GitLab CI, Azure DevOps, Jenkins, or other systems unless explicitly requested.
- Do not add deployment, publishing, release, package-upload, infrastructure, or secret-dependent jobs unless explicitly requested.
- Do not add, print, expose, rename, or guess secrets, tokens, certificates, credentials, or secret names unless the repository already documents the exact name and the task requires referencing it.
- Do not weaken existing checks, branch protection assumptions, test gates, code scanning, dependency scanning, or approval gates unless explicitly requested.
- Prefer minimal workflow changes that validate the touched project or script.
- If editing CI/CD, document the intended trigger, job purpose, required permissions, and validation method.
- If a workflow cannot be validated locally, state what was checked and what still needs to be verified by the hosted CI system.
- For CI/CD guidance, use `docs/ci-cd-guidelines.md` when present.

Recommended CI/CD order for new projects:

1. Build and test only.
2. Add lint/format checks when stable.
3. Add packaging/release automation after the project has versioning and changelog discipline.
4. Add deployment only when the deployment target, rollback process, and required secrets are documented.

---

## Comments and Summaries

Use comments and summaries to clarify important information, not to narrate obvious code or fill space.

Comment rules:

- Comments should explain intent, constraints, tradeoffs, non-obvious behavior, edge cases, external requirements, or safety concerns.
- Do not comment obvious assignments, simple conditionals, straightforward loops, or self-explanatory method calls.
- Do not add large header comments, banner comments, or wide comment blocks unless the surrounding file already uses that style.
- Prefer clearer names and simpler code over comments that explain confusing code.
- Preserve useful existing comments, but remove or update stale comments when editing related code.
- Public API/XML/doc comments are acceptable when the project already uses them or when they clarify behavior for consumers. Do not add XML comments to every member by default.

Summary rules:

- Task/PR summaries should be short, specific, and factual.
- Summarize what changed, why it changed when relevant, validation performed, and remaining risks.
- Do not include generic praise, broad filler, repeated bullets, or long explanations that belong in design docs.
- Do not mention AI assistant/tool/model names in summaries unless the task is explicitly about AI tooling or agent-guideline files.

Good comment:

```csharp
// Keep this timeout below the gateway limit so retries happen client-side.
private static readonly TimeSpan RequestTimeout = TimeSpan.FromSeconds(25);
```

Bad comments:

```csharp
// Set allowed to false.
var allowed = false;

// If the order is null, throw an exception.
if (order == null)
	throw new ArgumentNullException(nameof(order));
```

---

## Artifact and Bundle Naming

Use stable, searchable filenames for generated artifacts, bundles, and release packages.

Rules:

- Do not use vague suffixes such as `final`, `final2`, `new`, `latest`, `copy`, `fixed`, or `v2`.
- For distributed archives, put the semantic version immediately before the file extension.
- Use `MAJOR.MINOR.PATCH` format.
- Keep the artifact name prefix stable across versions.
- Internal files inside a template/starter bundle should keep stable names unless they are themselves versioned output artifacts.

Pattern:

```text
<artifact-name>_<major>.<minor>.<patch>.<extension>
```

Examples:

```text
agent-guidelines-pack_1.18.0.zip
project-starter_0.3.0.zip
backup-photos_1.1.0_report.txt
```

---

## Code Conventions

Detailed code conventions live in separate files so this root `AGENTS.md` stays operational and agent-friendly.

Use repository-specific convention files first. If no more specific convention exists, use these defaults:

- C#/.NET: `docs/coding-conventions-csharp.md`
- Unity/C#: `docs/coding-conventions-unity.md` (extends the C#/.NET conventions)
- Shell scripts: `docs/coding-conventions-shell.md`
- Python scripts: `docs/coding-conventions-python.md`
- Shell/Python shared rules: `docs/coding-conventions-scripts.md`
- CI/CD and workflow automation: `docs/ci-cd-guidelines.md`

Rules:

- Follow the nearest applicable convention file for the files being edited.
- If a child `AGENTS.md` points to a different convention file, use the child instruction for that path.
- Preserve existing local style when it conflicts with a generic convention and the task is not style cleanup.
- Preserve existing indentation style: use spaces in files/repos that already use spaces, and tabs in files/repos that already use tabs. For new files, follow the nearest `.editorconfig` or convention file.
- Preserve existing user-facing string style: ASCII vs Unicode punctuation, decorative separators, labels, prompts, CLI output, terminal headers, and UI text should stay consistent with nearby code.
- Shared templates and guideline examples should use generic domain names and generic enums, such as `OrderStatusEnum`, unless the example is intentionally project-specific.
- Follow comment and summary discipline: no obvious code comments, no wide/banner comments unless local style uses them, and concise summaries only.
- Do not rewrite unrelated code just to satisfy conventions.
- Add new language/framework convention files only when the repository actually needs them.

Future convention files can be added for TypeScript, Python applications, Go, Rust, Java, mobile, frontend, game development, or game/modding projects.

---

## Git Workflow

### Choosing a Branching Model

Pick the model that matches the repository type. Document the choice in the repository's own `AGENTS.md` or child instruction file.

| Model | Use when |
|-------|----------|
| **Git Flow** | Applications with formal release cycles, staging environments, parallel hotfix/feature lanes, or a team that gates `main` as production-only. Requires `main`/`master` + `develop`/`dev` as long-lived branches. |
| **GitHub Flow** | Docs, seed/template repos, libraries, solo projects, or any repo with a single long-lived branch. All work merges directly to `main`/`master`. |

If the repository does not specify a model, use Git Flow for applications and GitHub Flow for everything else.

---

### Git Flow

Use for applications that need a stable `main`/`master` protected from in-progress work, or that release on a defined schedule.

**Long-lived branches:**

| Branch | Role |
|--------|------|
| `main` or `master` | Production/release — only released code lands here. |
| `develop` or `dev` | Integration — all completed feature work merges here first. |

**Branch families:**

| Family | Base | PR target | Use for |
|--------|------|-----------|---------|
| `feature/*` | `develop` | `develop` | All normal work: implementation, docs, tests, refactors, tooling, non-emergency fixes |
| `release/*` | `develop` | `main` | Release preparation, version bumps, release notes, final stabilization |
| `hotfix/*` | `main` | `main` | Urgent fixes for production/released code |

After merging a `release/*` or `hotfix/*` into `main`, bring the changes back to `develop` through a separate PR or approved merge.

Do not create `docs/*`, `test/*`, `refactor/*`, `chore/*`, or `bugfix/*` branches. Use `feature/*` for all normal work including documentation, tests, maintenance, and non-emergency fixes.

---

### GitHub Flow

> **This repository uses GitHub Flow.**

Use for docs, seed/template repos, libraries, solo projects, or any repo with no separate staging/integration branch.

**Long-lived branches:**

| Branch | Role |
|--------|------|
| `main` or `master` | The only long-lived branch. Serves as both integration and production. |

**Branch families:**

| Family | Base | PR target | Use for |
|--------|------|-----------|---------|
| `feature/*` | `main` | `main` | All work: features, fixes, docs, refactors, releases, urgent changes |

There are no `release/*` or `hotfix/*` branches. Cut releases by tagging a commit on `main`. Urgent fixes use a normal `feature/*` branch.

Do not create a `develop` branch in a GitHub Flow repository.

---

### Git and PR Preflight

Before creating a new branch, starting duplicate work, or opening a pull request, agents MUST check the current repository and remote state when tools are available.

Run, when practical:

```bash
git fetch --all --prune
git status --short
git branch --show-current
git log --oneline --decorate --graph --all -20
git branch -r --merged origin/main
```

If GitHub CLI is available, also check:

```bash
gh pr status
gh pr list --state open --limit 20
gh pr list --state merged --limit 20
```

Rules:

- Do not create duplicate branches or PRs for work already merged into the integration branch.
- If an equivalent branch or open PR already exists, update/report that branch/PR instead of creating another one.
- If the requested change appears already merged, report that finding and ask before creating a new branch.
- If remote/PR checks cannot be run, state the limitation and continue using the available local Git evidence.
- Do not assume stale local branch state reflects hosted PR state; fetch/prune first when possible.

### Long-Lived Branches

- Do not delete, rename, or force-push long-lived branches.
- If the primary long-lived branch does not exist and branch setup is part of the task, create it from the current default branch.
- In Git Flow repositories, do not merge feature work directly to `main`/`master`; route it through `develop`/`dev` first.
- In GitHub Flow repositories, do not create a `develop` or `dev` branch.

### Branch Naming

All branches use lowercase kebab-case. Do not include dates, usernames, AI/model/tool names, or vague words like `changes`, `updates`, `fixes`, `final`, or `wip` unless they are part of a real issue key or release version.

**Feature branch** (both models):

```text
feature/<short-kebab-description>
```

**Release branch** (Git Flow only):

```text
release/<major>.<minor>.<patch>
```

**Hotfix branch** (Git Flow only):

```text
hotfix/<short-kebab-description>
```

Examples:

```text
feature/add-order-export
feature/update-agent-guidelines
feature/sync-agent-guidelines-1-28-0
release/1.28.0
hotfix/fix-login-crash
```

### Pull Request Rules

Every task branch MUST create or propose a pull request. Agents must not randomly skip PR creation based on preference.

- If the platform/repository supports PR creation, create a PR for the completed task branch.
- If PR creation is not available, provide exact PR instructions instead of pretending a PR exists.
- Do not auto-merge pull requests.
- Do not approve your own pull request when review/approval features exist.
- Do not bypass branch protection.
- For local-only or solo experimental repositories where hosted PRs are unavailable, still keep changes isolated on a branch when possible and report the intended PR details.

Default PR targets by model:

| Model | Branch family | Target |
|-------|--------------|--------|
| Git Flow | `feature/*` | `develop` |
| Git Flow | `release/*` | `main` |
| Git Flow | `hotfix/*` | `main` |
| GitHub Flow | `feature/*` | `main` |

PR titles should use a concise imperative phrase without branch prefixes, issue clutter, or AI/model/tool names.

Good PR titles:

```text
Add order export validation
Fix payment status mapping
Sync agent guidelines 1.24.0
```

Avoid PR titles like:

```text
feature/add-order-export
Chore updates
AI generated changes
Final fixes
```

### No AI Names in Git Artifacts

Do not include AI assistant, tool, provider, or model names in Git artifacts or review text.

This applies to:

- branch names
- commit messages
- PR titles
- PR descriptions
- review comments
- changelog entries
- release notes
- generated helper text

Avoid names such as `codex`, `claude`, `chatgpt`, `gpt`, `gemini`, `copilot`, model names, or similar branding.

Write Git artifacts as if authored by the repository maintainer. Describe the actual change, not the tool used to create it.

Allowed exception: files whose purpose is AI-agent configuration or documentation, such as `AGENTS.md` and `CLAUDE.md`, may reference agent/tool names where technically necessary.

### Commit Rules

- Keep commits focused and logically grouped.
- Use imperative commit messages.
- Prefer concise commit messages that describe the user-facing or code-facing change.
- Do not include secrets, credentials, tokens, local paths, machine-specific files, or AI assistant/model/tool names.

Examples:

```text
Add order export validation
Fix enum mapping for payment status
Sync agent guidelines
```

---

## Command Safety

Do not run destructive commands unless explicitly instructed.

Examples of destructive commands:

```bash
git reset --hard
git clean -fd
git push --force
git branch -D <branch>
rm -rf <path>
docker system prune
DROP DATABASE
```

Also avoid destructive equivalents in package managers, database tools, cloud CLIs, and deployment scripts.

If a destructive action seems necessary, explain the reason and ask first.

---

## Boundaries

Do not modify without explicit instruction:

- secrets, credentials, tokens, certificates, or `.env*` files
- production deployment files
- CI/CD pipelines
- workflow permissions and deployment triggers
- infrastructure-as-code files
- database migrations
- generated code
- lock files
- package references or dependency versions
- public API contracts
- authentication/authorization behavior
- payment, billing, or licensing behavior
- telemetry, audit, or compliance behavior

Do not commit secrets or machine-specific files.

---

## Dependency Policy

- Do not add production dependencies unless explicitly required by the task.
- Prefer built-in language/framework APIs before adding packages.
- If a dependency is necessary, choose a maintained package and explain why.
- Do not change package versions as part of unrelated work.
- Do not replace an existing library/framework unless the task explicitly asks for it.
- For test-only dependencies, keep the change scoped to test projects.

---

## Database and Migrations

- Do not create or modify database migrations unless the task requires schema changes.
- Do not manually edit generated migration snapshots unless necessary and explained.
- When changing persistence models, check whether migrations, tests, seed data, or docs need updates.
- Do not run destructive database commands unless explicitly instructed.
- Do not change connection strings, production database settings, or secrets.

---

## Generated Files

Do not manually edit generated files.

Instead:

- update the source/template/schema that produces them
- regenerate using the project’s documented command
- explain the regeneration command in the validation summary

If regeneration is not possible, explain the limitation and keep the manual edit minimal.

---

## Game Development Work

When working on a game, mod, prototype, or game-adjacent tool, prefer project-specific design documentation over generic assumptions.

Use the GDD/Game Design Document when provided. It should guide:

- core gameplay loop
- mechanics and rules
- player progression
- level, encounter, item, quest, or content design
- UI/UX and feedback expectations
- balancing goals and constraints
- narrative or world constraints
- platform, engine, and input assumptions
- acceptance criteria for playable behavior

Rules:

- Do not change core gameplay, economy, controls, progression, or balance outside the GDD/task scope.
- If engine, version, target platform, mod loader, or asset pipeline matters, identify it before making broad changes.
- Preserve existing save compatibility, content IDs, asset references, scene names, prefab names, and serialized data unless the task requires changing them.
- For mods, consider game version, mod loader, compatibility, load order, save backup, and rollback.
- For gameplay changes, include a short manual test plan when automated tests are not practical.
- If the GDD conflicts with code, assets, FSD/TSD, or the task, report the conflict instead of guessing.

---

## Agent Completion Checklist

Before finishing a task, confirm:

- Applicable upstream/repository/child `AGENTS.md` instructions were checked for the changed paths.
- Applicable convention docs under `docs/` were checked for changed code/scripts/docs.
- Existing indentation style was preserved in modified files.
- Existing user-facing text/output style was preserved, including ASCII vs Unicode punctuation and decorative separators.
- Comments and summaries are purposeful, concise, and do not explain obvious code.
- C# control-flow style was preserved or applied: no inline `if (...) return ...;`, braces required for multi-statement blocks, and blank line after a completed control block before the next independent statement.
- Git/PR preflight was run when available, or unavailable checks were reported.
- Existing branches/PRs/merged work were checked to avoid duplicate work.
- A new task branch was created, or branch creation was impossible and the reason is reported.
- Changes are focused on the requested task.
- Provided FSD/TSD/GDD/acceptance criteria were followed, or conflicts/gaps were reported.
- New behavior has unit tests when feasible, or a clear explanation why tests were not added.
- The affected project was built when possible, or skipped with a clear reason.
- Relevant automated tests were run when available, or skipped with a clear reason.
- Smoke tests or quick manual checks were run when practical, or skipped with a clear reason.
- The implementation was rechecked against requirements and changed files.
- Format/lint checks were run when configured, or skipped with a clear reason.
- CI/CD changes were explicitly requested, minimal, and documented, or CI/CD was left untouched.
- `README.md`, `CHANGELOG.md`, `FEATURES.md`, or `docs/` were updated when the change affected public behavior, setup, commands, features, versioned output, specifications, or documented limitations.
- Architecture documentation was updated when components, integrations, data flow, deployment, or key design decisions changed.
- User guide was updated when navigation, workflows, settings, or visible behavior changed in a GUI or client-facing app.
- `.editorconfig` impact was considered when changing formatting/style conventions.
- The repository PR template was used when creating or proposing a pull request.
- Branch family follows strict Git Flow: `feature/*`, `release/*`, or `hotfix/*`.
- A pull request was created, or exact PR instructions were provided.
- PR title, branch name, source branch, and target branch follow the strict Git Flow conventions.
- Branch names, commit messages, PR text, changelog entries, release notes, and helper text do not contain AI assistant/model/tool names.
- The PR was not auto-merged.

---

## PR Description Template

Use `.github/pull_request_template.md` when it exists. Otherwise, use this structure when creating or proposing a pull request:

```markdown
## Summary
- 

Keep the summary concise and factual. Do not add generic filler or mention AI assistant/tool/model names.

## Changes
- 

## Requirements / Spec Alignment
- 

## Documentation
- [ ] README.md updated if needed
- [ ] CHANGELOG.md updated if needed
- [ ] FEATURES.md/docs updated if needed

## Validation
- [ ] Build
- [ ] Unit tests added/updated where feasible
- [ ] Tests
- [ ] Smoke/manual check where practical
- [ ] Implementation rechecked against requirements
- [ ] Comments/summaries are concise and do not explain obvious code
- [ ] Format/lint

## Branching / Merge Safety
- [ ] Git/PR preflight checked remote state, open PRs, and recently merged PRs where available
- [ ] Branch name follows `feature/<short-kebab-description>`, `release/<version>`, or `hotfix/<short-kebab-description>`
- [ ] Branch family follows strict Git Flow
- [ ] PR targets the correct Git Flow branch
- [ ] No auto-merge requested/performed

## Notes / Risks
- 
```

For .NET/C# repositories, prefer these validation entries when applicable:

```markdown
- [ ] `dotnet format --verify-no-changes`
- [ ] `dotnet build`
- [ ] `dotnet test`
```

---

## Updating This File

Update `AGENTS.md` when:

- project structure changes
- repository areas need different language, framework, game/mod, script, or workflow instructions
- build/test/lint/smoke-test commands change
- FSD/TSD/GDD conventions or templates change
- recurring agent mistakes are discovered
- new architectural boundaries are introduced
- a new language/framework profile becomes necessary

Keep updates short, operational, and specific. Do not turn this file into a general tutorial, full code style guide, or full architecture document.

Detailed style rules belong in separate files under `docs/`.

---

## References

- `AGENTS.md` is a repository-level instruction file for coding agents.
- Codex reads `AGENTS.md` files before doing work and supports project-level instruction layering.
- Strict Git Flow uses `main`, `develop`, `feature/*`, `release/*`, and `hotfix/*` branches. In this pack, normal work uses `feature/*` only.
- Visual Studio Remove and Sort Usings should be the default using-directive cleanup behavior for C# repositories.
