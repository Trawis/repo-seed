# Label and Issue Guidance

**Document role**: Managed coding-agent guidance
**Sync destination**: `.agents/guidelines/labels.md`

This file is the single canonical source for shared label names, meanings,
and lightweight issue structure. Issue templates and other guidance agree
with it instead of defining a competing list.

## Canonical Type Labels

Every issue gets exactly one type label:

- `type: bug` - existing behavior is incorrect.
- `type: feature` - implementation-ready new behavior or capability.
- `type: tech-debt` - refactoring, internal cleanup, architecture
  improvement, or accumulated maintenance debt.
- `type: chore` - tooling, dependencies, CI, repository maintenance, or
  documentation maintenance.
- `type: decision` - a concrete choice must be resolved before
  implementation.
- `type: idea` - worth recording but not yet defined enough to implement.

## Priority Labels

Priority is optional. Do not require every issue to carry one.

- `priority: critical`
- `priority: high`
- `priority: medium`
- `priority: low`

## Area Labels

Do not establish a mandatory shared `area:*` taxonomy. A project may add a
small number of project-specific component or area labels when they provide
real filtering value. Do not create one merely for completeness.

## Idea, Decision, and Feature Lifecycle

```text
idea -> decision (only when a choice must first be resolved) -> feature / tech-debt / chore
```

An idea may remain incomplete indefinitely; not every idea needs a decision
step. Promote it to `type: decision` only when a choice blocks
implementation, and to `type: feature`, `type: tech-debt`, or `type: chore`
once it is implementation-ready.

## Issue Structure

Normal implementation issues:

```md
## Summary

Short explanation of the problem or change.

## Goal

What should be true after this work is complete?

## Suggested approach

Optional implementation direction when useful.

## Done when

- Concrete acceptance condition.
- Concrete acceptance condition.
```

`Suggested approach` is optional. Small issues may use only `Summary`,
`Goal`, and `Done when`. Acceptance conditions should be observable or
testable where practical. Do not force sections such as Context, Scope,
Dependencies, Risks, Priority, Requirements, or Implementation Notes onto
every issue; add one only when the individual issue benefits from it.

Decision issues:

```md
## Decision

What must be decided?

## Context

Relevant constraints or alternatives.

## Done when

- The decision is recorded.
- Follow-up implementation issues are created when needed.
```

Bug reports keep a dedicated diagnostic structure with reproduction,
expected, actual, and environment fields; see
`.github/ISSUE_TEMPLATE/bug_report.md`.

## GitHub-Hosted Labels

This file defines the label catalog represented in repository files and
scaffolded templates. It does not prove which labels currently exist in the
GitHub repository itself. Confirm and reconcile hosted labels directly
through GitHub (its UI, API, or an existing label-sync tool the project
already uses); repo-seed does not manage hosted label state.
