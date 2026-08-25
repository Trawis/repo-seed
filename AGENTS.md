# AGENTS.md

Repository instructions for contributors and coding agents working on `repo-seed`.

**Document role**: Repository-only instructions

**Sync behavior**: Never copied into target repositories

**Distributed instructions**: `pack/files/AGENTS.md`

---

## Distributed Guidance Changes

When changing distributed agent guidance, inspect the specific managed guidance
being modified and its related tests. Do not treat distributed instructions as
repository-level instructions for unrelated `repo-seed` work.

## Repository Scope

This repository maintains a reusable documentation and coding-agent guidance pack.

Ownership boundaries:

- Root documents describe `repo-seed` itself and are never sync sources.
- `pack/manifest.json` is the sole distributed-asset inventory.
- `pack/README.md` and `pack/LICENSE` are package-only archive files and are never synced.
- `pack/files/` mirrors target paths and contains managed files, reference templates, and the sync script.
- `docs/project/` contains project-owned documentation about `repo-seed`.
- `scripts/` contains repository tooling.
- `tests/` contains automated validation for the tooling and pack contents.

Do not use a root repository document as a sync source.

## Working Rules

- Make the smallest change that satisfies the task; do not include unrelated
  cleanup or alter sync, ownership, migration, profile, scaffold, or packaging
  behavior unless the task requires it.
- Do not expose secrets, run destructive commands without authorization, hide
  failed or skipped checks, bypass branch protections, auto-merge, or approve
  your own pull request.
- Prefer source files over generated or release artifacts.
- If a repo-seed behavior or public interface changes, update the affected
  repository-owned documentation.

## GitHub Flow

- `main` is the only long-lived branch.
- Start normal work from an updated `main` using `feature/<short-kebab-description>`.
- Open pull requests against `main`.
- Do not commit directly to `main` or create `develop`, `dev`, release, or hotfix branches.

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
python scripts/build-release-bundle.py --help
python -m py_compile pack/files/scripts/sync-docs.py scripts/build-release-bundle.py
git diff --check
```

Do not claim hosted release behavior is validated locally unless the archive-building path was exercised.
