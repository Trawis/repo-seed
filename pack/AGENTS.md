# AGENTS.md

Repository-level instructions for coding agents.

**Document role**: Managed coding-agent instructions

**Sync destination**: `AGENTS.md`

**Version**: 2.0.0

---

## Start Here

Before changing files:

1. Follow the current user request.
2. Read `.agents/project.md` when it exists.
3. Read the nearest child `AGENTS.md` for every path you may change.
4. Read relevant live requirements under `docs/project/`.
5. Load only the specialized guidance needed for the task.

Instruction precedence is:

1. Current user instructions.
2. The closest applicable child `AGENTS.md`.
3. `.agents/project.md`.
4. This root file.
5. Managed supporting guidance and general conventions.

Report meaningful conflicts instead of guessing.

## Document Authority

- `README.md` and `CHANGELOG.md` are project-owned root entry points.
- `docs/project/` contains authoritative live project documentation.
- `docs/templates/` contains managed references only.
- Never edit `docs/templates/` in a target repository.
- Template placeholders are not requirements.
- When a task changes documented behavior, update the relevant project-owned documentation when practical.

Read `.agents/guidelines/documentation.md` for documentation work or changes affecting public behavior, setup, architecture, features, guides, or specifications.

## Minimal Context

- Inspect relevant files before editing.
- Prefer the smallest safe change that satisfies the task.
- Preserve existing architecture, public APIs, project boundaries, naming, indentation, and user-facing text style.
- Do not reformat, rename, or clean up unrelated code.
- Do not add obvious comments or generic documentation filler.
- Prefer source files over generated output.

## Task Workflow

For implementation work:

1. Establish the applicable instructions and requirements.
2. Inspect the current implementation and nearby tests.
3. Check Git and pull-request state when branch or PR work is involved.
4. Implement a focused change.
5. Add or update relevant tests when feasible.
6. Build the affected project when a build command exists.
7. Run focused tests, lint/format checks, and a practical smoke check.
8. Recheck behavior against the task and live specifications.
9. Update relevant project-owned documentation.
10. Report changes, validation, limitations, and remaining risks accurately.

For review or diagnosis requests, inspect and report evidence without changing files unless a fix is requested.

## Safety Boundaries

Do not:

- expose, invent, rename, or commit secrets, credentials, tokens, certificates, or private keys;
- run destructive commands without explicit authorization;
- delete, rename, force-push, or rewrite long-lived branches;
- bypass branch protection, approvals, tests, scanning, or deployment gates;
- auto-merge or approve your own pull request;
- modify production deployment, infrastructure, database migrations, authentication, payment, licensing, telemetry, or public contracts unless the task explicitly requires it;
- add or replace production dependencies without a clear task requirement;
- hide failures, skipped checks, conflicts, or uncertainty.

Ask before broad refactors, architecture changes, framework replacement, schema changes, repository restructuring, or new cross-codebase patterns unless the task explicitly requests them.

## Code and Script Changes

- Follow repository-specific conventions first.
- Preserve the local style of every touched file.
- Keep public behavior and compatibility stable unless the task requires a change.
- Validate inputs and failure paths for scripts and user-facing entry points.
- Keep comments focused on constraints, intent, tradeoffs, or non-obvious behavior.
- Add tests for behavior changes, bug fixes, validation, and important edge cases when practical.

Load applicable managed conventions:

- C#/.NET: `.agents/conventions/csharp.md`
- Unity/C#: `.agents/conventions/unity.md` and the C# conventions
- Python scripts: `.agents/conventions/python.md`
- Shell scripts: `.agents/conventions/shell.md`
- Shared script rules: `.agents/conventions/scripts.md`

## Git and Pull Requests

Follow the branching model documented in `.agents/project.md`, a child `AGENTS.md`, or repository documentation.

When no model is documented:

- prefer GitHub Flow for libraries, documentation, templates, and solo repositories;
- use Git Flow only when the application clearly maintains a separate integration branch.

Normal work uses `feature/<short-kebab-description>`. Branch names, commits, PR text, changelog entries, and release notes must describe the work and must not contain assistant, model, or tool names.

Before creating branches or PRs, check remote state, existing branches, open PRs, and recently merged work when tooling is available. Do not duplicate existing work.

Read `.agents/guidelines/git.md` before branch creation, history changes, commits, pushes, or pull-request work.

## CI/CD

CI/CD changes are safety-sensitive.

- Do not create, remove, rename, or materially alter workflows unless explicitly requested.
- Preserve the existing provider, permissions, triggers, gates, and secret references.
- Do not add publishing, release, deployment, or infrastructure behavior implicitly.
- State what was validated locally and what still requires hosted verification.

Read `.agents/guidelines/ci-cd.md` before modifying workflow or deployment automation.

## Requirements and Specifications

When provided:

- treat the FSD as authoritative for user-facing behavior and acceptance criteria;
- treat the TSD as authoritative for technical constraints, architecture, integrations, and data flow;
- treat the GDD as authoritative for gameplay intent, progression, balance, content, and player experience;
- treat tickets and explicit acceptance criteria as task requirements.

If these sources conflict, stop and report the conflict. Do not implement behavior outside the requested scope.

## Validation

Use the narrowest relevant checks available, generally in this order:

1. Build the affected project.
2. Run focused automated tests.
3. Run configured lint and format checks.
4. Perform a practical smoke or manual check.
5. Recheck the diff and documented behavior.

Do not run irrelevant commands for languages or projects that are not present. If a check cannot run, state exactly why.

## Managed and Project-Owned Files

Routine guideline sync manages:

- `AGENTS.md` and `CLAUDE.md`;
- `.agents/guidelines/` and `.agents/conventions/`;
- `docs/templates/`;
- `.editorconfig`, the PR template, the sync script, and pack metadata.

Project-owned files include:

- `.agents/project.md`;
- `README.md` and `CHANGELOG.md`;
- everything under `docs/project/`;
- any unmapped repository file.

Do not customize managed files in target repositories. Put root-level project rules in `.agents/project.md` and module-specific rules in child `AGENTS.md` files.

## Completion

Finish with a concise factual summary containing:

- what changed;
- what was validated;
- checks that could not run and why;
- remaining risks, conflicts, or manual follow-up.

Never claim a build, test, push, pull request, deployment, or verification succeeded unless it actually did.
