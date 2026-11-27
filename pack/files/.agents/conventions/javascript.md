# JavaScript Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/javascript.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers JavaScript language practice for any
runtime. Runtime, TypeScript, and framework conventions, when selected, add to
this file. Configured ESLint, Prettier, or other tools, and nearby code, take
precedence over these defaults.

## Compatibility

- Use only syntax and APIs supported by the project's targets: its
  `browserslist`, transpiler or bundler settings, or `engines` field. Do not
  add polyfills or raise targets incidentally.
- Keep the project's module system. Do not mix `import` and `require` in one
  module unless the project already does.

## Style and Naming

- Follow the configured formatter and linter. Without one, match nearby code.
- Use `camelCase` for variables and functions, `PascalCase` for classes and
  constructors, and `UPPER_SNAKE_CASE` only for true constants, unless the
  project differs.
- Use `const` by default and `let` when reassignment is needed. Do not use
  `var` in new code.
- Prefer named exports when the project has no established default-export
  pattern.

## Correctness

- Use `===` and `!==`. Rely on `== null` only where the project uses it to
  match both `null` and `undefined`.
- Watch for coercion: `+`, truthiness checks that reject `0` or `""`, and
  `parseInt` without a radix. Use `??` and `?.` when only `null` and
  `undefined` should fall through.
- Do not mutate arguments, shared module state, or built-in prototypes unless
  that is the documented contract.
- Compare numbers with care: use `Number.isNaN`, integer-safe ranges, or
  `BigInt` where precision matters.

## Async and Errors

- Await or return every promise. Do not leave floating promises; handle
  rejections where the work starts.
- Use `try`/`catch` with `await`, and throw `Error` objects, not strings.
  Preserve the cause with `new Error(message, { cause })` where supported.
- Run independent async work with `Promise.all` or `Promise.allSettled`, not
  sequential awaits in a loop, when ordering does not matter.
- Support cancellation with `AbortSignal` where the APIs used accept one.

## Security

- Do not use `eval`, `new Function`, or string arguments to `setTimeout`.
- In browser code, insert untrusted text with `textContent` or framework
  escaping, never `innerHTML`, and validate URLs before use in links or
  redirects.
- Guard object merges and lookups with untrusted keys against prototype
  pollution, for example with `Object.hasOwn`, `Map`, or null-prototype objects.

## Documentation and Validation

- Use JSDoc for required documentation or caller-relevant contracts not evident
  from code.
- Run the project's configured lint, format check, and test scripts from
  `package.json`. Do not add new tools or rules incidentally.

## References

- [MDN JavaScript reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
  (an optional style baseline)
- [JSDoc](https://jsdoc.app/)
- [ESLint](https://eslint.org/docs/latest/)
