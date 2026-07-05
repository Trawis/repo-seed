# Features

**Document role**: Repo-seed project documentation

**Sync behavior**: Never copied into target repositories

## Implemented

- Self-contained `pack/` distribution with target-mirroring paths.
- One manifest shared by synchronization and release packaging.
- One universal archive containing every profile.
- Five documentation profiles: `minimal`, `library`, `app`, `game`, and `full`.
- Managed coding-agent entry files, focused guidelines, and language conventions.
- Unconditional refresh of managed files and read-only template references.
- Missing-only scaffolding for project documents, `.gitignore`, and `.editorconfig`.
- Separate missing-only scaffolding for GitHub bug, feature, and configuration templates.
- Source-path markers in scaffolded Markdown for manual template comparison.
- Dry-run support and strict manifest, source, and path validation.

## Deliberately Not Supported

- Hash or provenance state.
- Conflict copies, backups, or local-edit protection for managed files.
- Automatic merging of template changes into live project documentation.
- Migration cleanup or deletion when profiles change.
- Git branch creation, commits, pushes, pull requests, or merges.
- Profile-specific release archives.

## Possible Future Work

Add capabilities only after concrete target-repository usage demonstrates a recurring need. Prefer extending templates or guidance over adding synchronization state.
