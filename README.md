# Repo Seed

Reusable coding-agent guidance and project-document templates with a small, predictable synchronization tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- concise coding-agent instructions and focused supporting conventions;
- read-only documentation templates for five project profiles;
- missing-only scaffolding for project documents, `.gitignore`, `.editorconfig`, and GitHub issue templates;
- one universal release archive;
- a sync script copied into each target repository for future updates.

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

Root files describe `repo-seed` itself. They are never used as target sync sources.

## Sync Behavior

Sync has only two ownership rules:

1. Managed guidance, the sync script, and reference templates are always overwritten from the selected pack.
2. Project-owned files are created only when explicitly scaffolded and missing.

There is no target state file, hash tracking, conflict directory, migration cleanup, or Git branch handling. Do not customize managed files in a target repository. Put project-specific agent rules in `.agents/project.md` or a child `AGENTS.md`.

Updated templates remain under `docs/templates/` as read-only references. Agents compare a relevant live document with its source template and update the live document when practical. Git history supplies the template diff.

## Profiles

All profiles receive the complete agent-guidance set, sync script, and common reference templates.

| Profile | Additional project templates |
|---|---|
| `minimal` | None |
| `library` | None |
| `app` | Features, architecture, user guide, FSD, and TSD |
| `game` | Features and GDD |
| `full` | Every template |

The default profile is `full`.

## Use an Extracted Pack

The script discovers the pack containing it:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --scaffold-project-files \
  --scaffold-github-templates
```

On later updates, the managed script already copied into the project can use a newer extracted pack:

```bash
python scripts/sync-docs.py \
  --source /path/to/extracted/pack \
  --target . \
  --profile app
```

Use `--dry-run` to preview operations. `--scaffold-project-files` creates missing project documents, `.gitignore`, and `.editorconfig`. `--scaffold-github-templates` creates missing bug, feature, and issue configuration files.

## Build the Release

```bash
python scripts/build-release-bundles.py
```

The output is `dist/repo-seed-pack-3.0.0.zip`. It contains the top-level `pack/` directory and every asset listed in `pack/manifest.json`.

## Validate

```bash
python -m unittest discover -s tests -v
python pack/files/scripts/sync-docs.py --help
python scripts/build-release-bundles.py --help
python -m py_compile pack/files/scripts/sync-docs.py scripts/build-release-bundles.py
git diff --check
```

See [document ownership](docs/project/document-ownership.md) and [features](docs/project/features.md) for repository-specific details.
