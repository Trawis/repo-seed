# Document Ownership

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

## Ownership Model

| Class | Pack location | Target behavior |
|---|---|---|
| Repository-only | Root and `docs/project/` | Describes repo-seed; never distributed |
| Managed | `pack/files/` | Always overwritten during sync |
| Managed template | `pack/files/docs/templates/` | Always overwritten as a read-only reference |
| Project-owned scaffold | Rendered from a managed template | Created only when missing |
| Unmapped | None | Never touched |

`pack/manifest.json` is the sole inventory used by sync and release packaging. Paths under `pack/files/` mirror their managed target paths.

## Target Layout

```text
AGENTS.md                    # managed
CLAUDE.md                    # managed
.agents/
  project.md                 # optional, project-owned
  guidelines/                # managed
  conventions/               # managed
scripts/sync-docs.py         # managed
docs/
  templates/                 # managed, read-only references
  project/                   # project-owned, authoritative documentation
README.md                    # project-owned root exception
CHANGELOG.md                 # project-owned root exception
```

The root `AGENTS.md` requires agents to read optional `.agents/project.md`, applicable child `AGENTS.md` files, and relevant live documentation.

## Synchronization Rules

- Managed files and selected reference templates are copied unconditionally.
- Project files, `.gitignore`, and `.editorconfig` are scaffolded only when requested and missing.
- GitHub bug, feature, and configuration templates are scaffolded separately and only when missing.
- Existing project-owned destinations, unknown files, and files outside the selected profile are untouched.
- Sync never deletes files, creates conflicts or backups, tracks hashes, writes state, or performs Git operations.
- A missing source, invalid manifest, unsafe path, or copy failure stops the operation.

Scaffolded Markdown includes a source-path comment. When work affects documented behavior, agents compare the live document with its current template and update the live document when practical. They never edit target templates to describe one project.

## Source Maintenance

Repo-seed maintainers update distributed assets only under `pack/files/` and register every asset in `pack/manifest.json`. Root documents remain repository-only even when a similarly named distributed file exists.
