# C Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/c.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers C libraries, applications, and
firmware. Configured formatters, static analyzers, compiler flags, and nearby
code take precedence. Use `.agents/conventions/cpp.md` for C++ code.

## Compatibility and Build

- Target the C standard, compilers, and platforms the build declares, such as
  `-std=c11` or CMake's `C_STANDARD`. Do not use newer features or compiler
  extensions the project does not already use.
- Use the existing build system. Do not migrate build systems or standards
  incidentally.
- Keep public headers and struct layouts compatible when the project ships a
  stable ABI.

## Style and Headers

- Follow the configured formatter, such as clang-format. Without one, match
  nearby code.
- Follow the project's naming and prefixes; prefix public symbols to avoid
  collisions. Give internal functions and file-level data `static` linkage.
- Give every header an include guard or `#pragma once`, as the project does,
  and make it include what it uses.
- Prefer `const`, `enum`, and `static inline` functions to macros where they
  suffice; parenthesize macro arguments and bodies.

## Memory and Bounds

- Pair every allocation with one clear owner and release path, and document
  who frees returned pointers.
- Check allocation and I/O results. Set freed pointers to `NULL` where they can
  be reused.
- Pass buffer sizes with buffers, and check bounds before writing. Use
  size-limited functions correctly, and do not use `gets` or unbounded
  `sprintf` or `strcpy`.
- Do not return pointers to automatic storage, and do not read uninitialized
  memory.

## Integers and Undefined Behavior

- Check for overflow before arithmetic on untrusted or size values, and use
  `size_t` for sizes and indexes.
- Watch signed-to-unsigned conversions, integer promotion, and shifts by the
  type width or more.
- Avoid undefined behavior, including signed overflow, strict-aliasing
  violations, unsequenced modifications, and out-of-bounds pointer arithmetic.

## Errors

- Report errors through return values or the project's error convention, and
  check them at every call site.
- Release acquired resources on every error path, for example with a single
  cleanup label where the project uses `goto` cleanup.
- Check `errno` only after a call that reports failure.

## Documentation and Validation

- Document public header contracts when callers need information about
  preconditions, ownership, buffer sizes, or errors not evident from code.
  Use Doxygen syntax when required by the project.
- Build with the project's warning flags and fix new warnings. Run tests, and
  run them under sanitizers (AddressSanitizer, UndefinedBehaviorSanitizer)
  and configured static analyzers when available.

## References

- [SEI CERT C Coding Standard](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/)
- [GCC warning options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)
- [Clang sanitizers: AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
  and [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
- [OpenSSF compiler options hardening guide](https://best.openssf.org/Compiler-Hardening-Guides/Compiler-Options-Hardening-Guide-for-C-and-C++.html)
