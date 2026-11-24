# Lua Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/lua.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Lua in any host: standalone
interpreters, LuaJIT, embedded engines, editors, or games. Configured
formatters such as StyLua, linters such as Luacheck or Selene, and nearby code
take precedence; Lua has no universal formatting standard.

## Version and Host

- Identify the Lua version or dialect the host runs, such as Lua 5.1 through
  5.4, LuaJIT, or Luau, and use only its features. `goto`, integer division,
  `<close>` variables, and `table.unpack` versus `unpack` differ between them.
- Use the host's APIs and sandbox rules. Do not assume standard libraries such
  as `io`, `os`, or `debug` exist in an embedded host.

## Scope and Naming

- Declare variables `local`. Do not create globals except where the host
  requires them, and keep module state local to the module.
- Follow the project's naming scheme. Without one, match nearby code; a leading
  underscore conventionally marks unused or private names.

## Tables and Modules

- Write modules that return a table, and load them with `require`. Do not
  rely on `module()` or global side effects.
- Remember that arrays are 1-based by convention, and that `#` is unreliable on
  tables with holes. Track lengths explicitly when holes are possible.
- Use `pairs` for maps and `ipairs` for sequences, and do not depend on
  `pairs` iteration order.
- Use metatables and `__index` for classes or defaults only when nearby code
  does, and keep the pattern consistent.

## Errors and Resources

- Report expected failures as `nil, message` returns or with `error`, following
  the module's convention, and handle them at call sites.
- Use `pcall` or `xpcall` around calls that may raise when the caller can
  recover, and do not silently discard the error.
- Close files and host resources explicitly, or with `<close>` variables where
  the version supports them.
- Do not `load` or `loadstring` untrusted code without a restricted
  environment.

## Coroutines and Performance

- Resume coroutines only in valid states, check `coroutine.resume` results, and
  avoid yielding across C or host boundaries that do not allow it.
- In hot loops, cache frequently used globals and table lookups in locals, and
  avoid creating tables or closures per iteration, when profiling shows a
  need.

## Documentation and Validation

- Document module APIs with LDoc or the annotation style the project uses,
  such as LuaLS annotations.
- Run the configured formatter, linter, and tests, such as busted or the
  host's test runner.

## References

- [Lua reference manuals](https://www.lua.org/manual/) (choose the target
  version)
- [Programming in Lua](https://www.lua.org/pil/) (the online first edition
  covers Lua 5.0)
- [Luau](https://luau.org/) (for Roblox and other Luau hosts)
