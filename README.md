# Repo Seed

Reusable coding-agent guidance and project-document templates with a small sync tool.

**Document role**: Repository-only overview

**Sync behavior**: Never copied into target repositories

## What It Provides

- portable `AGENTS.md` guidance with a `CLAUDE.md` wrapper;
- Codex and Claude Code skills for code review, bug fixing, refactoring,
  dependency upgrades, issues, TDD, code simplification, architecture review,
  repository audit, bootstrap and upgrade, technical design, and documentation
  bootstrap;
- documentation, Git, CI/CD, and issue guidance, separate from language
  conventions;
- a shared label catalog, with an optional tool to sync hosted GitHub labels;
- read-only templates for four project profiles, plus scaffolds for project
  documents, issue forms, and a pull request template;
- one release archive, and a sync script with a read-only `--audit` report.

## Requirements

- Python 3.11 or newer;
- a writable target repository;
- Windows, Linux, or macOS.

The scripts use only the Python standard library. CI runs Python 3.14 on Linux
and Windows only. Older Python versions and macOS are not tested.

## Safety

Selected managed files are repo-seed-owned and are updated to the current pack
content whenever they differ. Do not customize them in target repositories;
local changes are overwritten on the next sync.

Project-owned scaffolds are created only when missing. They are preserved unless
their provenance proves they are unchanged and safe to upgrade.

When a profile or convention change unselects a managed file, repo-seed removes
it only if it still matches the recorded hash. A modified file is kept and
tombstoned for review.

Run `--dry-run` first and commit or back up the target. The dry run marks a
managed overwrite that would discard local edits with `and discard local
changes`, and one with no recorded baseline (for example on a first sync over an
existing file) with `no recorded baseline`. Add `--diff` to also print, for each
file with local edits, a diff from the pack's version to the local file: `+`
lines exist only locally and would be lost. `--diff` writes nothing, and a normal
sync still overwrites managed files. Writes are not transactional. Each target keeps `.repo-seed-state.json` as committed ownership
metadata.

See [Document ownership](docs/project/document-ownership.md) for path
ownership.

## Hosted GitHub Labels

`pack/github-labels.json` and `scripts/sync-github-labels.py` are maintainer
tools. They are not synced into targets. The catalog defines the `type:*` and
`priority:*` labels described in
[Issue guidance](pack/files/.agents/guidelines/issues.md).

The tool is optional and never runs during `sync-docs.py`. It needs the
[GitHub CLI](https://cli.github.com/) (`gh`), authenticated for the repository:

```bash
python scripts/sync-github-labels.py --check
python scripts/sync-github-labels.py --apply
```

`--check` reports missing or drifted labels and legacy labels (`bug`,
`enhancement`, `feature`, `critical`, `high`, `medium`, `low`, `lowest`,
`type: decision`, `type: idea`), and exits non-zero on drift. `--apply` creates missing labels and updates
descriptions and colors. It never deletes labels.

## Profiles, Conventions, and Scaffolds

Three independent choices:

```text
profile      = project shape (which templates are available)
conventions  = languages and tools used (which are installed)
scaffolds    = optional project documents, created only when needed
```

### Profiles

| Profile | Reference templates available |
|---|---|
| `minimal` | README and changelog only |
| `library` | Minimal plus architecture and an on-demand TSD reference |
| `app` | Library plus FSD and user-guide templates |
| `game` | Library plus a GDD template |

All profiles get the same agent instructions, guidance, and core skills (code
review, bug fixing, refactoring, dependency upgrades, issues, TDD, code
simplification, repository audit, bootstrap, and upgrade). `library`, `app`, and
`game` also get technical-design, documentation-bootstrap, and
architecture-review. A profile never installs a language convention.

The first sync needs `--profile`. Later syncs reuse the recorded profile.

### Conventions

Pick `csharp`, `python`, `scripts`, `shell`, or `unity` with `--conventions`.
The choice is saved in `.repo-seed-state.json`:

```bash
python pack/files/scripts/sync-docs.py --target . --profile app --conventions csharp
python pack/files/scripts/sync-docs.py --target . --conventions csharp,unity
```

A fresh sync with no `--conventions` installs none. Changing the selection
removes unchanged unselected files and keeps modified ones.

```text
C# desktop application:  profile app,     conventions csharp
Unity game:              profile game,    conventions csharp,unity
small Python utility:    profile minimal, conventions python
```

A pre-5.0 state file is no longer converted. Sync once with the 5.13.2 pack
and `--conventions <list>`, then use a current pack. See
[Upgrading to Version 5](docs/project/upgrading-to-5.md).

### Scaffolds

`--scaffold-project-files` creates the baseline `README.md` and `CHANGELOG.md`.
`architecture`, `fsd`, `gdd`, and `user-guide` are created only on request:

```bash
python pack/files/scripts/sync-docs.py --target . --scaffold architecture
python pack/files/scripts/sync-docs.py --target . --scaffold fsd --scaffold user-guide
```

`--scaffold` never overwrites a document. The name must be available for the
profile (`gdd` needs `game`).

Each document has one job:

- FSD or GDD: accepted product or gameplay behavior;
- architecture: the verified current technical system;
- TSD under `docs/project/designs/`: one substantial change;
- user guide: current user workflows.

Top-level documents become short indexes as detail documents are added.

## Adopting into an Existing Project

A first sync overwrites managed files, including `AGENTS.md` and `CLAUDE.md`,
even when a copy already exists. Before the first real run:

1. Commit or back up the target.
2. Move your own rules from an existing `AGENTS.md` or `CLAUDE.md` into
   `.agents/project.md`, which stays project-owned.
3. Run with `--dry-run --diff` and read what would be lost. A file with no
   recorded baseline is flagged `no recorded baseline`, and the run ends with a
   `NOTE:` line when any managed file would be overwritten that way.

`--target` defaults to the current directory.

| Term | Meaning |
|---|---|
| Managed file | Owned by the pack; overwritten whenever it differs. |
| Template | Read-only reference under `docs/templates/`. |
| Scaffold | A project file created once from a template, then project-owned. |
| Baseline | The hash recorded in `.repo-seed-state.json` when a file was last synced. |
| Tombstone | A record of an unselected file that was kept because it was modified. |
| Drift | A target that differs from what the pack and recorded state expect (`--audit`). |

## Download and First Sync

Download the latest ZIP from
[GitHub Releases](https://github.com/Trawis/repo-seed/releases), extract it, and
preview the sync:

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

Optional scaffolding:

- `--scaffold-project-files`: missing README and CHANGELOG, or verified unchanged Markdown upgrades;
- `--scaffold-github-templates`: missing Issue Forms, chooser config, and `.github/pull_request_template.md`; existing files, including legacy `.md` templates, are kept;
- `--scaffold-workflows`: the optional drift-check and sync workflows `.github/workflows/repo-seed-audit.yml` and `.github/workflows/repo-seed-sync.yml`, each only when missing (see Automatic Drift Check and Automatic Sync Pull Request);
- `--scaffold-editorconfig`: `.editorconfig`, only when missing;
- `--scaffold <name>`: one on-demand document; repeat for more.

Existing project-owned files are kept unless an eligible Markdown scaffold is
verified unchanged and can be upgraded safely. `.gitignore` is entirely
project-owned and never touched. `.editorconfig` is project-owned too, but
may be created once as a missing-only scaffold. The `.github/workflows/` tree is
always project-owned and never managed. The only files the pack can create there
are the optional drift check and sync callers (`--scaffold-workflows`), once each, and only when missing.

## Update an Existing Project

Use the script from the newly extracted pack, so the newest validation runs
first:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --dry-run
```

The copied `scripts/sync-docs.py` cannot cross manifest-schema changes and may
lack newer fixes. Pass `--profile` to change the profile.

## Automatic Drift Check

Optional. A target repository can find out on its own when a newer pack is
released or its managed files drift, instead of waiting for someone to run the
script. Add a workflow that calls the reusable audit workflow in this
repository. Either run `sync-docs.py --scaffold-workflows`, which creates the
file below once, pinned to the pack release that created it, and never changes
an existing file, or write it yourself:

```yaml
name: repo-seed audit
on:
  schedule:
    - cron: "17 6 * * 1"
  workflow_dispatch:
jobs:
  audit:
    permissions:
      contents: read
      issues: write
    uses: Trawis/repo-seed/.github/workflows/audit.yml@vX.Y.Z   # a release tag, such as the one the scaffold uses
```

Pin `@` to a release tag. Dependabot can keep it current, but only if the repository has its own
`.github/dependabot.yml` with a `github-actions` entry; the pack does not create one. Each run downloads the
latest release, checks its SHA-256, and runs `sync-docs.py --audit` against the
repository. While the audit reports drift, exactly one open issue titled
`repo-seed: managed files are out of date` carries the audit output, and it
closes itself once the audit is clean. The job fails only when the tooling
itself fails, such as a checksum mismatch, not when drift is found. It needs
`issues: write` and network access to GitHub. It changes no file; apply updates
with the steps above.

**What you are trusting.** The pinned tag fixes only the workflow file. The
script it runs is always the latest release of this repository, and the
checksum comes from that same release, so it detects a corrupted download, not
a compromised publisher. The script runs without the job token (checkout does
not persist it, and only the two `gh` steps receive it), so it cannot use it to
write. Pin to a commit or fork the workflow if you need a stricter guarantee. A
repository without `.repo-seed-state.json`, or with issues disabled, is skipped
with a notice instead of failing.

## Automatic Sync Pull Request

Optional. Instead of running the script by hand, a target repository can let a
workflow open the update. `sync-docs.py --scaffold-workflows` creates
`.github/workflows/repo-seed-sync.yml` once, pinned to the pack release that
created it, and never changes an existing file. Delete the file to turn the
sync off. It calls the reusable sync workflow in this repository:

```yaml
name: repo-seed sync
on:
  schedule:
    - cron: "43 6 * * 1"
  workflow_dispatch:
jobs:
  sync:
    permissions:
      contents: write
      pull-requests: write
    uses: Trawis/repo-seed/.github/workflows/sync.yml@vX.Y.Z   # a release tag
    # with:
    #   pack-version: "X.Y.Z"             # pin the pack instead of using the latest
    # secrets:
    #   token: ${{ secrets.REPO_SEED_TOKEN }}
```

Each run downloads the latest release (or the pinned one), checks its SHA-256,
and runs `sync-docs.py` with the recorded profile and conventions and no
`--scaffold-*` flag, so project-owned files are never touched. When managed
files differ, it force-pushes the branch `chore/repo-seed-sync` and opens or
updates one pull request that lists the dry-run output and flags any overwrite
with no recorded baseline. When the files already match, it closes that pull
request. It skips repositories without `.repo-seed-state.json` and runs from the
default branch only.

Setup the repository needs:

- Settings, Actions, General: allow GitHub Actions to create and approve pull
  requests.
- A pull request opened with the default token does not start other workflows,
  so required checks do not run on it. To run them, store a personal access
  token or GitHub App token as a secret and pass it as `secrets.token`.

The same trust model as the drift check applies: the script that runs comes from
the release, and the checksum detects corruption, not a compromised publisher.
The script runs in steps that do not hold the write token. Pin `pack-version`
to control which release is applied. Review the pull request before merging.

## Upgrading a Pre-5.0 Target

Version 5 resets compatibility:

- **Manifest**: `schema_version: 3` is incompatible with older scripts. Pre-4.x
  migration is removed. A target with no `.repo-seed-state.json` is a fresh
  install.
- **State**: schema 1 (before explicit conventions) converts to schema 2 only
  with the [5.13.2 pack](https://github.com/Trawis/repo-seed/releases/tag/v5.13.2)
  and one `--conventions <list>` sync. Later packs refuse it.

See [Upgrading to Version 5](docs/project/upgrading-to-5.md).

## Source Layout

```text
pack/
  manifest.json              # sole distributed-asset inventory
  README.md                  # package-only quick start
  LICENSE                    # package-only license
  github-labels.json         # hosted-label catalog
  skill-sources.json         # provenance of upstream-derived skills
  files/                     # mirrors target repository paths
    AGENTS.md
    CLAUDE.md
    .agents/
      guidelines/
      conventions/
      skills/                # Codex skills
    .claude/
      skills/                # Claude Code skills
    docs/templates/
    scripts/sync-docs.py
docs/project/                # documentation about repo-seed
scripts/                     # tooling: release build, label sync, skill provenance
                             # check, skill mirror, changelog-to-release-notes
tests/                       # pack and tooling tests
.github/                     # this repository's CI, release, and reusable audit workflows
.claude/settings.json        # turns the distributed skill wrappers off for repo-seed itself
CHANGELOG.md                 # release history; the top entry is the release notes
```

Skills hold repeatable workflows. Policy and language rules stay in
`.agents/guidelines/` and `.agents/conventions/`. Root files describe
`repo-seed` itself and are never sync sources.

## Build and Validate

```bash
python scripts/build-release-bundle.py
```

The full validation list is in [`AGENTS.md`](AGENTS.md#repository-validation). CI runs the same commands.

The build writes `dist/repo-seed-pack-<version>.zip` from `pack/manifest.json`.

## Project and Community

- [Document ownership](docs/project/document-ownership.md)
- [Upstream-derived skills](docs/project/upstream-skills.md)
- [Skill audit](docs/project/skill-audit.md)
- [Issue guidance](pack/files/.agents/guidelines/issues.md)
- [Upgrading to Version 5](docs/project/upgrading-to-5.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Repo Seed is available under the [MIT License](LICENSE).
