---
name: code-review
description: Reviews diffs, pull requests, patches, or existing code for correctness, regressions, security, maintainability risks, and missing validation. Use when asked to review, audit, critique, inspect a change, find defects, or assess code without implementing fixes by default.
---

# Code Review

Follow the applicable `AGENTS.md` files and `.agents/project.md`. Load relevant
language conventions or specialized guidance only when the reviewed code
requires them.

Do not modify files unless the user also asks for fixes.

## Workflow

1. Establish the review scope: changed files, diff or comparison base, requested
   behavior, and any acceptance criteria.
2. Inspect the changed implementation together with relevant callers, callees,
   tests, configuration, schemas, and public contracts. Do not review a diff in
   isolation when surrounding behavior determines correctness.
3. Prioritize concrete defects: incorrect behavior, regressions, data loss,
   security issues, broken compatibility, concurrency problems, resource leaks,
   unsafe error handling, and meaningful performance risks.
4. Distinguish actionable defects from preferences. Do not report style nits
   already handled by automated formatting or unsupported hypothetical risks.
5. Check whether tests exercise the changed behavior and important failure or
   boundary paths. Report missing coverage only when it creates a concrete
   regression risk.
6. Validate suspected findings with repository evidence or the narrowest useful
   checks when practical. Do not present speculation as a confirmed defect.

## Findings

Report findings before general commentary, ordered by severity.

For each finding include:

- the affected file and location;
- the concrete failure mode or user impact;
- why the current code causes it;
- the smallest useful direction for fixing it.

If there are no actionable findings, say so explicitly and mention any relevant
validation gaps or residual risks.

## Completion

State what was reviewed and which checks were run. Never claim code, tests,
hosted state, or runtime behavior was inspected when it was not.
