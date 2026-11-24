# Node.js Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/nodejs.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/javascript.md`, and with
`.agents/conventions/typescript.md` for TypeScript projects. Repository rules
and nearby code take precedence. Framework conventions, when selected, add to
this file.

## Runtime and Modules

- Target the Node.js versions in `engines`, `.nvmrc`, `.node-version`, or CI.
  Check API availability for the oldest supported version.
- Keep the project's module format. `"type"` in `package.json` and the `.mjs`
  and `.cjs` extensions decide whether a file is ESM or CommonJS. Do not
  convert modules between formats incidentally.
- Keep a published package's `exports` map and entry points working for its
  documented consumers.
- Import built-ins with the `node:` prefix when the project does.

## Packages and Dependencies

- Use the package manager the lock file indicates (`package-lock.json`,
  `yarn.lock`, `pnpm-lock.yaml`, or `bun.lock`), and commit lock file changes
  with the dependency change.
- Use the clean install command, such as `npm ci`, in automation.
- Add dependencies only when needed. Distinguish runtime from development
  dependencies, and check the maintenance and install scripts of new packages.
- Report known vulnerabilities with the package manager's audit command, but
  do not apply forced upgrades outside the task.

## Event Loop and I/O

- Do not block the event loop in servers or long-running processes with
  synchronous file, crypto, or compression calls, or with large CPU-bound work.
  Use async APIs, streams, or worker threads.
- Use streams with `pipeline` from `node:stream/promises` for large data, so
  errors and backpressure are handled.
- Set timeouts on outbound network calls, and bound concurrency and request
  sizes.

## Configuration and Errors

- Read configuration from environment variables or the project's config
  module, and validate it at startup. Never commit secrets or log them.
- Handle errors from every callback, promise, and `error` event. Do not use
  `uncaughtException` handlers to keep running in an unknown state.
- On `SIGTERM` and `SIGINT`, stop accepting work, finish or abort in-flight
  work within a timeout, close servers and connections, then exit.

## Security

- Do not pass untrusted input to `child_process.exec` or a shell. Use
  `execFile` or `spawn` with an argument array.
- Resolve and check user-supplied paths against an allowed root before file
  access.
- Do not deserialize untrusted data into code or objects with side effects.

## Validation

Run the project's test script, such as `npm test`, `node --test`, or the
configured runner, and its lint and type-check scripts. Use `node:test` for
new tests only when the project has no test framework.

## References

- [Node.js API documentation](https://nodejs.org/api/)
- [Modules: Packages](https://nodejs.org/api/packages.html)
- [Don't block the event loop](https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop)
- [Node.js security best practices](https://nodejs.org/learn/getting-started/security-best-practices)
- [Test runner](https://nodejs.org/api/test.html)
