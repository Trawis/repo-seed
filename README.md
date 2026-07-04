# repo-seed

Reusable coding-agent guidance and project-document templates with profile-based, conflict-aware synchronization.

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

**Pack version**: 2.0.0

## Ownership Model

| Location | Purpose | Target behavior |
|---|---|---|
| Root documents | Describe and govern repo-seed | Never synced |
| `pack/` | Managed agent, convention, editor, and PR sources | Updated by routine sync |
| `docs/templates/` | Managed read-only references and scaffold sources | Updated by routine sync |
| `docs/project/` | Live repo-seed documentation | Never synced |
| `pack-manifest.json` | Asset, profile, ownership, scaffold, and migration inventory | Drives sync and release bundles |

Repo-seed’s own root documents are never used as sync sources. Their distributed counterparts are explicit:

| Source | Target | Behavior |
|---|---|---|
| `pack/AGENTS.md` | `AGENTS.md` | Always managed and synchronized |
| `pack/CLAUDE.md` | `CLAUDE.md` | Always managed and synchronized |
| `docs/templates/readme.template.md` | `README.md` | Scaffold only when missing |
| `docs/templates/changelog.template.md` | `CHANGELOG.md` | Scaffold only when missing |
| `docs/templates/gitignore.template` | `.gitignore` | Scaffold only when missing |

In target repositories, `README.md`, `CHANGELOG.md`, `.gitignore`, `.agents/project.md`, and `docs/project/` are project-owned. Managed root `AGENTS.md` contains the essential rules directly and routes specialized work to `.agents/guidelines/` and `.agents/conventions/`.

`pack-manifest.json` belongs to repo-seed and extracted release bundles; it describes source assets. It is not copied into the target as a project file. The sync script instead writes `.agent-guidelines-manifest.json` in the target to track the profile, version, and managed-file hashes required for safe future updates.

See [`docs/project/document-ownership.md`](docs/project/document-ownership.md) for the complete lifecycle.

## Profiles

| Profile | Managed guidance | Project templates |
|---|---|---|
| `minimal` | Core agent, Git, and documentation guidance | README, changelog, and gitignore |
| `library` | Minimal + CI/CD and general coding conventions | README, changelog, and gitignore |
| `app` | Library guidance | Core docs + features, architecture, user guide, FSD, TSD |
| `game` | Library + Unity conventions | Core docs + features and GDD |
| `full` | All managed guidance | Every project template |

Generic GitHub bug and feature templates are available through a separate explicit scaffold option.

## Sync

Preview routine managed-file changes:

```bash
python /path/to/repo-seed/scripts/sync-agent-guidelines.py \
  --source /path/to/repo-seed \
  --target /path/to/target-repo \
  --profile app \
  --dry-run
```

Apply managed updates:

```bash
python /path/to/repo-seed/scripts/sync-agent-guidelines.py \
  --source /path/to/repo-seed \
  --target /path/to/target-repo \
  --profile app
```

Create missing project-owned files:

```bash
python /path/to/repo-seed/scripts/sync-agent-guidelines.py \
  --source /path/to/repo-seed \
  --target /path/to/target-repo \
  --profile app \
  --scaffold-project-files
```

Use `--scaffold-github-templates` to create missing generic issue templates. Scaffolding never overwrites existing files. The former `--include-project-docs` option remains as a deprecated alias for one transition release.

Routine sync:

- updates managed files only when their recorded hash proves they were untouched;
- writes incoming conflicts under `.agent-guidelines-conflicts/`;
- removes obsolete managed files only when they remain unmodified;
- protects root project documents and unknown files;
- updates reference templates without rewriting live project documents;
- reports template-review warnings without failing.

When branch creation is enabled, the sync script bases work on an existing `develop` or `dev` branch first and falls back to `main` or `master` only when no integration branch exists. `--base-branch` remains available as an explicit override.

## Release Bundles

Build all self-contained profile archives:

```bash
python scripts/build-release-bundles.py
```

Each archive contains a profile-filtered manifest, its required sources, templates, and the sync script.

## Validation

```bash
python -m unittest discover -s tests -v
python scripts/sync-agent-guidelines.py --help
python scripts/build-release-bundles.py --help
python -m py_compile scripts/sync-agent-guidelines.py scripts/build-release-bundles.py
git diff --check
```

## Project Documents

- [`CHANGELOG.md`](CHANGELOG.md) — release history
- [`docs/project/features.md`](docs/project/features.md) — implemented and planned capabilities
- [`docs/project/document-ownership.md`](docs/project/document-ownership.md) — file ownership and sync lifecycle

## License

No license has been declared yet.
