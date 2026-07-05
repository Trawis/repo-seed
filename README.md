# Repo Seed

Reusable coding-agent guidance and project-document templates with a small, predictable synchronization tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- portable `AGENTS.md` guidance with a `CLAUDE.md` compatibility wrapper;
- focused documentation, Git, CI/CD, and language references;
- read-only templates for five project profiles;
- missing-only scaffolding for project documents, `.gitignore`, `.editorconfig`, and GitHub issue templates;
- one universal release archive;
- a sync script copied into each target repository for future updates.

## Requirements

- Python 3.10 or newer;
- a writable target repository directory;
- Windows, Linux, or macOS.

The scripts use only the Python standard library. Pull-request CI validates Python 3.10 on Linux. Run local checks on the target operating system when filesystem behavior matters.

## Safety

Managed files are overwritten; project-owned files are scaffolded only when missing. Run `--dry-run` first and commit or back up the target repository before updating because filesystem writes are not transactional.

See [Document ownership](docs/project/document-ownership.md) for the authoritative path classification.

## Profiles

All profiles receive the core agent instructions, documentation and Git guidance, sync script, and common reference templates. Specialized guidance is included only where the profile benefits from it.

| Profile | Guidance and project templates |
|---|---|
| `minimal` | Core guidance plus README, changelog, and `.gitignore` |
| `library` | Minimal plus general coding conventions |
| `app` | Library guidance plus features, architecture, user guide, FSD, and TSD |
| `game` | Library guidance plus Unity conventions, features, and GDD |
| `full` | Every managed reference and template |

The default profile is `full`. Profiles select what is copied; changing to a smaller profile does not delete files installed by a larger profile.

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

- `--scaffold-project-files` creates missing project documents and `.gitignore`;
- `--scaffold-github-templates` creates missing bug, feature, and chooser files;
- `--scaffold-editorconfig` creates `.editorconfig` only when missing.

Existing scaffold destinations are always preserved.

## Update an Existing Project

The managed script copied into the target can use a newer extracted pack:

```bash
python scripts/sync-docs.py \
  --source /path/to/extracted/pack \
  --target . \
  --profile app \
  --dry-run
```

See [Upgrading to Version 3](docs/project/upgrading-to-3.md) when migrating from the old stateful 2.x synchronizer.

## Source Layout

```text
pack/
  manifest.json              # sole distributed-asset inventory
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

The build creates `dist/repo-seed-pack-<version>.zip` from the assets listed in `pack/manifest.json`.

## Project and Community

- [Document ownership](docs/project/document-ownership.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Repo Seed is available under the [MIT License](LICENSE).
