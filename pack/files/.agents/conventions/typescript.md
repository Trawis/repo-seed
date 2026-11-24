# TypeScript Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/typescript.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/javascript.md`. Repository rules,
`tsconfig.json`, configured typescript-eslint rules, and nearby code take
precedence. Runtime and framework conventions, when selected, add to this file.

## Compiler and Compatibility

- Respect the project's `tsconfig.json`, including `strict`, `target`,
  `module`, and `moduleResolution`. Do not loosen compiler options to make code
  compile.
- Use only TypeScript features supported by the project's installed version and
  build tool. Some tools strip types without type checking and reject
  constructs such as `enum` or `namespace`; follow the project's settings.

## Types

- Do not use `any` in new code. Use `unknown` for values of unknown shape and
  narrow them before use.
- Narrow with `typeof`, `instanceof`, `in`, discriminated unions, and type
  predicates. Prefer narrowing to type assertions.
- Avoid `as` assertions and non-null `!` assertions that the code does not
  prove. Never use double assertions such as `as unknown as T` to silence
  errors.
- Do not suppress errors with `@ts-ignore`. When a suppression is unavoidable,
  use `@ts-expect-error` with a comment explaining why.
- Keep generics purposeful: add a type parameter only when it relates inputs
  and outputs. Constrain it with `extends` when needed.
- Annotate exported function signatures and public types explicitly. Let
  inference handle local variables.
- Use `readonly` and `as const` for data that must not change.

## Boundaries

- Static types do not validate runtime data. Validate input from HTTP, files,
  environment variables, storage, and message queues at the boundary, with
  the project's validation library or explicit checks, before treating it as a
  typed value.
- Handle `catch` variables as `unknown`, and narrow before reading properties.

## Documentation and Validation

- Document exported APIs with TSDoc or JSDoc comments following the project's
  style. Describe behavior and constraints; do not repeat types already in the
  signature.
- Run the project's type check, such as `tsc --noEmit` or its build script,
  plus its lint and test scripts.

## References

- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TSConfig reference](https://www.typescriptlang.org/tsconfig/)
- [typescript-eslint](https://typescript-eslint.io/)
- [TSDoc](https://tsdoc.org/)
- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
  (an optional style baseline)
