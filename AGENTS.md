# AGENTS.md

Repository instructions for contributors and coding agents working on `repo-seed`.

**Document role**: Repository-only instructions

**Sync behavior**: Never copied into target repositories

**Distributed instructions**: `pack/files/AGENTS.md`

---

## Required Guidance

Read [`pack/files/AGENTS.md`](pack/files/AGENTS.md) before changing this repository. It contains the generic safety, validation, documentation, coding, and Git rules maintained by this pack.

The rules below override the distributed guidance only for work in `repo-seed`.

## Repository Scope

This repository maintains a reusable documentation and coding-agent guidance pack.

Ownership boundaries:

- Root documents describe `repo-seed` itself and are never sync sources.
- `pack/manifest.json` is the sole distributed-asset inventory.
- `pack/files/` mirrors target paths and contains managed files, reference templates, and the sync script.
- `docs/project/` contains project-owned documentation about `repo-seed`.
- `scripts/` contains repository tooling.
- `tests/` contains automated validation for the tooling and pack contents.

Do not use a root repository document as a sync source.

## Git Workflow

- Use `feature/<short-kebab-description>` for normal work.
- Target `develop` or `dev` when either integration branch exists.
- Target `main` or `master` only when no integration branch exists.
- Do not create a missing integration branch as a side effect of ordinary work.

## Relevant Conventions

For Python or sync-script changes, read:

- [`pack/files/.agents/conventions/scripts.md`](pack/files/.agents/conventions/scripts.md)
- [`pack/files/.agents/conventions/python.md`](pack/files/.agents/conventions/python.md)

For workflow changes, also read:

- [`pack/files/.agents/guidelines/ci-cd.md`](pack/files/.agents/guidelines/ci-cd.md)

## Repository Validation

For sync-script or packaging changes, run:

```bash
python -m unittest discover -s tests -v
python pack/files/scripts/sync-docs.py --help
python scripts/build-release-bundles.py --help
python -m py_compile pack/files/scripts/sync-docs.py scripts/build-release-bundles.py
git diff --check
```

Do not claim hosted release behavior is validated locally unless the archive-building path was exercised.
