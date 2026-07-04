# Document Ownership

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

## Ownership Classes

| Class | Source | Target | Lifecycle |
|---|---|---|---|
| Repo-seed-only | Root and `docs/project/` | None | Maintained only for this repository |
| Managed guidance/config | `pack/` or listed tool source | Manifest target | Hash-protected routine updates |
| Managed template | `docs/templates/*.template.md` | `docs/templates/` | Read-only reference updated by sync |
| Project-owned scaffold | Managed template body | Root exception or `docs/project/` | Created only when missing |
| Unmapped file | None | Existing target path | Never touched |

`pack-manifest.json` is the authoritative inventory. Root repo-seed documents are never sync sources.

## Target Layout

```text
README.md
CHANGELOG.md
AGENTS.md
CLAUDE.md
.agents/
  project.md              # optional and project-owned
  guidelines/             # managed
  conventions/            # managed
docs/
  project/                # live and authoritative
  templates/              # managed and read-only
```

Root `AGENTS.md` contains essential rules directly. It requires agents to read optional `.agents/project.md`, applicable child `AGENTS.md` files, and relevant live requirements.

## Root File Matrix

| Path | Owner | Routine sync |
|---|---|---|
| `AGENTS.md` | Managed pack | Update if untouched; conflict if locally edited |
| `CLAUDE.md` | Managed pack | Update if untouched; conflict if locally edited |
| `.agent-guidelines-version` | Managed pack | Update if untouched |
| `.editorconfig` | Managed pack | Update if untouched; conflict if locally edited |
| `.github/pull_request_template.md` | Managed pack | Update if untouched; conflict if locally edited |
| `scripts/sync-agent-guidelines.py` | Managed pack | Update if untouched; conflict if locally edited |
| `README.md` | Target project | Create only when missing and explicitly scaffolded |
| `CHANGELOG.md` | Target project | Create only when missing and explicitly scaffolded |
| `.agents/project.md` | Target project | Never created, updated, or removed |
| Any unmapped file | Target project | Untouched |

## Template Rules

- Template filenames end in `.template.md`.
- Visible template metadata states the role and scaffold destination.
- Sync copies the labeled template into target `docs/templates/`.
- Agents must not edit target templates.
- Scaffolding removes template-only metadata and adds a hidden asset ID and content hash.
- Existing scaffold destinations are always preserved.
- When a template hash changes, sync prints a review warning and exits successfully.
- Agents update live documents only when relevant to their task; they acknowledge a completed review by updating the hidden provenance hash.

## Migration and Profile Changes

Sync creates new managed targets before cleanup.

- Obsolete files are removed only when their current hash matches the previous managed hash.
- Locally modified obsolete files are preserved and reported.
- Legacy README, CHANGELOG, FEATURES, ROADMAP, and unknown files are never pruned.
- Reducing a profile uses the same hash-safe cleanup.
- Invalid manifests, unsafe paths, missing sources, template errors, and managed conflicts fail the operation.

## Source Maintenance

Repo-seed maintainers may edit sources under `pack/` and `docs/templates/` when the task explicitly changes the distributed pack. Target repositories place local agent rules in `.agents/project.md` or a child `AGENTS.md`, never in managed files.
