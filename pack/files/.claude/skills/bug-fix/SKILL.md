---
name: bug-fix
description: Diagnoses and fixes incorrect existing behavior with a root-cause-first workflow and regression validation. Use when asked to fix a bug, regression, crash, failing edge case, incorrect result, or reproducible test failure.
---

# Bug Fix

Follow the applicable `AGENTS.md` files and `.agents/project.md`. Load the
relevant language conventions and specialized guidance for the affected code.

## Workflow

1. Establish the failing behavior before editing. Reproduce it with an existing
   test, a focused command, a minimal example, or a concrete traced failure path
   when execution is unavailable.
2. Inspect the affected implementation, callers, tests, configuration, and
   recent relevant changes only as needed to identify the root cause.
3. Separate the root cause from downstream symptoms. Prefer fixing the source of
   the invalid state or behavior rather than adding guards around every symptom.
4. Add or update a regression test when practical. The test should fail for the
   original defect and exercise observable behavior rather than incidental
   implementation details.
5. Make the smallest coherent fix. Do not combine the bug fix with unrelated
   cleanup or redesign.
6. Avoid compatibility wrappers, fallback branches, or legacy behavior unless a
   supported version, public contract, stored data format, or explicit
   requirement still needs them.
7. Re-run the focused reproduction or regression test, then the narrowest
   relevant broader validation.

## Investigation Rules

- Do not guess at a cause because an error message appears nearby.
- Do not suppress exceptions, validation, or warnings merely to make a failing
  test pass.
- Do not weaken assertions or delete meaningful tests unless the expected
  behavior itself is proven wrong.
- Use Git history only when it helps explain a concrete regression or contract;
  do not scan history by default.

## Completion

Report the root cause, the fix, regression coverage, and validation performed.
Call out any failure mode that could not be reproduced or any broader check that
was unavailable.
