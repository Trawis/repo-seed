# Project Name

Short description of what this project does and who it is for.

## Status

Current status: `planning`, `prototype`, `active`, `maintenance`, or `archived`.

## Features

See [`FEATURES.md`](FEATURES.md) for implemented, planned, maybe-later, and out-of-scope features.

## Requirements

Document required runtimes, SDKs, databases, services, tools, or platform requirements here.

## Setup

```bash
# install/setup commands
```

## Build

```bash
# build command
```

## Test

```bash
# test command
```

## Run

```bash
# run command
```

## Configuration

Describe required configuration, environment variables, local settings, and safe defaults.

Do not document real secrets.

## Usage

Add examples for common usage.

## Documentation

- [`AGENTS.md`](AGENTS.md) — AI-agent workflow and repository rules
- [`CLAUDE.md`](CLAUDE.md) — Claude Code wrapper that imports `AGENTS.md`
- [`CHANGELOG.md`](CHANGELOG.md) — version history
- [`FEATURES.md`](FEATURES.md) — feature state
- [`docs/coding-conventions-csharp.md`](docs/coding-conventions-csharp.md) — C#/.NET conventions
- [`docs/coding-conventions-scripts.md`](docs/coding-conventions-scripts.md) — shared script conventions
- [`docs/coding-conventions-python.md`](docs/coding-conventions-python.md) — Python script conventions
- [`docs/coding-conventions-shell.md`](docs/coding-conventions-shell.md) — shell script conventions
- [`.editorconfig`](.editorconfig) — baseline formatting/style configuration
- [`.github/pull_request_template.md`](.github/pull_request_template.md) — pull request checklist
- [`docs/fsd-template.md`](docs/fsd-template.md) — Functional Specification Document template
- [`docs/tsd-template.md`](docs/tsd-template.md) — Technical Specification Document template
- [`docs/gdd-template.md`](docs/gdd-template.md) — Game Design Document template
- [`docs/ci-cd-guidelines.md`](docs/ci-cd-guidelines.md) — CI/CD and workflow automation guidance
- [`docs/architecture-template.md`](docs/architecture-template.md) — architecture documentation template
- [`docs/user-guide-template.md`](docs/user-guide-template.md) — user guide template for GUI and client-facing apps
- [`docs/readme-template.md`](docs/readme-template.md) — generic starter `README.md` copied into target repos via `--include-project-docs`
- [`docs/changelog-template.md`](docs/changelog-template.md) — generic starter `CHANGELOG.md` copied into target repos via `--include-project-docs`
- [`docs/features-template.md`](docs/features-template.md) — generic starter `FEATURES.md` copied into target repos via `--include-project-docs`
- [`scripts/sync-agent-guidelines.py`](scripts/sync-agent-guidelines.py) — sync this pack from `repo-seed` into other repositories
- [`.agent-guidelines-version`](.agent-guidelines-version) — synced guideline pack version marker


Core pack rules include instruction strictness levels, Git/PR preflight checks, strict Git Flow branch families, mandatory PR creation/proposal behavior, CI/CD safety guidance, no AI/model names in Git artifacts, repo-seed sync workflow with stable script filename, indentation preservation for existing files, user-facing text/output style preservation, generic reusable examples, concise comment/summary discipline, C# guard clauses with statements on the next line, and C# blank-line spacing after completed control blocks.

## Syncing Into Other Repositories

Use `repo-seed` as the central source repository for this pack, then sync a committed snapshot into each target repository.

```bash
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target /path/to/target-repo --dry-run --profile <profile>
python /path/to/repo-seed/scripts/sync-agent-guidelines.py --source /path/to/repo-seed --target /path/to/target-repo --profile <profile>
```

Available profiles: `minimal`, `library`, `app`, `game`, `full` (default).

Pass `--include-project-docs` to also seed a target repo's `README.md`, `CHANGELOG.md`, and `FEATURES.md` from `docs/readme-template.md`, `docs/changelog-template.md`, and `docs/features-template.md` (only when those files are missing in the target). This repository's own root `README.md`, `CHANGELOG.md`, and `FEATURES.md` document `repo-seed` itself and are never synced.

Routine syncs should use a strict Git Flow branch such as:

```text
feature/sync-agent-guidelines-1-25-0
```

Then open a PR into `develop`. Do not auto-merge.

## Known Limitations

List verified limitations. Do not invent unsupported claims.

## License

Add license information.
