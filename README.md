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

In target repositories, `README.md`, `CHANGELOG.md`, `.agents/project.md`, and `docs/project/` are project-owned. Managed root `AGENTS.md` contains the essential rules directly and routes specialized work to `.agents/guidelines/` and `.agents/conventions/`.

See [`docs/project/document-ownership.md`](docs/project/document-ownership.md) for the complete lifecycle.

## Profiles

| Profile | Managed guidance | Project templates |
|---|---|---|
| `minimal` | Core agent, Git, and documentation guidance | README and changelog |
| `library` | Minimal + CI/CD and general coding conventions | README and changelog |
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
