# Repo Seed

Reusable coding-agent guidance and project-document templates with a small, predictable synchronization tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- portable `AGENTS.md` guidance with a `CLAUDE.md` compatibility wrapper;
- focused documentation, Git, CI/CD, and language references;
- read-only templates for five project profiles;
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
| `library` | Minimal plus general coding conventions |
| `app` | Library guidance plus features, architecture, user guide, FSD, and TSD |
| `game` | Library guidance plus Unity conventions, features, and GDD |
| `full` | Every managed reference and template |

The default profile is `full`. Profiles select the managed assets retained in
the target. Changing to a smaller profile prunes unchanged managed assets that
are no longer selected; modified files are preserved. Eligible legacy cleanup
applies independently of the selected profile.

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

## Update an Existing Project

The managed script copied into the target can use a newer extracted pack:

```bash
python scripts/sync-docs.py \
  --source /path/to/extracted/pack \
  --target . \
  --profile app \
  --dry-run
```

See [Upgrading to Version 3](docs/project/upgrading-to-3.md) when migrating from the old stateful 1.x or 2.x synchronizer.

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
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Repo Seed is available under the [MIT License](LICENSE).
