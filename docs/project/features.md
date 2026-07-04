# Features

**Document role**: `repo-seed` repository documentation

**Sync behavior**: Never copied into target repositories

## Implemented

- Explicit separation between repo-only files, managed pack files, reusable templates, and target-owned project documents.
- Concise root agent instructions with task-specific guidance and convention routing.
- Managed coding-agent references under `.agents/` in target repositories.
- Clearly labeled, routinely synced reference templates under `docs/templates/`, with stable scaffold destinations under `docs/project/`.
- Profile-based sync through `minimal`, `library`, `app`, `game`, and `full`.
- Declarative `pack-manifest.json` shared by sync and release tooling.
- Hash-based managed-file conflict detection.
- Hash-safe migration and profile cleanup.
- One-time project-document scaffolding that preserves existing target documents.
- Template provenance and non-failing drift warnings.
- Optional generic GitHub issue-template scaffolding.
- C#, Unity, Python, shell, script, and CI/CD guidance.
- Pull-request and coding-agent entry-file support.
- Profile-specific release archives.

## Planned

- No additional features are planned during 2.0 stabilization.

## Maybe Later

- Non-mutating synchronization check mode.
- JSON Schema validation for `pack-manifest.json`.
- Release archive checksums.
- A project-specific agent-instructions template.
- Additional profiles and convention families.
- Splitting conventions when real target repositories show context problems.
- A dedicated template-review acknowledgement command if manual provenance updates prove error-prone.
- Separating Git branch preparation from file synchronization.
- Reconsidering whether `.editorconfig` should be managed or scaffolded.
- Provider-specific CI/CD examples after concrete project needs are known.

## Rejected / Out of Scope

- Routine synchronization of project-owned documentation.
- Automatic merging of template changes into live project documentation.
- Automatic commits, pushes, pull requests, or merges.
- A separate roadmap that duplicates feature state.
