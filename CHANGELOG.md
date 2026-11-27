# Changelog

**Document role**: `repo-seed` repository documentation

**Sync behavior**: Never copied into target repositories

All meaningful user-facing and developer-facing changes should be documented in
this file.

Use newest entries first. Do not dump raw git commits here.

## 6.18.0 - 2026-11-24

Added a reference-only session handoff template, `docs/templates/handoff.template.md`, for every profile. When a user asks to hand off unfinished work to another agent session, the agent can copy it to a path or channel the user chooses, outside `docs/project/`. It records the governing task and scope, the branch, base commit, and pull request, working-tree changes including ones to preserve, completed and remaining work, validation status, blockers, the next action, and links to authoritative sources. The template states that a handoff is temporary and non-authoritative and never overrides current source, requirements, designs, or issues. The receiving session must verify the current repository state before acting on it, and secrets, conversation transcripts, and undecided choices stay out. Like the TSD reference, it has no scaffold target: sync never creates, updates, or deletes live handoffs, and no skill, flag, or required workflow is added.
## 6.17.1 - 2026-11-24

Added an optional Gameplay Experiments table to the GDD template's Playtest Criteria section. A game project can record an uncertain mechanic as a hypothesis, the minimum playable experiment that tests it, the observable result, and a decision to accept, revise, or discard it. The template states that a hypothesis is not accepted gameplay intent, and that only accepted results move into the authoritative sections. It also notes that experiments need no production presentation or unrelated systems, and that development-only tuning controls help when a mechanic depends on values such as speed, timing, or cost. The existing structure, playtest criteria, and scaffold ownership are unchanged, and unchanged scaffolds upgrade as before.

## 6.17.0 - 2026-11-24

Added two opt-in conventions, `lua` and `gdscript`, available under every profile and independent of each other and of Unity. `lua` assumes no host. It covers identifying the Lua version or dialect, such as 5.1 through 5.4, LuaJIT, or Luau, and the host's APIs and sandbox. It also covers `local` scope without stray globals, modules that return tables, 1-based arrays and the unreliable `#` on tables with holes, `pairs` versus `ipairs`, and consistent metatable patterns. It adds `nil, message` or `error` reporting, `pcall` and `xpcall`, explicit resource closing or `<close>`, no `load` of untrusted code, checked coroutine resumes, profiled hot-loop caching, LDoc or LuaLS annotations, and configured StyLua, Luacheck, or Selene with tests. `gdscript` covers the project's Godot version and the differences between Godot 3 and 4, the GDScript style guide's naming and member order, past-tense signals, and static typing with warnings fixed. It also covers call-down and signal-up scene boundaries, `@onready` and unique-name references, `is_instance_valid` and `queue_free`, and no scene-tree changes from threads. It adds signal disconnection, `_ready` initialization, `_physics_process` versus `_process`, shared `Resource` instances, no untrusted resource loading, `##` documentation comments, and configured gdtoolkit checks with GUT or gdUnit4 tests. The `--conventions` help text and the README files list the new IDs.

## 6.16.0 - 2026-11-24

Added two opt-in conventions, `ruby` and `rails`, available under every profile. Select `--conventions ruby` for Ruby libraries and scripts or `ruby,rails` for Rails applications. `ruby` treats configured RuboCop or Standard rules as authoritative, with the community Ruby Style Guide as an optional baseline. It covers the supported Ruby versions, Bundler and lock files, compatible gem APIs, naming with `?` and `!` conventions, frozen string literals where used, `Enumerable` idioms, small classes with private helpers, and no monkey patching or unsafe `send`. It also covers specific `StandardError` subclasses without bare `rescue`, block-form resource handling, no `eval` or `Marshal.load` on untrusted data, `YAML.safe_load`, safe `system` arguments, YARD or RDoc, and configured lint and tests. `rails` uses the installed version's Rails Guides without adding gems or layers. It covers Zeitwerk naming, resourceful routes and thin controllers, credentials, strong parameters, authorization with user-scoped lookups, N+1 avoidance and batched processing, and query placeholders. It also covers database constraints behind validations, careful callbacks, transactions, reversible migrations that are never edited after running, idempotent jobs with identifiers, ERB escaping and CSRF, and tests with RuboCop and Brakeman when configured. The `--conventions` help text and the README files list the new IDs.

## 6.15.0 - 2026-11-24

Added two opt-in conventions, `django` and `fastapi`, available under every profile. Each is selected independently alongside `python`, and the `python` convention is unchanged. `django` uses the installed release's documentation and notes that Django's own coding style is for contributors to Django. It covers existing app boundaries, settings with secrets from the environment, N+1 avoidance with `select_related` and `prefetch_related`, and parameterized raw SQL. It also covers `transaction.atomic`, `select_for_update` or `F()` for lost updates, `on_commit` side effects, reviewed migrations with historical models in data migrations, form or serializer validation, per-view authorization with user-scoped querysets, CSRF and auto-escaping, production settings, and `manage.py check --deploy` and `makemigrations --check`. `fastapi` uses the installed FastAPI and Pydantic versions and treats router composition as a tool, not a required architecture. It covers typed request and response models with separate input and output models, `Depends` and `yield` dependencies for per-request resources, lifespan-managed shared resources, and no blocking work inside `async def`. It also covers dependency-based authentication with object-level authorization, explicit CORS, no logged secrets, and `TestClient` or HTTPX tests with dependency overrides. The `--conventions` help text and the README files list the new IDs.

## 6.14.0 - 2026-11-24

Added two opt-in conventions, `vue` and `angular`, available under every profile. Each is selected independently alongside `javascript` and `typescript`, with no cross-framework dependency or migration. `vue` keeps the installed version and the existing Composition or Options API. It covers multi-word component names, typed props and declared emits, read-only props, composables, `computed` instead of copying watchers, watcher cleanup, and reactivity-preserving destructuring. It also covers stable `v-for` keys without `v-if` on the same element, simple templates, no untrusted `v-html` or templates, measured performance work, and component tests with the configured lint and `vue-tsc`. `angular` covers version-matched documentation, the existing standalone or NgModule model, focused components with logic in services, injection through the injector at the narrowest scope, and signals or RxJS as used. It adds unsubscribing with the `async` pipe or `takeUntilDestroyed`, no nested subscriptions, tracked `@for` loops, side-effect-free templates, `OnPush` where the project uses it, client and server validation, no sanitizer bypasses for untrusted content, server-side authorization beyond route guards, and template-level tests with lint and `ng build`. The `--conventions` help text and the README files list the new IDs.

## 6.13.0 - 2026-11-24

Added two opt-in conventions, `dart` and `flutter`, available under every profile. Select `--conventions dart` for standalone Dart or `dart,flutter` for Flutter applications. `dart` covers the `pubspec.yaml` SDK constraint, dependency and lock-file practice, compatible published APIs, `dart format`, Effective Dart naming, private `_` members, and sound null safety with sparing `!` and `late`. It also covers explicit public API types without needless `dynamic`, `final` and `const`, awaited or `unawaited` futures, cancelled subscriptions and closed controllers, `Exception` versus `Error` with `on` clauses, `///` doc comments, and `dart analyze`, format checks, and `dart test`. `flutter` covers the project's existing state management, architecture, and SDK, without mandating a package or pattern. It adds small widget classes over widget-returning helpers, `const` widgets, side-effect-free `build`, and a single owner for state. It also covers disposing controllers with `super.dispose()` last, `mounted` checks after `await`, constraint-based responsive layouts and text scaling, semantic labels and tap targets, builder lists, profiling before expensive effects, no secrets in app bundles, and widget, integration, and unit tests with `flutter analyze` and `flutter test`. The `--conventions` help text and the README files list the new IDs.

## 6.12.0 - 2026-11-24

Added an opt-in `swift` convention, available under every profile, for Swift applications, libraries, and tools on any platform, without assuming an Apple UI framework. It covers the Swift tools version, language mode, and deployment targets without incidental upgrades or upcoming features, availability checks, and the project's build system. It applies the Swift API Design Guidelines: clarity at the point of use, argument labels, uniform acronym casing, and noun or verb method names by side effects. It also covers optional unwrapping over force-unwraps and `try!`, specific thrown errors without careless `try?`, value types by default, small protocols, and weak captures and delegates to avoid retain cycles. Concurrency guidance covers structured concurrency with cancellation checks, actor isolation and `Sendable` checking without unexplained `@unchecked Sendable` or `nonisolated(unsafe)`, and main-actor UI updates. It also covers DocC documentation comments and validation with `swift build`, `swift test` or the project's scheme, and configured swift-format or SwiftLint. The `--conventions` help text and the README files list the new ID.

## 6.11.0 - 2026-11-24

Added an opt-in `kotlin` convention, available under every profile, for Kotlin on JVM, Android, multiplatform, or native targets, without assuming Android or a build tool. It covers the declared Kotlin, `jvmTarget`, and platform versions without incidental opt-in APIs, the existing build tool and catalog, and the configured formatter with the official Kotlin coding conventions as the fallback. It also covers naming, `val` and read-only collections, and readable use of expression bodies and scope functions. On types, it adds nullable types over `!!`, checking Java platform types, data classes, sealed hierarchies with exhaustive `when`, and extension functions without hidden side effects. On errors and coroutines, it adds specific exceptions, structured concurrency without `GlobalScope`, rethrowing `CancellationException`, main-safe suspending functions, lifecycle-scoped `Flow` collection, and `@JvmStatic`, `@JvmOverloads`, and `@Throws` for Java callers. It also covers KDoc for public APIs and the build's compile, test, and configured ktlint or detekt tasks. The `--conventions` help text and the README files list the new ID.

## 6.10.0 - 2026-11-24

Added an opt-in `powershell` convention, available under every profile, for PowerShell scripts and modules. It complements `scripts` and is kept separate from `shell`. It covers targeting Windows PowerShell 5.1, PowerShell 7+, or both with `#Requires` or `CompatiblePSEditions`, avoiding 7+-only syntax on 5.1, cross-platform paths, and explicit encodings. It also covers approved `Verb-Noun` names, full cmdlet names instead of aliases, and advanced functions with `[CmdletBinding()]` and parameter validation. Output guidance covers emitting objects instead of formatted text, the right output and message streams, and suppressing stray output. For errors, it adds `$ErrorActionPreference = 'Stop'`, checking `$LASTEXITCODE` after native commands, and explicit exit codes. It also covers `Join-Path` and `-LiteralPath`, quoting, no `Invoke-Expression`, `SupportsShouldProcess` with `-WhatIf` and `-Confirm` for state changes, `[PSCredential]` instead of plain-text passwords, comment-based help, and configured PSScriptAnalyzer and Pester checks. The `--conventions` help text and the README files list the new ID.

## 6.9.0 - 2026-11-24

Added an opt-in `rust` convention, available under every profile, for Rust libraries, applications, and tools. It covers the crate's edition, `rust-version` (MSRV), and toolchain file, workspace dependency and feature conventions, `Cargo.lock` discipline, and semver-compatible public APIs. It also covers `rustfmt` and standard naming, API Guidelines conversion and getter names, and private-by-default items. On ownership and errors, it adds borrowing over unconsidered clones, general inputs with concrete outputs, elided lifetimes, `Option` and `Result` with type-encoded invariants, `?` propagation with context, typed library errors, and `unwrap` and `expect` only for proven invariants. It adds panics for bugs only, thread-safe shared state, no locks held across `.await`, and non-blocking async. `unsafe` must be minimal and justified, with `// SAFETY:` comments and `# Safety` docs. It also covers rustdoc with `# Errors`, `# Panics`, and examples, and validation with `cargo fmt --check`, Clippy, `cargo test` including doctests, and MSRV builds where CI checks them. The `--conventions` help text and the README files list the new ID.

## 6.8.0 - 2026-11-24

Added two opt-in conventions, `c` and `cpp`, available under every profile. They keep the two languages' ownership models distinct, and each can be selected alone or together for mixed codebases. `c` covers the declared standard, compilers, and build system without incidental migrations, ABI-stable public headers, the configured formatter, symbol prefixes and `static` linkage, include guards, and macro hygiene. It covers single-owner allocation with documented frees, checked allocation and I/O, bounds with explicit buffer sizes, and banned unbounded string functions. It also covers overflow-safe size arithmetic, conversion and shift pitfalls, common undefined behavior, error returns with cleanup on every path, `errno` use, and header documentation of preconditions and ownership. `cpp` adds respecting the declared C++ standard and constraints such as disabled exceptions or RTTI, RAII instead of raw `new` and `delete`, `unique_ptr` by default and `shared_ptr` only for shared ownership, and the rule of zero or five. It also covers dangling views and iterators, const correctness, `explicit`, `override`, virtual destructors, constrained templates, the project's error model, scoped locks, and joined threads. Both validate with the project's warning flags, tests, configured static analysis or clang-tidy, and sanitizers when available. The `--conventions` help text and the README files list the new IDs.

## 6.7.0 - 2026-11-24

Added an opt-in `go` convention, available under every profile, for Go libraries, services, and command-line tools. It covers the `go` and `toolchain` lines in `go.mod`, tidy module files, major-version import paths for breaking changes, `gofmt`, `MixedCaps` and initialism naming, short package names without stutter, and doc comments on exported identifiers. It also covers checked errors wrapped with `%w` and inspected with `errors.Is` and `errors.As`, panics only for programmer errors, and consumer-side small interfaces. For concurrency and resources, it adds `context.Context` as the first parameter, goroutines with clear owners and exit conditions, mutex discipline, deferred cleanup, and explicit network timeouts. Validation uses table-driven tests, `go vet`, `go test`, the race detector, and the configured linter. Effective Go is cited for core idioms only, since it is not updated for modules or generics. The `--conventions` help text and the README files list the new ID.

## 6.6.0 - 2026-11-24

Added two opt-in conventions, `java` and `springboot`, available under every profile. Select `--conventions java` for Java libraries and applications, or `java,springboot` for Spring Boot services. `java` covers the declared Java release and build wrapper, the configured formatter with Google Java Style as an optional baseline, and naming and narrow visibility. It also covers generics without raw types, nullness annotations and `Optional` for return values only, records and sealed types only where supported, and consistent `equals` and `hashCode`. On errors and resources, it adds specific exceptions with causes, handling `InterruptedException`, try-with-resources, avoiding Java deserialization of untrusted data, executors, documented shared-state guards, Javadoc for public APIs, and the build's verify or check tasks. `springboot` adds version-matched documentation, the existing structure, constructor injection, validated `@ConfigurationProperties`, and secrets kept out of committed configuration. It also covers Bean Validation, DTOs instead of exposed entities, server-side authorization and CSRF, `@Transactional` on the owning service with its proxy limitation, N+1 avoidance, migrations through Flyway or Liquibase rather than `ddl-auto`, secured Actuator endpoints, and choosing between slice tests and `@SpringBootTest`. The `--conventions` help text and the README files list the new IDs.

## 6.5.0 - 2026-11-24

Added an opt-in `sql` convention, available under every profile, for SQL in application code, migrations, and database scripts. It defers to the project's actual database engine and version and its configured formatter or SQLFluff dialect. It covers explicit column lists and joins, three-valued `NULL` logic and the `NOT IN` pitfall, deterministic ordering for pagination, row multiplication in joins, constraints for invariants, bound parameters with allow-listed dynamic identifiers, short transactions with the required isolation and locking, least privilege, and guarded bulk updates and deletes. Migration guidance covers using the project's migration tool, adding new migrations instead of editing applied ones, preserving data through staged destructive changes, lock-aware changes on large tables, and down migrations or recovery plans. It also requires indexes backed by query-plan evidence and testing against the target engine rather than a substitute. It forces no ORM or database change. The `--conventions` help text and the README files list the new ID.

## 6.4.0 - 2026-11-24

Added two opt-in conventions, `react` and `nextjs`, available under every profile. Select `react` for React-only projects, or add `nextjs` for Next.js, alongside `javascript` and optionally `typescript`. `react` covers the Rules of React: pure rendering, no mutation of props or state, top-level hooks, and rendering components as elements. It also covers minimal derived state with a single owner, effects only for external synchronization with complete dependencies and cleanup, functional updates, stable keys, deliberate memoization or React Compiler guidance, sanitized `dangerouslySetInnerHTML`, accessible components, and behavior-focused tests with the hooks lint rules. `nextjs` covers version-matched documentation and keeping the existing App or Pages Router. It also covers minimal `"use client"` boundaries, serializable and secret-free props, server-only modules, explicit caching without shared caching of per-user data, and authorizing inside every Server Action and route handler rather than only in middleware or proxy. It adds the `NEXT_PUBLIC_` exposure rule, existing header and image configuration, and `next build` as a validation step. Neither forces a router migration, state library, or architecture. The `--conventions` help text and the README files list the new IDs.

## 6.3.0 - 2026-11-24

Added two opt-in conventions, `html` and `css`, available under every profile and independent of any frontend framework. `html` covers document structure and landmarks, native elements over rebuilt controls, keyboard operation and focus, `alt` text and accessible names, ARIA only when no native element fits, labeled form controls with fieldsets, server-side validation, escaping untrusted data, unsafe URLs, Content Security Policy-friendly markup, progressive enhancement, reserved media dimensions, and configured validation and accessibility checks. `css` covers browser targets and `@supports`, low and predictable specificity without `!important` battles, the project's layering, naming, and design tokens, flexbox and grid layouts that tolerate content growth, relative units, visible focus styles, contrast, `prefers-reduced-motion` and theme preferences, accessible hiding, comments for non-obvious constraints, and configured formatter and Stylelint checks. Neither mandates a CSS framework or methodology. The `--conventions` help text and the README files list the new IDs.

## 6.2.0 - 2026-11-24

Added three opt-in conventions, `javascript`, `typescript`, and `nodejs`, available under every profile and selectable independently or together, for example `--conventions javascript,typescript,nodejs` for a Node.js TypeScript service. `javascript` covers runtime-neutral language practice: browser and engine targets, the existing module system, naming, `const` and `let`, strict equality and coercion pitfalls, awaited promises and `Error` causes, `AbortSignal`, avoiding `eval` and `innerHTML` with untrusted data, prototype pollution, JSDoc, and configured lint and tests. `typescript` adds respecting `tsconfig.json` without loosening it, `unknown` over `any`, narrowing over assertions, `@ts-expect-error` with a reason, purposeful generics, explicit exported signatures, runtime validation at trust boundaries, TSDoc, and the configured type check. `nodejs` adds supported runtime versions, ESM and CommonJS boundaries and `exports`, lock-file and package-manager discipline, not blocking the event loop, stream `pipeline`, timeouts, validated configuration and secrets, error and signal handling with graceful shutdown, safe child processes and paths, and the configured or built-in test runner. The `--conventions` help text and the README files list the new IDs.

## 6.1.0 - 2026-11-24

Added two opt-in conventions, `php` and `laravel`, available under every profile. Select `--conventions php` for standalone PHP or `--conventions php,laravel` for Laravel applications. `php` covers supported versions from `composer.json`, Composer and lock files, PSR-4 autoloading, the configured coding standard with PER Coding Style as the fallback, naming, `strict_types`, native types and PHPDoc for what types cannot express, and strict comparison. It also covers specific exceptions and exception chaining, prepared statements, context-aware escaping, unsafe `unserialize` and shell use, password hashing, and validation with configured PHPUnit or Pest, static analysis, and formatters. `laravel` adds version-matched documentation, existing structure without new architectural layers, injection and `config()` rather than `env()` outside config files, form request validation, policies and gates, mass-assignment protection, eager loading and chunked queries, transactions, raw-query bindings, migrations, retry-safe jobs dispatched after commit, scheduled-task overlap, CSRF and Blade escaping, and testing with fakes, Pint `--test`, and Larastan when configured. The `--conventions` help text and the README files list the new IDs.

## 6.0.7 - 2026-11-24

Reviewed the `csharp` and `unity` conventions against Microsoft and Unity documentation. The `csharp` convention now labels tabs, brace omission for guards, the `Enum` suffix, and enum values starting at `1` as Repo Seed defaults that a project's own style overrides, and notes where they differ from Microsoft's conventions. It also bases language features on `LangVersion`, keeps nullable annotations accurate, and covers disposal with `using` and `await using`, `CancellationToken` propagation, avoiding `async void` and blocking waits, and XML documentation comments for public APIs. It adds validation with `dotnet build`, `dotnet test`, and configured analyzers. The `unity` convention now separates its callback source order from runtime scheduling. It notes that `FixedUpdate` runs zero or more times per frame, that callback order across objects is not guaranteed, and when `Awake` and `Start` run. It explains why `is null`, `?.`, and `??` bypass Unity's destroyed-object check, and that `Destroy` is deferred. It covers coroutine and async cleanup, serialization rules including `[FormerlySerializedAs]`, `.meta` files, and checking APIs against the project's Unity version. Both conventions link to upstream references. Convention IDs, paths, and selection are unchanged.

## 6.0.6 - 2026-11-24

Broadened the `python` convention from command-line scripts to libraries and applications, and renamed it Python Conventions. It now follows the project's supported Python versions and configured formatter, linter, type checker, test runner, and dependency manager, and records dependencies where the project already declares them. The standard library stays a preference, not a ban on dependencies. It adds PEP 8 naming and import grouping, no side effects at import time, a stable public API and package boundaries, type hints valid for the minimum version, and PEP 257 docstrings for public APIs. On errors, it requires specific exceptions, chaining with `raise ... from`, and libraries that raise instead of exiting. It also covers context-managed resources, explicit text encodings, not using `assert` for validation, and avoiding `shell=True`, string-built SQL, and loading untrusted pickles. CLI rules are now scoped to executable scripts and still refer to `scripts`. Reference links are added. The convention ID, path, and selection are unchanged.

## 6.0.5 - 2026-11-24

Expanded the `shell` convention for POSIX `sh` and Bash. It now treats the shebang as the dialect contract, lists common Bash-only constructs, and notes the oldest supported Bash version, such as 3.2 on macOS. It adds guidance on naming, `local` scope, and a `main "$@"` entry point. It also covers quoted expansions, preserving `"$@"`, building commands in arrays instead of strings, avoiding `eval`, and handling filenames safely. It replaces the bare `set -euo pipefail` recommendation with its limits: errexit is ignored in conditions and lists, `local var=$(cmd)` masks failures, command substitutions do not inherit errexit by default, `pipefail` is missing from dash, and `set -u` has empty-array behavior before Bash 4.4. Critical commands are now checked explicitly. It adds `mktemp` with cleanup traps, guards for destructive paths, and validation with the declared interpreter's syntax check, configured ShellCheck, shfmt, or Bats, and a strict POSIX shell. General help, output, and exit-code rules stay in `scripts`. The convention ID, path, and selection are unchanged.

## 6.0.4 - 2026-11-24

Refined the `scripts` convention with language-independent command-line practice. It now treats an existing script's documented arguments, output, and exit codes as a contract that new defaults do not retrofit. It also covers `-h` and `--help` content, named and long-form options, never accepting secrets as option values, result output on standard output with diagnostics on standard error, stable machine-readable output, no color or progress output when not writing to a terminal, actionable error messages, and documented exit codes. The convention now requires prompting only on a terminal with a noninteractive alternative, bounded timeouts, confirmation before destructive actions, and safe reruns after interruption. It also covers validating failure paths and noninteractive runs, and links to the Command Line Interface Guidelines, POSIX utility conventions, and NO_COLOR. The convention ID, path, and selection are unchanged.

## 6.0.3 - 2026-11-21

Extended the `bug-fix` skill to cover visual defects, such as layout overlap, rendering problems, and an incorrectly presented state. A capture of the wrong state is now a usable reproduction signal, and a missing viewport size, resolution, zoom, theme, or application state is requested when it changes the result. The before and after comparison must reproduce the same conditions, and a successful build or a passing test that never renders the affected view does not show that a visual defect is corrected. The agent now reports what it could not verify visually, and non-visual fixes stay free of screenshot, recording, and visual-tooling requirements. The existing reproduction, root-cause, regression, and secret-redaction rules are unchanged.

## 6.0.2 - 2026-10-19

Fixed `sync-docs.py` so a managed file that a release removes from the manifest, such as a retired skill under `.agents/skills/` and `.claude/skills/`, is deleted from the target when it still matches its recorded hash. Previously every such file was kept and tombstoned. A modified file is still kept and tombstoned, and a recorded path outside `.agents/guidelines/`, `.agents/conventions/`, `.agents/skills/`, `.claude/skills/`, and `docs/templates/` is never deleted, nor is a symbolic link, directory, or path outside the repository. Existing tombstones for files that now match again are cleared on the next sync.

## 6.0.1 - 2026-10-18

Fixed `--audit` to report a tombstoned path that is a symbolic link, including a dangling one, instead of reporting no drift. Fixed the reusable audit workflow to edit or close only drift issues whose body starts with its `<!-- repo-seed-audit -->` marker, so an unrelated issue with the same title is left alone. An open drift issue created by an earlier release has no marker, so close it manually once the workflow opens its marked replacement.

## 6.0.0 - 2026-10-18

Removed the four `priority:*` labels from the label catalog and the Priority Labels and Area Labels sections from the issue guidance, and dropped priority from the issue-authoring skill. Changed `repo-seed.py labels` to report hosted `priority:*` labels and the old `critical`, `high`, `medium`, `low`, and `lowest` labels as retired with no replacement. Hosted labels are still never deleted, and existing repositories keep any labels they have. Raised the minimum supported Python to 3.14, the only version CI tests, and moved the reusable audit and sync workflows to Python 3.14.

## 5.19.5 - 2026-10-17

Fixed the repository-audit skill to run the source pack's `sync-docs.py` with `--source`, `--target`, and `--audit` instead of the target's possibly outdated copy. Fixed `--audit` to report a target pack version newer than the source as ahead instead of behind, comparing versions numerically; a matching version still reports no version drift.

## 5.19.4 - 2026-10-17

Fixed the `--scaffold-workflows` help text, the pack README, and the repository-bootstrap skill to say the flag creates two request-only caller workflows, the drift-check issue and the sync pull request, and that the sync caller needs write permissions.

## 5.19.3 - 2026-10-17

Removed the pre-5.0 upgrade guide and shortened the pre-5.0 section in the pack README. A pre-5.0 state file still needs the 5.13.2 pack, as the script error says.

## 5.19.2 - 2026-10-17

Changed the sync script and the reusable audit and sync workflows to shorter comments, with no change in behavior.

## 5.19.1 - 2026-10-17

Changed the pack to ship each skill once, under `.agents/skills/`, and the sync script to install the same files under `.claude/skills/` in each target. Targets end up with the same files as before and a current sync reports no change to them; an older copied script leaves the existing `.claude/skills/` files in place. The manifest no longer lists `.claude/skills/` paths and both manifest loaders reject them.

## 5.19.0 - 2026-10-17

Added a reusable `sync.yml` workflow that keeps one pull request open on `chore/repo-seed-sync` while a target's managed files differ from the latest pack release, and a `repo-seed-sync.template.yml` caller that `--scaffold-workflows` now creates next to the drift-check caller. Changed `--scaffold-workflows` to create both workflow callers when they are missing, so an existing adopter that reruns it gets the new sync caller; delete it to opt out.

## 5.18.2 - 2026-10-17

Changed the sync to stop before writing anything when a managed file is not valid UTF-8, to show a diff and a closing note when a first sync overwrites a file with no recorded baseline, and to require the sync script when discovering a pack. Changed the audit to report non-UTF-8 and symlinked paths as findings instead of failing, and the manifest loaders to reject wrongly typed fields and a non-object state file with a clear error. Changed the release builder to reject `package_files: null` like the sync script. Changed the reusable drift workflow to drop persisted checkout credentials, run one audit per repository at a time, skip repositories without repo-seed state or with issues disabled, and look through up to 1000 issues, and the release workflow to tag the tested commit. Changed the Git guidance to say agents commit, push, open pull requests, merge, and delete branches only when asked, to cover pull request descriptions in the attribution rule, to resolve the base-branch contradiction, and to add the hotfix-into-release merge row. Fixed the changelog template, the bootstrap and audit skills, the drift-check template comment about Dependabot, and the pack README.

## 5.18.1 - 2026-10-17

Clarified the `git.md` rule on attribution. It now says what it always meant:
no AI attribution in commit messages or release text (assistant or model names,
co-author trailers, "generated with" lines). It no longer bans mentioning tools
by name, and it allows the exact trailer when the repository or the agent host
requires one.

## 5.18.0 - 2026-10-16

Added `--scaffold-workflows` to `sync-docs.py`. It creates
`.github/workflows/repo-seed-audit.yml`, a caller for the reusable drift-check
workflow, once, only when the file is missing. The `uses:` tag is the pack
version that created the file, so Dependabot can keep it current. Nothing is
created without the flag, an existing file is never changed, and the rest of
`.github/workflows` stays project-owned and unmanaged. This relaxes the rule
that no manifest entry may target that tree, for this one scaffold group only:
both the sync script and the release builder now accept a `workflows` group
whose target is inside `.github/workflows`, and still reject every other group.

## 5.17.0 - 2026-10-16

Added a reusable workflow, `.github/workflows/audit.yml`, that a target
repository can call on a schedule to detect drift. It downloads the latest
release, verifies its checksum, runs `sync-docs.py --audit` against the
caller, and keeps one issue open while the audit reports drift, closing it when
clean. It is optional, installs nothing into targets, and is not part of the
release archive. The README documents the caller workflow. Added a test for the
workflow's permissions and trigger.

## 5.16.1 - 2026-10-16

The `repository-upgrade` skill now tells the agent that a copy line marked
`and discard local changes` overwrites local edits, to rerun the command with
`--diff` to show the user those diffs, and to get their go-ahead before
applying.

## 5.16.0 - 2026-10-16

Added `--diff` to `sync-docs.py`. It behaves like `--dry-run` and also prints,
for each managed file whose local edits a sync would discard, a diff from the
pack's version to the local file. Sync output now says when an overwrite
discards local changes (`and discard local changes`, past tense after a real
sync) or has no recorded baseline (`; no recorded baseline`, as on a first sync
over an existing file). Overwrite behavior itself is unchanged.

## 5.15.1 - 2026-10-16

CI now also runs the test suite and command checks on macOS and Windows with
Python 3.14, using bash for every step. Added a `mirror-skills.py` test for a
case-only rename that runs only on case-insensitive filesystems, where the
earlier ordering bug could occur. No distributed content changed.

## 5.15.0 - 2026-10-16

Raised the supported Python version from 3.10 to 3.11. Python 3.10 reached
end of life on 2026-10-01 (PEP 619). CI now runs Python 3.11 and 3.14, and the
release workflow uses 3.11. The README states the new minimum. The scripts are
not made to refuse older interpreters, but they are no longer tested on them, so
adopters on 3.10 should move to 3.11 or newer before running a later pack.

## 5.14.4 - 2026-10-16

Fixes from an independent review of the 5.13.0 to 5.14.3 changes. The
`repository-upgrade` skill now reports an old-state-file error to the user and
asks instead of following it, so it cannot download a pack without permission,
and it again explains what `remove` and `preserve` lines in a dry run mean.
`sync-docs.py --audit` now flags `type: decision` and `type: idea` in a
target's existing issue forms. Existing forms are never overwritten, so a
target's `feature_request.yml` may still mention the `type: idea` label and
needs editing by hand. The `issue-authoring` description now names chore.
Repo-only tooling: `mirror-skills.py` refuses a symlinked mirror root, reports
and removes empty directories, and deletes stale files before copying; the
changelog test now checks the top heading itself. Corrected the changelog entry
for 5.14.2, the ownership doc's section layout, and the README's legacy label
list.

## 5.14.3 - 2026-10-16

Restored the original `issue-implementation` description. The 5.14.2 wording
dropped "fix" from its triggers and pointed bugs without an issue at
`bug-fix`, which the skill body already handles by delegating defect issues to
`bug-fix`.

## 5.14.2 - 2026-10-16

Updated the `repository-upgrade` skill for the removed pre-5.0 state bridge: it
no longer mentions converting an older state schema, tells the agent to follow
the script's error for an old state file, and no longer restates tombstone
rules that belong to the sync script. Added "use X instead" boundaries to the
descriptions of `repository-upgrade`, `repository-audit`, `issue-implementation`
(reverted in 5.14.3), `refactor`, and `technical-design`, and changed `refactor` to preserve
"supported" behavior to match its body. Removed the pre-5.0 note from the
`--conventions` help text. The upstream-derived skills are unchanged.

## 5.14.1 - 2026-10-16

Fixed `sync-docs.py --audit` aborting when a tombstoned or historical managed
path is a symbolic link that resolves outside the repository. The audit now
reports that path as a `tombstone:` finding and continues. Removed a redundant
deduplication set in the same audit loop. No other behavior changed.

## 5.14.0 - 2026-10-16

Removed the pre-5.0 state bridge from `sync-docs.py`. A `.repo-seed-state.json`
with `schema_version: 1` is now refused with a message that points to the 5.13.2
pack, the last one that converts it with a single `--conventions <list>` sync.
Audit no longer has a pre-5.0 mode. Removed the unused `schema_version` field
from the parsed state. Updated the README, pack README, and the Version 5
upgrade notes. Tombstones and retired-convention handling are unchanged.

## 5.13.2 - 2026-10-16

Closed gaps in repo-seed's own CI and release workflows, with no change to
distributed content. CI now runs every command in the `AGENTS.md` validation
list, checks whitespace in pull request changes, builds the archive with its
checksum, cancels superseded runs, and has a job timeout. The release workflow
runs tests in a read-only job, grants `contents: write` only to the publishing
job, serializes releases with a concurrency group, and reports when a version
already has a release. A test now fails when the top `CHANGELOG.md` entry
differs from `pack_version`. The README points to `AGENTS.md` for the
validation list instead of repeating it.

## 5.13.1 - 2026-10-16

Added `scripts/mirror-skills.py`, repo-seed-only tooling that generates
`pack/files/.claude/skills/` from `pack/files/.agents/skills/`. Skills are now
edited in one place and CI checks that the copy matches. No distributed skill
content changed.

## 5.13.0 - 2026-10-16

Removed the `type: decision` and `type: idea` labels from the issue convention,
the label catalog, and the `issue-authoring` skill. The type labels are now
`bug`, `feature`, `tech-debt`, and `chore`. Every type has an Issue Form: added
Tech Debt and Chore forms to the scaffolded templates
(`--scaffold-github-templates`) and removed the maintainer-only blank-issue
path and the Decision and Idea structures from `issues.md`. A choice that blocks
implementation is settled in the issue before work starts. Existing target
repositories keep their current forms. `sync-github-labels.py` and `issues.md`
list `type: decision` and `type: idea` as legacy labels to re-triage. Tightened
the `type: tech-debt` and `type: chore` definitions: tech-debt changes the
structure of the project's own source, chore covers the tooling, configuration,
and documentation around it. Added a tie-breaker rule, and aligned the label
catalog descriptions with `issues.md`.

## 5.12.4 - 2026-10-16

Added merge rules, release and hotfix flow, and commit message format to
`git.md`. Feature branches are squashed. Release and hotfix branches and
merge-backs to `develop` use merge commits, never squash. Releases are tagged on
`main`. Merged short-lived branches are deleted.

## 5.12.3 - 2026-10-16

Changed `AGENTS.md`, the Git, CI/CD, documentation, and issue guidelines, and
the convention files to shorter sentences, without changing any rule. Shortened
comments, docstrings, and help text in the Python scripts, with no behavior
change.

## 5.12.2 - 2026-10-16

Added a short pull request template, scaffolded to
`.github/pull_request_template.md` with `--scaffold-github-templates`. It is
created only when missing, so existing templates are kept. Changed changelog
guidance and the changelog template to short prose entries ordered added,
changed, fixed, removed.

## 5.12.1 - 2026-10-16

Fixed `--audit` not reporting legacy `bug`/`enhancement` labels in Issue Forms.
It now checks every `.md`, `.yml`, and `.yaml` file in `.github/ISSUE_TEMPLATE/`
(#100).

## 5.12.0 - 2026-10-15

Added the `repository-upgrade` skill. It upgrades a repo-seed install with the
newer pack's own `sync-docs.py`, starting with a dry run and ending with an
audit. It stops and asks when an older state needs an explicit selection.

## 5.11.0 - 2026-10-15

Added the `repository-bootstrap` skill. It applies repo-seed to a repository
with `sync-docs.py`, after a dry run, and checks the result. It warns that an
existing `AGENTS.md` and `CLAUDE.md` are replaced, and moves project content to
`.agents/project.md` first, with the user's agreement.

## 5.10.0 - 2026-10-15

Added the read-only `repository-audit` skill. It reports drift, stale files, and
competing agent guidance using the repository's own `sync-docs.py --audit`.

## 5.9.0 - 2026-10-15

Added the read-only `architecture-review` skill for `library`, `app`, and `game`
profiles. It reports a small ranked set of evidence-backed architecture
problems. Adapted from Matt Pocock's `improve-codebase-architecture` (MIT).

## 5.8.0 - 2026-10-15

Added the `code-simplification` skill. It simplifies code without changing
behavior and hands behavior changes to `refactor`. Adapted from Addy Osmani's
`code-simplification` (MIT). Turned off the `issue-authoring`,
`issue-implementation`, and `test-driven-development` wrappers in repo-seed's
own `.claude/settings.json`.

## 5.7.0 - 2026-10-15

Added the `test-driven-development` skill. It applies only when TDD is
requested. Adapted from Matt Pocock's `tdd` (MIT), with ideas from Superpowers'
`test-driven-development`.

## 5.6.0 - 2026-10-15

Added an acceptance review to `code-review`. When an issue or acceptance
criteria exist, each `Done when` condition is marked satisfied, unsatisfied, or
not verifiable. It also checks bug fixes for regression tests.

## 5.5.0 - 2026-10-15

Added the `issue-implementation` skill. It checks the issue against the current
repository and tracker before editing, and checks every acceptance condition
afterwards.

## 5.4.0 - 2026-10-15

Added the `issue-authoring` skill. It drafts issues from repository evidence,
checks for duplicates, and creates hosted issues only with permission.

## 5.3.0 - 2026-10-15

Changed `bug-fix` to start from a reliable reproduction and test one hypothesis
at a time. Changed `code-review` to validate the comparison base, cite
repository rules, and report standards findings separately. Audit decisions are
in `docs/project/skill-audit.md`.

## 5.2.0 - 2026-10-15

Added provenance tracking for skills derived from upstream repositories:
`pack/skill-sources.json` (shipped in the archive, never synced), a per-skill
`NOTICE.md`, and `scripts/validate-skill-sources.py`. The registry is empty for
now. Syncing stays offline. Maintainer steps are in
`docs/project/upstream-skills.md`.

## 5.1.0 - 2026-10-15

Added GitHub Issue Forms (`bug_report.yml`, `feature_request.yml`) in place of
the Markdown issue templates. They are scaffolded when missing. Existing `.md`
templates are not removed, so delete them after adopting the forms or GitHub
lists both.

## 5.0.0 - 2026-09-23

Breaking release. Added `--conventions` selection (`csharp`, `python`,
`scripts`, `shell`, `unity`), independent of profile; a fresh sync installs
none. Added `--audit`, a read-only drift report. Added `--scaffold <name>` for
`architecture`, `fsd`, `gdd`, and `user-guide`; `--scaffold-project-files` now
creates only README and CHANGELOG. Added the label catalog
`pack/github-labels.json` with `scripts/sync-github-labels.py` (`--check`,
`--apply`, needs the GitHub CLI), and issue guidance in
`.agents/guidelines/issues.md`. Changed the manifest to `schema_version: 3`,
which older and newer scripts cannot read from each other. Changed `CLAUDE.md` to
a plain `@AGENTS.md` import, issue labels to `type: bug` and `type: feature`,
and skills to the `minimal`, `library`, `app`, and `game` profiles. A state file
from before explicit conventions (schema 1) fails without `--conventions <list>`
and converts to schema 2 with it; see `docs/project/upgrading-to-5.md`. Removed
the `full` profile, pre-4.x migration (a target with no state file is a fresh
install), convention auto-detection, legacy scaffold markers (older unmarked
scaffolds are now project-owned), and `previous_hashes`.

## 4.2.0 - 2026-08-26

Added Codex and Claude Code skills for code review, bug fixing, refactoring,
dependency upgrades, technical design, and documentation bootstrap. `minimal`
gets the core skills, and other profiles also get technical design and
documentation bootstrap.

## 4.1.0 - 2026-08-26

Changed agent guidance so agents read only the documentation relevant to the
task, and check branch models only for Git and pull request work.

## 4.0.5 - 2026-07-08

Clarified branch-model discovery before branch and pull request work. Added
code convention checks before completion.

## 4.0.4 - 2026-07-07

Added guidance against decision-diary wording in documentation. Changed
templates to describe current state only.

## 4.0.3 - 2026-07-07

Changed metadata fields in the FSD, GDD, architecture, technical design, and
user-guide templates to lists.

## 4.0.2 - 2026-07-07

Fixed templates for non-ASCII punctuation, long lines, visible scaffold
instructions, and placeholder `Unreleased` headings.

## 4.0.1 - 2026-07-06

Fixed unknown pack paths in `.repo-seed-state.json` being accepted, and
protected the whole `.github/workflows/` tree from management. Corrected the
version 3 to 4 update command to run the new pack's script.

## 4.0.0 - 2026-07-06

Added existing-project bootstrap guidance for agents. Changed architecture to
the current system overview and TSD to a reference template for substantial
changes. Required an explicit profile on first sync, reused on later syncs, and
moved the manifest to schema version 2. `full` became a reference-only profile
that rejects project scaffolding. Removed the features template from normal
profiles and the generic `docs/project/tsd.md` scaffold.

## 3.4.1 - 2026-07-06

Changed existing `.gitignore` files to be reported as project-owned.

## 3.4.0 - 2026-07-06

Added a non-functional requirements section to the FSD template, a date column
to the architecture decision log, and a release note to the changelog template.
Removed the `.gitignore` scaffold; it is fully project-owned. Targets synced
with 3.3.0 or later drop the retired `docs/templates/gitignore.template`
automatically. Older ones can delete it by hand.

## 3.3.0 - 2026-07-06

Added `.repo-seed-state.json` to track managed files and tombstones, and
provenance hashes for Markdown scaffolds. Legacy files with local changes are
kept and reported. Profile reductions remove only unchanged stale files.
Protected `.editorconfig` and the pull request template as project-owned.
Unchanged managed files are no longer rewritten.

## 3.2.3 - 2026-07-05

Changed the version 3 migration guide to cover 1.x and 2.x installs.

## 3.2.2 - 2026-07-05

Clarified that Git Flow repositories keep merge commits across long-lived
branches.

## 3.2.1 - 2026-07-05

Added package instructions and the MIT license to the release archive, without
syncing them into targets.

## 3.2.0 - 2026-07-05

Changed guidance and conventions to be shorter, and templates to have one
purpose each. Fixed template review guidance to match stateless sync.

## 3.1.0 - 2026-07-05

Added contribution, security, license, install, and 2.x migration docs, a pull
request CI job, release checksums, and `--scaffold-editorconfig`. Added a
pre-copy check that fails on directory or symlink paths, and hardening against
unsafe source links and path collisions. Changed `library` to include general
coding conventions, Git guidance to be branching-model neutral, and the release
builder name to `scripts/build-release-bundle.py`. Removed the redundant
features document.

## 3.0.0 - 2026-07-04

Added a generic GitHub issue config template and made `.editorconfig` an
optional missing-only scaffold. Replaced stateful sync with plain managed-file
copying and missing-only scaffolding, moved all assets under `pack/`, renamed
the sync tool to `scripts/sync-docs.py`, and shipped one universal archive.
Removed managed-file hashes, target state, conflict copies, drift tracking,
migration cleanup, and Git branch operations.

## 2.0.1 - 2026-07-04

Changed the gitignore scaffold to cover only pack artifacts, and moved deferred
ideas into `docs/project/features.md`. Fixed Python and release ignore rules
leaking into target repositories.

## 2.0.0 - 2026-07-04

Added `pack-manifest.json` as the single inventory. Added focused guidance for
documentation, Git, and CI/CD, explicit project-file and issue-template
scaffolding, and a release builder with sync tests. Changed `AGENTS.md` to short
core rules with task routing, moved guidance and conventions under `.agents/`,
templates to `docs/templates/`, and project docs to `docs/project/`. Branch
selection now prefers `develop`/`dev`, then `main`/`master`. Fixed templates
masquerading as live docs, the pull request template assuming Git Flow, and
unsafe paths or bad manifests not failing clearly. Removed the roadmap (future
work is in `docs/project/features.md`), forced project doc overwrite, and
`.agents/base.md`. Deprecated `--include-project-docs` for
`--scaffold-project-files`.

## 1.31.0 - 2026-07-02

Added README, changelog, and features starter templates for target repos. Fixed
repo-seed's own root docs being used as sync sources.

## 1.30.0 - 2026-06-25

Added a release workflow that builds one ZIP per profile. Added bug report and
feature request issue templates, and Unity conventions for the `game` and `full`
profiles.

## 1.29.0 - 2026-06-23

Added a `--profile` flag with `minimal`, `library`, `app`, `game`, and `full`
(the default). Changed the default base branch from `develop` to `main`.

## 1.28.0 - 2026-06-23

Changed Git guidance to present Git Flow and GitHub Flow with a decision table.
This repository uses GitHub Flow.

## 1.27.0 - 2026-06-23

Changed this repository to GitHub Flow: `main` is the only long-lived branch and
all branches target it.

## 1.26.0 - 2026-06-23

Added architecture and user-guide templates, with guidance on when to create and
update them.

## 1.25.0 - 2026-06-19

Added CI/CD guidance. CI/CD changes now need explicit task scope.

## 1.24.0 - 2026-06-19

Added guidance on useful comments and concise task and PR summaries.

## 1.23.0 - 2026-06-19

Added pre-flight checks before creating branches or pull requests, to avoid
duplicate work, and generic-example guidance for templates. The sync script now
fetches and prunes remotes during branch preparation unless skipped.

## 1.22.0 - 2026-06-19

Renamed the sync script to the stable path `scripts/sync-agent-guidelines.py`.

## 1.21.0 - 2026-06-19

Added `scripts/sync-agent-guidelines.py` with version and hash tracking and
conflict copies, plus separate Python and shell conventions. Changed branching
to strict Git Flow families `feature/*`, `release/*`, and `hotfix/*`, with
`develop` as the default integration and PR target.

## 1.20.0

Skipped. This version was not released.

## 1.19.0 - 2026-06-19

Added a branch type table, branch naming policy, and pull request policy with
fallback reporting.

## 1.18.0 - 2026-06-18

Changed the C# rule to allow single-statement guard clauses without braces.
Replaced project-specific examples with generic ones.

## 1.17.0 - 2026-06-18

Added a C# rule for a blank line after a completed control block.

## 1.16.0 - 2026-06-18

Added a rule to keep the existing style of user-facing text, such as ASCII
versus Unicode punctuation.

## 1.15.0 - 2026-06-18

Added a C# rule against inline guards such as `if (...) return ...;`.

## 1.14.0 - 2026-06-15

Added `MUST`/`SHOULD`/`MAY` strictness levels, a rule against AI tool names in
repository text, and indentation preservation guidance. Softened Git Flow and PR
wording for solo repositories.

## 1.13.0 - 2026-06-12

Added the `CLAUDE.md` wrapper for Claude Code. Softened PR wording for local
repositories.

## 1.12.0 - 2026-06-12

Baseline starter pack with `AGENTS.md`, README, changelog, features file,
`.editorconfig`, a pull request template, conventions, and FSD, TSD, and GDD
templates.
