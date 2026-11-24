# Java Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/java.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Java libraries and applications.
Framework conventions, such as Spring Boot, add to this file. Configured
formatters, Checkstyle, Error Prone, SpotBugs, or other analyzers, and nearby
code, take precedence over these defaults.

## Compatibility and Build

- Target the Java release the build declares (`maven.compiler.release`,
  Gradle toolchains, or CI). Do not use language features or APIs newer than
  that release.
- Use the project's build tool and wrapper (`./mvnw` or `./gradlew`). Add
  dependencies only when needed, through the existing dependency management
  or version catalog.

## Style and Naming

- Follow the configured formatter. Without one, match nearby code; the Google
  Java Style Guide is an optional baseline.
- Use `UpperCamelCase` for types, `lowerCamelCase` for methods, fields, and
  variables, `UPPER_SNAKE_CASE` for constants, and lowercase package names.
- Keep one top-level type per file, and avoid wildcard imports.
- Keep visibility as narrow as practical, and do not expose mutable internal
  collections.

## Types and Nulls

- Use generics without raw types, and avoid unchecked casts. Suppress an
  unchecked warning only on the narrowest declaration, with a reason.
- Follow the project's nullness annotations where present. Validate required
  arguments with `Objects.requireNonNull` at public boundaries.
- Use `Optional` for return values that may be absent, not for fields or
  parameters.
- Use records, sealed types, and pattern matching only when the target release
  supports them and nearby code does.
- Implement `equals` and `hashCode` together, consistently with each other.

## Exceptions and Resources

- Throw specific exceptions, and keep the cause when wrapping. Do not catch
  `Exception` or `Throwable` without rethrowing or reporting it.
- Do not swallow `InterruptedException`; restore the interrupt status or
  propagate it.
- Close resources with try-with-resources.
- Use parameterized queries and safe deserialization; never deserialize
  untrusted data with Java serialization.

## Concurrency

- Prefer `java.util.concurrent` executors and utilities to raw threads, and
  shut executors down.
- Guard shared mutable state with one documented mechanism, or make it
  immutable.
- Use virtual threads only when the target release and the project's libraries
  support them.

## Documentation and Validation

- Write Javadoc for public types and members of libraries and shared APIs:
  behavior, parameters, return values, and thrown exceptions.
- Run the build's test and check tasks, such as `./mvnw verify` or
  `./gradlew check`, with JUnit or the configured framework. Fix new compiler
  warnings.

## References

- [Java SE documentation](https://docs.oracle.com/en/java/javase/)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
  (an optional style baseline)
