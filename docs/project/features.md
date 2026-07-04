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

- Optional provider-specific CI/CD examples after concrete project needs are known.
- Additional profile-specific conventions when real repositories demonstrate the need.

## Maybe Later

- A dedicated template-review acknowledgement command if manual provenance updates prove error-prone.

## Rejected / Out of Scope

- Routine synchronization of project-owned documentation.
- Automatic merging of template changes into live project documentation.
- Automatic commits, pushes, pull requests, or merges.
