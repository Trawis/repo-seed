# Dart Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/dart.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Dart packages, applications, and
tools. Framework conventions, such as Flutter, add to this file. The project's
`analysis_options.yaml` lints and nearby code take precedence.

## Compatibility and Dependencies

- Respect the SDK constraint in `pubspec.yaml`. Do not use language features
  newer than its lower bound allows.
- Add dependencies only when needed, with `dart pub add` or the project's
  workflow. Commit `pubspec.lock` for applications when the project tracks it.
- Keep a published package's public API compatible with its version, and
  update its changelog when the project does.

## Style and Naming

- Format with `dart format`.
- Use `UpperCamelCase` for types and extensions, `lowerCamelCase` for members,
  variables, and constants, and `lowercase_with_underscores` for libraries,
  packages, directories, and files.
- Prefix private members and declarations with `_`. Prefer relative imports
  within a package's `lib/` when the project does.

## Types and Null Safety

- Use sound null safety: declare nullable types only where `null` is a valid
  value. Avoid `!` unless the code proves the value is non-null.
- Use `late` only when a value is guaranteed to be initialized before use.
- Annotate public APIs with explicit types, and let inference handle locals.
  Avoid `dynamic` unless the value is truly untyped.
- Prefer `final` for variables that are not reassigned, and `const`
  constructors and values where possible.

## Async and Errors

- Await or deliberately handle every `Future`; mark intentional
  fire-and-forget calls with `unawaited`.
- Cancel `StreamSubscription`s and close `StreamController`s you own.
- Throw `Exception` subtypes for runtime failures and `Error` subtypes only for
  programmer errors. Do not catch `Error`, and do not use bare `catch` blocks
  that hide failures; use `on` clauses for expected exception types.

## Documentation and Validation

- Write `///` doc comments for public APIs, starting with a one-sentence
  summary, per Effective Dart.
- Run `dart analyze`, `dart format --output=none --set-exit-if-changed`, and
  `dart test`, or the project's equivalents.

## References

- [Effective Dart](https://dart.dev/effective-dart)
- [Sound null safety](https://dart.dev/null-safety)
- [Customizing static analysis](https://dart.dev/tools/analysis)
- [Asynchronous programming](https://dart.dev/libraries/async/async-await)
