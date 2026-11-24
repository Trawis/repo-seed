# Kotlin Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/kotlin.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Kotlin on any platform: JVM,
Android, multiplatform, or native. Do not assume Android or a particular build
tool. Configured ktlint, detekt, or IDE formatter settings, and nearby code,
take precedence. Framework conventions, when selected, add to this file.

## Compatibility and Build

- Target the Kotlin version, `jvmTarget`, and platform versions the build
  declares. Do not use language features or library APIs newer than they
  allow, and do not enable experimental or opt-in APIs incidentally.
- Use the existing build tool, wrapper, and dependency catalog.

## Style and Naming

- Follow the configured formatter. Without one, follow the official Kotlin
  coding conventions and match nearby code.
- Use `UpperCamelCase` for classes and objects, `lowerCamelCase` for functions
  and properties, and `UPPER_SNAKE_CASE` for `const val` and top-level
  immutable constants.
- Prefer `val` over `var`, and read-only collection types in public APIs.
- Use expression bodies, `when`, and scope functions where they make code
  clearer, not to compress it.

## Null Safety and Types

- Model absence with nullable types. Avoid `!!`; use safe calls, `?:`, early
  returns, or `requireNotNull` and `checkNotNull` with a message.
- Annotate or check values from Java APIs, whose platform types have unknown
  nullness.
- Use `data class` for value-like types, `sealed` hierarchies for closed sets
  of states, and exhaustive `when` without an `else` branch over them.
- Write extension functions for behavior that reads naturally on the receiver,
  and keep them close to their use; do not hide side effects in them.

## Errors and Coroutines

- Throw specific exceptions, or use the project's result type. Do not catch
  `Throwable` or `Exception` broadly.
- Follow structured concurrency: launch coroutines in a scope tied to the
  owner's lifecycle, never `GlobalScope`, and do not leak jobs.
- Do not swallow `CancellationException`; rethrow it when catching broad
  exceptions in suspending code.
- Keep suspending functions main-safe: move blocking or CPU-heavy work to an
  appropriate dispatcher with `withContext`.
- Use `Flow` for streams, collected within a lifecycle-aware scope.

## Java Interoperability

- When Java code calls Kotlin APIs, use `@JvmStatic`, `@JvmOverloads`, and
  `@Throws` where the project's Java callers need them.

## Documentation and Validation

- Write KDoc for public APIs: behavior, parameters, return values, and thrown
  exceptions.
- Run the build's compile, test, and configured lint tasks, such as
  ktlint or detekt, and fix new compiler warnings.

## References

- [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- [Null safety](https://kotlinlang.org/docs/null-safety.html)
- [Coroutines basics](https://kotlinlang.org/docs/coroutines-basics.html)
  and [Cancellation and timeouts](https://kotlinlang.org/docs/cancellation-and-timeouts.html)
- [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- [KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
