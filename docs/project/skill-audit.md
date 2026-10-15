# Skill Audit

**Document role**: `repo-seed` project documentation

**Sync behavior**: Never copied into target repositories

Record of the keep/adapt/replace/split/retire decision for each distributed
skill, made by reading the complete upstream skills and their supporting files
at the pinned revisions below. Both upstream projects are MIT-licensed. No
upstream text was copied: adopted ideas are restated in repo-seed's own words,
so no `pack/skill-sources.json` entry was required (see
[Upstream-derived skills](upstream-skills.md)). Re-run the audit by comparing
against the revisions here.

| Upstream | Revision inspected |
|---|---|
| `mattpocock/skills` | `49dd158d1076134a641b33efb035946536778336` |
| `obra/superpowers` | `bb92a77741419a4ab5f06e711a283343f1ada0c3` |

Upstream issue trackers were not checked (the GitHub API returned 403 from the
audit environment), so known upstream defects were not reviewed; the decisions rest on the skill text, which
was reviewed for tool-specific assumptions.

## Decisions

| Skill | Decision | Basis |
|---|---|---|
| `bug-fix` | Adapt | Compared with `diagnosing-bugs` and `systematic-debugging`. Adopted: build and tighten a red-capable feedback loop first, minimize the reproduction, falsifiable hypotheses, one variable at a time, greppable debug markers, regression test only at a real seam, stop after repeated failed fixes, secret redaction. Not adopted: the HITL shell script template, the mandatory phase gates and persuasion tables, the "show hypotheses to the user" checkpoint, the `superpowers:` skill namespace, and automatic commit or PR behavior. |
| `code-review` | Adapt | Compared with `code-review`, `requesting-code-review`. Adopted: pin the comparison to a merge-base and fail early on a bad ref or empty diff, cite the documented rule, treat smells as judgement calls that repository rules override, keep standards findings separate. Not adopted: parallel sub-agents (tool-specific), the full smell catalog (overlaps the separately planned simplification skill), the issue-tracker fetch, and severity labels. Spec and acceptance-criteria alignment is deferred to the dedicated issue. |
| `refactor` | Keep | The inspected upstreams offer architecture discovery (`improve-codebase-architecture`, `codebase-design`), which produces an HTML report and proposes deepening candidates rather than performing behavior-preserving edits. The current skill is shorter and already enforces contract preservation, deletion over wrappers, and separation of behavior from structure. |
| `dependency-upgrade` | Keep | Neither inspected upstream contains a dependency-upgrade workflow, so there is no alternative to compare. The audit did not search beyond the two upstreams named in the issue, so other maintained upgrade workflows remain unevaluated. |
| `technical-design` | Keep | `to-spec` and `writing-plans` publish to an issue tracker or write implementation plans under their own paths, with a larger framework. repo-seed's skill keeps its document ownership (`docs/project/designs/`, the TSD template) and no-invented-decisions rule. |
| `documentation-bootstrap` | Keep | `domain-modeling` builds a glossary and ADRs interactively. It does not replace evidence-only documentation of an existing repository, which repo-seed's no-invented-intent rule requires. |

The `issue-authoring` skill added afterwards was written from `triage`
(`49dd158d1076134a641b33efb035946536778336`) and its `AGENT-BRIEF.md`. Adopted
ideas: concept-level redundancy search, claim verification before drafting,
behavioral and durable acceptance criteria, and a prior-rejection check
(restated as the already-implemented, removed-on-purpose, and already-tracked
cases). Not adopted: the tracker state machine and role labels, setup files,
the AI-disclaimer policy, `.out-of-scope/` writes, and automatic hosted
writes.

The `issue-implementation` skill was written from `implement` and
`implement-spec` (same revision). Adopted ideas: state the ticket before
starting, run narrow checks while working and the full suite at the end, and
review the finished work. Not adopted: integration branches, per-ticket
worktrees, implementer and merger sub-agents, `tdd` and `code-review` calls by
tool name, automatic commits, draft pull requests, and ticket closing.

The `code-review` acceptance review was added afterwards from `code-review` in
`mattpocock/skills` (same revision) and `code-review` in `github/spec-kit`
(`f6e72bc8523de8ec8368129cbdea78d45f27cef8`, MIT). Adopted ideas: evaluate the
change against the originating spec separately from standards, quote the
requirement behind each finding, flag omitted work and unrequested additions,
require positive and negative test coverage, look for regression-test evidence
on bug fixes, and treat an intentional design change differently from an
unexplained violation. Not adopted: parallel sub-agents, tracker setup files,
framework-specific design documents and commands, and posting review actions.

No skill was split or retired. Both skill surfaces were updated together and
remain identical.
