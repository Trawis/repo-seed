# Go Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/go.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Go libraries, services, and
command-line tools; for CLIs, also use `.agents/conventions/scripts.md`.
Configured linters, such as golangci-lint, and nearby code take precedence.

## Compatibility and Modules

- Respect the `go` and `toolchain` lines in `go.mod`. Do not use language
  features or standard-library APIs newer than the declared version.
- Add dependencies only when needed. Keep `go.mod` and `go.sum` tidy with
  `go mod tidy`, and do not edit `go.sum` by hand or vendor code unless the
  project vendors.
- Keep a published module's import path and exported API compatible; a
  breaking change needs a new major version path.

## Style and Naming

- Format with `gofmt` (or `goimports` where configured). Formatting is not a
  style choice in Go.
- Use `MixedCaps`; keep initialisms uniform (`URL`, `ID`). Keep names short in
  small scopes and descriptive for exported identifiers.
- Name packages with short lowercase words, without `util` or `common`, and do
  not repeat the package name in exported names (`http.Client`, not
  `http.HTTPClient`).
- Write doc comments for every exported identifier, starting with its name.

## Errors

- Return errors as the last result and check them. Do not discard errors with
  `_` unless the reason is documented.
- Wrap with context using `fmt.Errorf("...: %w", err)`, and inspect with
  `errors.Is` and `errors.As`, not string comparison.
- Keep error strings lowercase without trailing punctuation.
- Use `panic` only for programmer errors, not for expected failures.

## Interfaces and APIs

- Define interfaces where they are consumed, keep them small, and return
  concrete types.
- Pass `context.Context` as the first parameter of functions that do I/O or may
  block, and do not store it in structs.
- Make the zero value useful where practical.

## Concurrency and Resources

- Give every goroutine a clear owner and exit condition, usually a context or
  channel close. Do not start goroutines that can leak.
- Protect shared state with a mutex or confine it to one goroutine; do not copy
  values that contain a mutex.
- Close what you open, using `defer` right after a successful acquisition, and
  check errors from `Close` on writes.
- Set timeouts on network clients and servers; the zero-value `http.Client` and
  `http.Server` have none.

## Testing and Validation

- Use table-driven tests with `t.Run` where they clarify cases, and `t.Helper`
  in helpers.
- Run `go vet` and `go test ./...`, plus `go test -race` for concurrent code
  when the platform supports it. Run the configured linter.

## References

- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- [Go doc comments](https://go.dev/doc/comment)
- [Effective Go](https://go.dev/doc/effective_go) (core idioms; not updated for
  modules or generics)
- [Managing dependencies](https://go.dev/doc/modules/managing-dependencies)
- [Data race detector](https://go.dev/doc/articles/race_detector)
