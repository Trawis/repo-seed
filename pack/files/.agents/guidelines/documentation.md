# Documentation Guidance

**Document role**: Managed coding-agent guidance

**Sync destination**: `.agents/guidelines/documentation.md`

## Document Authority

- `README.md` and `CHANGELOG.md` are project-owned root entry points.
- `docs/project/` contains authoritative live project documentation.
- `docs/templates/` contains managed reference templates, not project requirements.
- Never edit files under `docs/templates/` in a target repository.
- Never copy placeholders or unverified claims into live documentation.

## When to Update Live Documentation

Update the relevant project-owned document when a task changes:

- setup, build, test, run, configuration, CLI usage, or public behavior: `README.md`;
- meaningful user-facing or developer-facing behavior: `CHANGELOG.md`;
- implemented, planned, or rejected capabilities: `docs/project/features.md`;
- components, boundaries, dependencies, integrations, or data flow: `docs/project/architecture.md`;
- visible workflows, navigation, settings, or troubleshooting: `docs/project/user-guide.md`;
- documented functional, technical, or game requirements: the applicable FSD, TSD, or GDD under `docs/project/`.

Keep documentation changes scoped to verified behavior. Do not create documents as busywork.

## Template Changes

Scaffolded documents contain a hidden template ID and content hash. When sync reports a newer template:

1. Compare the managed template with the live document.
2. Apply only relevant structural improvements.
3. Preserve verified project content and intentional differences.
4. Update the provenance hash only after completing the review.

A template warning does not by itself authorize rewriting a project-owned document.

## Style

- Prefer concise, factual sections and working examples.
- Link from the README to detailed documents instead of duplicating them.
- Keep changelog entries curated; do not dump commit history.
- Mark unknown information as unknown or omit it.
- Preserve the repository's existing punctuation and formatting style.
