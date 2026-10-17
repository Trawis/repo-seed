# Upstream-Derived Skills

**Document role**: `repo-seed` project documentation

**Sync behavior**: Never copied into target repositories

This document defines how repo-seed adopts workflows from external skill
repositories. Upstream skills are source material, not runtime dependencies:
the distributed pack is self-contained and target synchronization never
contacts an upstream repository.

## Principles

- Prefer adapting a proven workflow over copying it, and distribute only the
  files the skill needs. Do not import plugin wrappers, hooks, telemetry,
  installer configuration, or unrelated skills.
- repo-seed's permission, ownership, synchronization, and portability rules
  stay authoritative. A derived skill must defer to the applicable
  `AGENTS.md` and must not grant itself automatic commit, push, pull request,
  or issue-write permission.
- The pack ships each skill once, under `.agents/skills/`. `sync-docs.py`
  installs the same bytes under `.claude/skills/` in targets, so both surfaces
  are identical there. Edit only `.agents/skills/`.
- Updates are deliberate maintainer actions. Nothing is refreshed from
  upstream during target sync.

## Provenance Registry

`pack/skill-sources.json` records every upstream-derived skill. It ships in
the release archive as a package file for traceability and is not synced into
target repositories. Each entry requires:

| Field | Meaning |
|---|---|
| `name` | Skill directory name under both skill surfaces |
| `upstream_repository` | `https://` URL of the upstream repository |
| `source_path` | Path of the skill in the upstream repository |
| `source_revision` | Full 40-character commit SHA used for the adaptation |
| `license` | SPDX identifier of the license that covers this skill |
| `license_evidence` | Upstream path proving that license applies to this skill |
| `adaptation` | `copied` or `adapted` |
| `reviewed` | Date of the last maintainer review (`YYYY-MM-DD`) |
| `security_review` | What was reviewed in every distributed file and the result |
| `distributed_files` | Every file shipped for the skill, relative to its directory |
| `security_reviewed_files` | Required for any non-Markdown file; each is also in `distributed_files` |

Tags and branches are not accepted as revisions; they can move.

## Licensing

Accepted licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD,
CC0-1.0, and Unlicense. A source with no license, an unclear or per-skill
license that does not cover the skill, a copyleft license, or terms that
restrict redistribution is rejected, not copied. Do not assume a
repository-wide license covers a skill when the project licenses skills
individually; record the file that proves the license in `license_evidence`.

Every derived skill ships a `NOTICE.md` in both surfaces. It states the
upstream repository, source revision, and license, and carries any copyright
or notice text the license requires. Because `NOTICE.md` is a managed skill
file, it reaches targets through the normal manifest.

## Security Review

Review every file before distribution. Reject, rather than adapt around,
hidden network calls, credential access, arbitrary remote execution,
telemetry, or destructive behavior. Hook, plugin, marketplace, MCP, and
settings files are never distributed. Scripts and other non-Markdown
resources are allowed only after explicit review and are listed in
`security_reviewed_files`.

## Adding a Derived Skill

1. Pin the upstream commit and read the complete skill and its supporting
   files, not only its README.
2. Confirm the license covers the skill. Stop if it does not.
3. Adapt the skill to repo-seed rules, removing automatic commit, push, PR, or
   issue behavior and any tool-specific framework dependence.
4. Add the skill to both surfaces, add every file to `pack/manifest.json` as a
   managed asset, and add `NOTICE.md`.
5. Add the registry entry in `pack/skill-sources.json`.
6. Run the validation below.

## Updating a Derived Skill

1. Compare the recorded `source_revision` with the new upstream revision and
   review the diff, including every added or changed supporting file.
2. Re-confirm the license for the new revision.
3. Apply only the changes that fit repo-seed, and keep both surfaces identical.
4. Update `source_revision`, `reviewed`, `security_review`, and `NOTICE.md`.
5. Re-run validation.

## Validation

```bash
python scripts/validate-skill-sources.py
python -m unittest discover -s tests -v
```

`validate-skill-sources.py` reads local files only. It fails when a derived
skill lacks provenance, has an unpinned revision or disallowed license, ships
files that differ from `distributed_files`, includes hooks or unreviewed
non-Markdown files, contains a network fetch command, omits the `NOTICE.md`
details, or differs between skill surfaces. A skill that ships `NOTICE.md`
without a registry entry also fails.

The checks are deterministic guards. They do not replace the maintainer
review of what an upstream skill instructs the agent to do.
