# Repo Seed

Reusable coding-agent guidance and project-document templates with a small, predictable synchronization tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- portable `AGENTS.md` guidance with a `CLAUDE.md` compatibility wrapper;
- focused documentation, Git, CI/CD, and language references;
- read-only templates for four project profiles plus a complete reference catalog;
- missing-only scaffolding plus verified Markdown scaffold upgrades;
- one universal release archive with package instructions and license;
- a sync script copied into each target repository for future updates.

## Requirements

- Python 3.10 or newer;
- a writable target repository directory;
- Windows, Linux, or macOS.

The scripts use only the Python standard library. Pull-request CI validates Python 3.10 and 3.13 on Linux. Run local checks on the target operating system when filesystem behavior matters.

## Safety

Unchanged legacy-managed files with matching recorded hashes are retired, and
current managed files are updated only when their content differs. Project-owned
files are scaffolded or upgraded only when safely verifiable. Modified or
unrecorded legacy files are preserved and reported. Run `--dry-run` first and
commit or back up the target repository because filesystem writes are not
transactional.

Each target keeps `.repo-seed-state.json` as committed ownership metadata.
Profile reductions remove only stale managed files matching their recorded
hashes. Modified stale files remain in place and stay tombstoned for review.

See [Document ownership](docs/project/document-ownership.md) for the authoritative path classification.

## Profiles

All profiles receive the core agent instructions, documentation and Git guidance, sync script, and common reference templates. Specialized guidance is included only where the profile benefits from it.

| Profile | Guidance and project templates |
|---|---|
| `minimal` | Core guidance plus README and changelog |
| `library` | Minimal plus coding conventions, architecture, and an on-demand TSD reference |
| `app` | Library guidance plus FSD and user-guide templates |
| `game` | Library guidance plus Unity conventions and a GDD template |
| `full` | Complete reference catalog; not a project type |

The first sync requires an explicit project profile when no reusable profile is
recorded. Later syncs reuse a recorded `minimal`, `library`, `app`, or `game`
profile when `--profile` is omitted.
Profiles select the managed assets retained in the target. Changing to a smaller
profile prunes unchanged managed assets that are no longer selected; modified
files are preserved. Eligible legacy cleanup applies independently of the
selected profile.

`full` synchronizes every reference template for review. It cannot be combined
with `--scaffold-project-files` because FSD and GDD are mutually exclusive
project models, and it must always be selected explicitly.

Living documents have distinct responsibilities:

- FSD or GDD describes accepted product or gameplay behavior;
- architecture describes the verified current technical system;
- a TSD under `docs/project/designs/` describes one substantial change;
- the user guide describes current user workflows.

Top-level project documents remain stable as projects grow and become concise
indexes when detailed documents are added beneath them.

## Download and First Sync

Download the latest universal ZIP from [GitHub Releases](https://github.com/Trawis/repo-seed/releases), extract it, and preview the sync:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --scaffold-project-files \
  --scaffold-github-templates \
  --dry-run
```

Review the output, then rerun without `--dry-run`.

Optional scaffolding is separated by ownership:

- `--scaffold-project-files` creates missing project documents, or upgrades verified unchanged Markdown;
- `--scaffold-github-templates` creates missing bug, feature, and chooser files, or upgrades verified unchanged Markdown;
- `--scaffold-editorconfig` creates `.editorconfig` only when missing.

Existing project-owned files are preserved unless an eligible Markdown scaffold is
verified unchanged from repo-seed and can be upgraded safely.
On initial sync, version updates, and legacy migration, existing `.gitignore`,
`.editorconfig`, and pull-request templates are explicitly reported as protected
project-owned files.

## Update an Existing Project

Prefer the script from the newly extracted pack so the newest validation runs
before any target file is inspected or changed:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --dry-run
```

The copied `scripts/sync-docs.py` remains available for compatible packs, but it
cannot cross manifest-schema changes and may not contain fixes introduced by a
newer pack. Pass `--profile` to change the recorded profile intentionally.

## Upgrade from Version 3

Version 3 scripts cannot read the version 4 manifest. Run the script from the
newly extracted pack so it can update the target copy:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --profile app \
  --dry-run
```

See [Migrating from Version 1 or 2](docs/project/upgrading-to-3.md) for legacy
installations and [Upgrading to Version 4](docs/project/upgrading-to-4.md) for
the documentation-model changes.

## Source Layout

```text
pack/
  manifest.json              # sole distributed-asset inventory
  README.md                  # package-only quick start
  LICENSE                    # package-only license
  files/                     # mirrors target repository paths
    AGENTS.md
    CLAUDE.md
    .agents/
    docs/templates/
    scripts/sync-docs.py
docs/project/                # live documentation about repo-seed
scripts/                     # repository release tooling
tests/                       # pack and tooling tests
```

Root files describe `repo-seed` itself and are never target sync sources.

## Build and Validate

```bash
python scripts/build-release-bundle.py
python -m unittest discover -s tests -v
python pack/files/scripts/sync-docs.py --help
python scripts/build-release-bundle.py --help
python -m py_compile pack/files/scripts/sync-docs.py scripts/build-release-bundle.py
git diff --check
```

The build creates `dist/repo-seed-pack-<version>.zip` from the inventory declared in `pack/manifest.json`.

## Project and Community

- [Document ownership](docs/project/document-ownership.md)
- [Upgrading to Version 4](docs/project/upgrading-to-4.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Repo Seed is available under the [MIT License](LICENSE).
