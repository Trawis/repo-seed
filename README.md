# Repo Seed

Reusable coding-agent guidance and project-document templates with a small, predictable synchronization tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- portable `AGENTS.md` guidance with a `CLAUDE.md` compatibility wrapper;
- focused documentation, Git, and CI/CD guidance, independently selectable
  from language/tool conventions;
- a canonical shared label catalog and lightweight issue/decision structure,
  plus an optional tool to reconcile it with hosted GitHub labels;
- read-only templates for four project profiles plus a complete reference catalog;
- baseline scaffolding plus on-demand, named optional-document scaffolds and
  verified Markdown scaffold upgrades;
- one universal release archive with package instructions and license;
- a sync script copied into each target repository for future updates, including
  a diagnostic `--audit` report.

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

## Hosted GitHub Labels

`pack/github-labels.json` and `scripts/sync-github-labels.py` are
repo-seed-side maintainer tooling: unlike everything under `pack/files/`,
neither is synced into target repositories. `pack/github-labels.json` is
the canonical machine-readable catalog behind the `type:*` and `priority:*`
labels described in
[Issue guidance](pack/files/.agents/guidelines/issues.md), which target
repositories receive as the label convention itself, not this catalog file
or tool. Repository files can only describe the intended catalog; they
cannot prove what labels actually exist in a GitHub repository.
`scripts/sync-github-labels.py` reconciles the two for repo-seed's own
repository, or any repository a maintainer points it at, but is optional,
requires explicit invocation, and is never run as part of normal
`sync-docs.py` synchronization:

```bash
python scripts/sync-github-labels.py --check
python scripts/sync-github-labels.py --apply
```

It requires the [GitHub CLI](https://cli.github.com/) (`gh`), authenticated
against the target repository. `--check` reports missing or drifted
canonical labels and known legacy labels (`bug`, `enhancement`, `feature`,
`critical`, `high`, `medium`, `low`, `lowest`) without writing anything, and
exits non-zero when it finds drift. `--apply` creates missing canonical
labels and updates the description or color of existing ones; it never
deletes any label, including legacy ones that may still be attached to open
or historical issues.

## Profiles, Conventions, and Scaffolds

Three independent choices, not one:

```text
profile      = project shape (which core guidance and templates are available)
conventions  = languages/tools actually used (which are installed)
scaffolds    = optional project documents, created only when needed
```

### Profiles

| Profile | Reference templates available |
|---|---|
| `minimal` | README and changelog only |
| `library` | Minimal plus architecture and an on-demand TSD reference |
| `app` | Library plus FSD and user-guide templates |
| `game` | Library plus a GDD template |
| `full` | Complete reference catalog and every convention; for repo-seed testing/reference, not a project type |

All profiles receive the same core agent instructions, documentation, Git,
CI/CD, and issue guidance. A profile only changes which optional reference
templates are available; it says nothing about programming language and
never installs a language convention by itself.

The first sync requires an explicit project profile when no reusable profile
is recorded. Later syncs reuse a recorded `minimal`, `library`, `app`, or
`game` profile when `--profile` is omitted.

### Conventions

Language and tool guidance (`csharp`, `python`, `scripts`, `shell`, `unity`)
is selected independently of profile with `--conventions`, and persisted in
`.repo-seed-state.json` so later syncs reuse it when `--conventions` is
omitted:

```bash
python pack/files/scripts/sync-docs.py --target . --profile app --conventions csharp
python pack/files/scripts/sync-docs.py --target . --conventions csharp,unity
```

A fresh sync with no `--conventions` installs none. `full` always installs
every known convention, since it is a complete reference catalog. Changing
the selection prunes an unchanged, now-unselected convention file and
preserves one with local modifications, exactly like a profile change.

Examples:

```text
C# desktop application:  profile app,     conventions csharp
Unity game:              profile game,    conventions csharp,unity
small Python utility:    profile minimal, conventions python
```

An installation synced before conventions existed is migrated safely on its
first 4.2+ sync: repo-seed never deletes an already-installed convention
file outright, deriving an initial selection from what is already installed
plus strong repository evidence (see
[Document ownership](docs/project/document-ownership.md#migration-to-explicit-conventions)).

### Scaffolds

`README.md` and `CHANGELOG.md` are the baseline, created by
`--scaffold-project-files`. `architecture`, `fsd`, `gdd`, and `user-guide`
are on-demand: their templates are available under the applicable profile,
but repo-seed never creates them automatically. Create one explicitly when
the project needs it:

```bash
python pack/files/scripts/sync-docs.py --target . --scaffold architecture
python pack/files/scripts/sync-docs.py --target . --scaffold fsd --scaffold user-guide
```

`--scaffold` refuses to overwrite an existing document and reports its
destination; pass a name only available for the current profile (for
example, `gdd` requires `game` or `full`).

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
  --conventions csharp \
  --scaffold-project-files \
  --scaffold-github-templates \
  --dry-run
```

Review the output, then rerun without `--dry-run`.

Optional scaffolding is separated by ownership:

- `--scaffold-project-files` creates the missing baseline README/CHANGELOG, or upgrades verified unchanged Markdown;
- `--scaffold-github-templates` creates missing bug, feature, and chooser files, or upgrades verified unchanged Markdown;
- `--scaffold-editorconfig` creates `.editorconfig` only when missing;
- `--scaffold <name>` creates one on-demand document (`architecture`, `fsd`, `gdd`, `user-guide`) available for the selected profile; repeat the flag for more than one.

Existing project-owned files are preserved unless an eligible Markdown scaffold is
verified unchanged from repo-seed and can be upgraded safely.
On initial sync, version updates, and legacy migration, existing `.gitignore`,
`.editorconfig`, and pull-request templates are explicitly reported as protected
project-owned files.
The `.github/workflows/` tree is always project-owned and cannot be managed,
scaffolded, retired, or deleted by the pack.

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
  github-labels.json         # canonical hosted-label catalog
  files/                     # mirrors target repository paths
    AGENTS.md
    CLAUDE.md
    .agents/
    docs/templates/
    scripts/sync-docs.py
docs/project/                # live documentation about repo-seed
scripts/                     # repository tooling, including the optional
                              # sync-github-labels.py hosted-label tool
tests/                       # pack and tooling tests
```

Root files describe `repo-seed` itself and are never target sync sources.

## Build and Validate

```bash
python scripts/build-release-bundle.py
python -m unittest discover -s tests -v
python pack/files/scripts/sync-docs.py --help
python scripts/build-release-bundle.py --help
python scripts/sync-github-labels.py --help
python -m py_compile pack/files/scripts/sync-docs.py scripts/build-release-bundle.py scripts/sync-github-labels.py
git diff --check
```

The build creates `dist/repo-seed-pack-<version>.zip` from the inventory declared in `pack/manifest.json`.

## Project and Community

- [Document ownership](docs/project/document-ownership.md)
- [Issue guidance](pack/files/.agents/guidelines/issues.md)
- [Upgrading to Version 4](docs/project/upgrading-to-4.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Repo Seed is available under the [MIT License](LICENSE).
