# Swift Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/swift.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Swift applications, libraries, and
tools on any platform. Do not assume an Apple UI framework. Configured
swift-format or SwiftLint rules, and nearby code, take precedence.

## Compatibility and Build

- Respect the Swift tools version, language mode, and deployment targets in
  `Package.swift` or the project settings. Do not raise them or enable
  upcoming features incidentally.
- Use availability checks (`if #available`, `@available`) for APIs newer than
  the deployment target.
- Use the project's build system, such as Swift Package Manager or Xcode
  project settings, and add dependencies only when needed.

## Naming and API Design

- Follow the Swift API Design Guidelines: name for clarity at the point of use,
  read call sites as phrases, and label arguments where meaning is not obvious.
- Use `UpperCamelCase` for types and protocols and `lowerCamelCase` for
  everything else. Case acronyms uniformly, all upper or all lower by
  position (`urlString`, `userSMTPServer`).
- Name side-effect-free methods as nouns or `-ed`/`-ing` forms, and mutating
  methods as imperative verbs.

## Optionals and Errors

- Unwrap optionals with `if let`, `guard let`, or `??`. Avoid force-unwraps and
  `try!` unless failure is a programmer error with a stated invariant.
- Throw errors for recoverable failures, with specific error types, and
  propagate them with `try`. Do not discard errors with `try?` when the caller
  needs to know.

## Types and Memory

- Prefer structs and enums for value semantics, and classes when identity or
  shared mutable state is required.
- Use protocols for abstraction at real boundaries, and keep them small.
- Avoid retain cycles: capture `self` weakly or unowned in escaping closures
  stored by the object, and use `weak` delegates.

## Concurrency

- Use structured concurrency (`async`/`await`, task groups) over detached
  tasks, and support cancellation by checking `Task.isCancelled` or calling
  `Task.checkCancellation()` in long work.
- Respect actor isolation and `Sendable` checking for the project's language
  mode. Do not silence data-race diagnostics with `@unchecked Sendable` or
  `nonisolated(unsafe)` without a documented reason.
- Keep UI updates on the main actor where the platform requires it.

## Documentation and Validation

- Use Markdown and DocC conventions for required API documentation or
  caller-relevant contracts not evident from signatures and code.
- Run `swift build` and `swift test`, or the project's `xcodebuild` scheme, and
  the configured formatter and linter. Fix new compiler warnings.

## References

- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
- [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
- [Automatic Reference Counting](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/)
- [Swift 6 migration guide](https://www.swift.org/migration/documentation/migrationguide/)
- [DocC](https://www.swift.org/documentation/docc/)
