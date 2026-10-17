# Repo Seed Pack

Package-only instructions for the downloadable pack. This file, `LICENSE`, `github-labels.json`, and `skill-sources.json` are in the archive but never synced into targets.

## First Sync

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --conventions csharp \
  --dry-run
```

Choose `minimal`, `library`, `app`, or `game`. Use `--conventions` for the
languages and tools you use (`csharp`, `python`, `scripts`, `shell`, `unity`).
A fresh sync installs none by default.

Every profile installs Codex and Claude Code skills for code review, bug fixing,
refactoring, dependency upgrades, issues, TDD, code simplification, repository
audit, bootstrap, and upgrade. `library`, `app`, and `game` also install
technical-design, documentation-bootstrap, and architecture-review. Git, CI/CD,
documentation, and language rules stay in `.agents/` guidance.

Add only the scaffolding you need:

```text
--scaffold-project-files          # baseline README/CHANGELOG
--scaffold-github-templates       # bug/feature/tech-debt/chore Issue Forms, PR template
--scaffold-workflows              # two optional workflows (drift issue, sync pull request), only when missing
--scaffold-editorconfig           # .editorconfig
--scaffold <name>                 # one on-demand document: architecture, fsd, gdd, user-guide
```

Review the dry run, commit or back up the target, then rerun without
`--dry-run`. Managed guidance updates only when different. Modified or
unverified project files are kept.

The `.github/workflows/` tree is always project-owned and never managed.
`--scaffold-workflows` can create two caller files there, each once and only
when missing: `repo-seed-audit.yml` (weekly; opens or closes a drift issue; needs
`issues: write`) and `repo-seed-sync.yml` (weekly; opens or updates a pull
request with the changes; needs `contents: write` and `pull-requests: write`).
Both are request-only; delete a file to turn it off.

Commit the generated `.repo-seed-state.json`. It lets a smaller profile or a
changed convention selection remove unchanged stale files and keep modified ones
as tombstones for review.

## Update an Existing Project

Use the script from the newly extracted pack, so the newest validation runs
first:

```bash
python /path/to/extracted/pack/files/scripts/sync-docs.py \
  --target . \
  --dry-run
```

The recorded profile and conventions are reused when `--profile` and
`--conventions` are omitted. Pass `--conventions ""` to clear the recorded
conventions. `--audit` reports drift without writing and exits 0 even when it
finds some, so read its output rather than its exit code. The copied target script cannot cross
manifest-schema changes and may lack newer fixes.

## Upgrading a Pre-5.0 Target

A pre-5.0 `.repo-seed-state.json` is no longer converted. Run the
[5.13.2 pack](https://github.com/Trawis/repo-seed/releases/tag/v5.13.2) once
with `--conventions <list>`, then use a current pack.

Full documentation: [repo-seed on GitHub](https://github.com/Trawis/repo-seed).

## License

MIT. See `LICENSE`.
