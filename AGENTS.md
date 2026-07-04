# AGENTS.md

Repository instructions for contributors and coding agents working on `repo-seed`.

**Document role**: Repository-only instructions

**Sync behavior**: Never copied into target repositories

**Distributed instructions**: `pack/AGENTS.md`

---

## Required Guidance

Read [`pack/AGENTS.md`](pack/AGENTS.md) before changing this repository. It contains the generic safety, validation, documentation, coding, and Git rules maintained by this pack.

The rules below override the distributed guidance only for work in `repo-seed`.

## Repository Scope

This repository maintains a reusable documentation and coding-agent guidance pack.

Ownership boundaries:

- Root documents describe `repo-seed` itself and are never sync sources.
- `pack/` contains managed files copied into target repositories.
- `docs/templates/` contains managed reference templates and one-time scaffolding sources.
- `docs/project/` contains project-owned documentation about `repo-seed`.
- `scripts/` contains repository tooling.
- `tests/` contains automated validation for the tooling and pack contents.

Do not use a root repository document as a sync source.

## Git Workflow

This repository uses GitHub Flow:

- `main` is the only long-lived branch.
- Use `feature/<short-kebab-description>` for all work.
- Target pull requests to `main`.
- Do not create `develop`, `release/*`, or `hotfix/*` branches.

## Relevant Conventions

For Python or sync-script changes, read:

- [`pack/.agents/conventions/scripts.md`](pack/.agents/conventions/scripts.md)
- [`pack/.agents/conventions/python.md`](pack/.agents/conventions/python.md)

For workflow changes, also read:

- [`pack/.agents/guidelines/ci-cd.md`](pack/.agents/guidelines/ci-cd.md)

## Repository Validation

For sync-script or packaging changes, run:

```bash
python -m unittest discover -s tests -v
python scripts/sync-agent-guidelines.py --help
python scripts/build-release-bundles.py --help
python -m py_compile scripts/sync-agent-guidelines.py scripts/build-release-bundles.py
git diff --check
```

Do not claim hosted release behavior is validated locally unless the archive-building path was exercised.
