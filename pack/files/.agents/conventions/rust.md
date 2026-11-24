# Rust Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/rust.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Rust libraries, applications, and
tools. Configured `rustfmt.toml`, Clippy lints, `deny` or `allow` attributes,
and nearby code take precedence. For command-line tools, also use
`.agents/conventions/scripts.md`.

## Compatibility and Cargo

- Respect the crate's `edition`, its `rust-version` (MSRV), and any
  `rust-toolchain.toml`. Do not use language features or standard-library APIs
  newer than the MSRV.
- Add dependencies only when needed, with the existing workspace dependency
  and feature conventions. Keep default features minimal for libraries.
- Commit `Cargo.lock` changes with dependency changes when the project tracks
  it. Do not edit the lock file by hand.
- Keep a published crate's public API semver-compatible unless the task is a
  breaking release.

## Style and Naming

- Format with `rustfmt`. Use `snake_case` for functions, variables, and
  modules, `UpperCamelCase` for types and traits, and `SCREAMING_SNAKE_CASE`
  for constants and statics.
- Follow the API Guidelines' conversion names (`as_`, `to_`, `into_`) and
  getter style (no `get_` prefix for simple getters).
- Keep items private by default, and expose a deliberate public API.

## Ownership and Types

- Borrow instead of cloning when the caller keeps ownership. Do not add
  `.clone()` only to satisfy the borrow checker without considering the cost
  and semantics.
- Accept the most general reasonable input (`&str`, `&[T]`, `impl AsRef<Path>`)
  and return owned or concrete types.
- Let lifetimes be elided where possible. Name them only when needed.
- Use `Option` for absence and `Result` for recoverable failure; encode
  invariants in types rather than comments where practical.

## Errors

- Propagate errors with `?`, and add context at boundaries. Libraries should
  return typed errors; applications may use the project's error-reporting
  crate.
- Do not `unwrap` or `expect` on values that can fail at runtime, outside tests
  and proven invariants. Give `expect` a message stating the invariant.
- Reserve `panic!` for bugs, not for invalid input.

## Concurrency and Unsafe

- Share state across threads with `Arc` plus `Mutex`, `RwLock`, or atomics, or
  with channels. Do not hold a lock across an `.await` in async code.
- In async code, use the project's runtime, avoid blocking calls on runtime
  threads, and make cancellation safe.
- Avoid `unsafe` unless it is required and justified. Keep each `unsafe` block
  minimal, document the invariants it relies on in a `// SAFETY:` comment, and
  document a `# Safety` section on every `unsafe fn`.

## Documentation and Validation

- Write rustdoc comments for public items, with `# Errors`, `# Panics`, and
  `# Safety` sections where they apply, and runnable examples where useful.
- Run `cargo fmt --check`, `cargo clippy` with the project's targets and
  features, and `cargo test`, which includes doctests. Check the MSRV build
  when CI does.

## References

- [Rust Style Guide](https://doc.rust-lang.org/style-guide/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Cargo: the `rust-version` field](https://doc.rust-lang.org/cargo/reference/rust-version.html)
- [rustdoc documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html)
- [Clippy](https://doc.rust-lang.org/clippy/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/) (for `unsafe` code)
