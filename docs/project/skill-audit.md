# Skill Audit

**Document role**: `repo-seed` project documentation

**Sync behavior**: Never copied into target repositories

Record of the keep/adapt decision for each distributed skill, made by reading
the full upstream skills at the pinned revisions below. Both upstreams are
MIT-licensed. Skills marked "ideas only" restate adopted ideas in repo-seed's
own words and copy no text, so they need no `pack/skill-sources.json` entry
(see [Upstream-derived skills](upstream-skills.md)).

| Upstream | Revision inspected |
|---|---|
| `mattpocock/skills` | `49dd158d1076134a641b33efb035946536778336` |
| `obra/superpowers` | `bb92a77741419a4ab5f06e711a283343f1ada0c3` |
| `github/spec-kit` | `f6e72bc8523de8ec8368129cbdea78d45f27cef8` |
| `addyosmani/agent-skills` | `aeac41d4d005999432bb7312f7ff06383a91d59d` |

Upstream issue trackers were not checked (the GitHub API returned 403), so known
upstream defects were not reviewed.

## Decisions

| Skill | Decision | Adopted | Not adopted |
|---|---|---|---|
| `bug-fix` | Adapt, ideas only | Reliable reproduction, falsifiable hypotheses, one variable at a time, greppable debug markers, real-seam regression test, stop after repeated failures, secret redaction | Shell script template, mandatory phase gates, `superpowers:` namespace, automatic commits and PRs |
| `code-review` | Adapt, ideas only | Merge-base pinning, cited rules, smells as judgement calls, standards findings kept separate; later, acceptance review against the originating spec, omitted and unrequested work, regression-test evidence | Parallel sub-agents, full smell catalog, issue-tracker fetch, severity labels, posting review actions |
| `refactor` | Keep | None | The inspected upstreams do architecture discovery, not behavior-preserving edits |
| `dependency-upgrade` | Keep | None | No upstream equivalent was found in the two inspected repositories |
| `technical-design` | Keep | None | Upstreams publish to issue trackers or write plans under their own paths |
| `documentation-bootstrap` | Keep | None | `domain-modeling` is interactive and does not replace evidence-only documentation |
| `issue-authoring` | New, ideas only (`triage`) | Concept-level duplicate search, claim verification, durable acceptance criteria, prior-rejection check | Tracker state machine, role labels, `.out-of-scope/` writes, automatic hosted writes |
| `issue-implementation` | New, ideas only (`implement`, `implement-spec`) | State the ticket first, narrow checks while working, full suite at the end, review the finished work | Integration branches, worktrees, sub-agents, automatic commits, draft PRs, ticket closing |
| `test-driven-development` | New, derived (`tdd`, with Superpowers' `test-driven-development`) | Named seams, vertical slices, behavior over implementation, mocks only at boundaries, verified red failure, refactor only when green, mutation check | Iron law, rationalization tables, TDD for every change, extra `tests.md` and `mocking.md` |
| `code-simplification` | New, derived (`addyosmani/agent-skills`) | Behavior-preservation test, project conventions, clarity over cleverness, one change at a time, modified tests signal a behavior change | `simplify-ignore` hook, slash commands, plugin manifest, evals, language examples, per-change commits |
| `architecture-review` | New, derived (`improve-codebase-architecture`, with `codebase-design`) | Scoping, reading existing decisions first, friction questions, deletion test, seam discipline, ranking by strength | Generated HTML report, mandatory glossary and ADR files, grilling loop, design-it-twice sub-agents, proposing interfaces |

Derived skills have a `pack/skill-sources.json` entry. `architecture-review`
stays read-only and separate from `technical-design`, and `code-simplification`
stays separate from `refactor` by excluding behavior, compatibility, and
structural change.

No skill was split or retired. Skills are edited under `.agents/skills/` and mirrored to
`.claude/skills/` with `scripts/mirror-skills.py`, so both surfaces stay identical.
