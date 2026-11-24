# C++ Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/cpp.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers C++ libraries and applications.
Configured formatters, clang-tidy checks, compiler flags, and nearby code take
precedence. Use `.agents/conventions/c.md` for C code.

## Compatibility and Build

- Target the C++ standard, compilers, and platforms the build declares, such
  as `CMAKE_CXX_STANDARD`. Apply only guidance and library features available
  in that standard.
- Use the existing build system and package manager. Do not migrate either
  incidentally.
- Keep exported headers, class layouts, and inline functions compatible when
  the project promises ABI stability.
- Respect project constraints such as disabled exceptions or RTTI, embedded
  targets, or banned standard headers.

## Style

- Follow the configured formatter and naming rules. Without them, match nearby
  code.
- Use namespaces for library code. Do not put `using namespace` in headers.
- Prefer `enum class`, `constexpr`, and `const` to macros and plain enums in
  new code.

## Resources and Ownership

- Manage resources with RAII. Do not use raw `new` and `delete` in new code;
  use `std::unique_ptr`, `std::make_unique`, containers, or the project's
  owning types.
- Use `std::shared_ptr` only for real shared ownership. Pass non-owning
  references or raw pointers to functions that do not take ownership.
- Follow the rule of zero; when a class must manage a resource, define or
  delete all five special members consistently.
- Do not return or store references, pointers, views (`std::string_view`,
  `std::span`), or iterators that outlive the object they refer to.

## Types and Interfaces

- Mark everything `const` that does not change, including member functions.
- Make single-argument constructors `explicit` unless conversion is intended.
- Use `override` on overriding functions, and give polymorphic base classes a
  virtual or protected destructor.
- Constrain templates with concepts or `static_assert` where the standard
  allows, and keep template code readable.

## Errors and Concurrency

- Use the project's error model: exceptions, error codes, or `std::expected`.
  Throw by value, catch by reference, and do not let exceptions escape
  destructors.
- Avoid undefined behavior: out-of-bounds access, dangling references, signed
  overflow, data races, and use of moved-from objects beyond valid operations.
- Protect shared data with mutexes held through `std::scoped_lock` or
  `std::lock_guard`, or use atomics; join or stop every thread you start.

## Documentation and Validation

- Document public APIs in headers: ownership, lifetime, thread safety,
  preconditions, and errors. Use Doxygen syntax when the project does.
- Build with the project's warning flags and fix new warnings. Run tests,
  configured clang-tidy checks, and sanitizers (AddressSanitizer,
  UndefinedBehaviorSanitizer, ThreadSanitizer) when available.

## References

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)
- [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- [Doxygen documentation blocks](https://www.doxygen.nl/manual/docblocks.html)
