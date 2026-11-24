# Ruby Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/ruby.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers Ruby libraries, applications, and
scripts. Framework conventions, such as Rails, add to this file. Configured
RuboCop or Standard rules and nearby code take precedence; the community Ruby
Style Guide is an optional baseline.

## Compatibility and Dependencies

- Target the Ruby versions in `.ruby-version`, the `Gemfile`, the gemspec's
  `required_ruby_version`, or CI. Do not use syntax or core APIs newer than the
  minimum.
- Manage dependencies with Bundler. Add gems only when needed, and commit
  `Gemfile.lock` changes with them when the project tracks it.
- Keep a published gem's public API compatible with its version.

## Style and Naming

- Use `snake_case` for methods, variables, and files, `CamelCase` for classes
  and modules, and `SCREAMING_SNAKE_CASE` for constants.
- End predicate methods with `?`, and reserve `!` for methods with a safer
  counterpart, such as mutating or raising variants.
- Add `# frozen_string_literal: true` to new files when the project uses it.

## Idioms and Design

- Use `Enumerable` methods (`map`, `select`, `each_with_object`) and blocks
  instead of manual index loops, and keep blocks short.
- Keep classes small with clear public interfaces; mark helpers `private`.
- Do not monkey-patch core classes or other libraries. Use refinements or
  wrapper objects when the project accepts them.
- Avoid `method_missing` and `send` with untrusted method names; prefer
  `public_send` and explicit methods.

## Errors and Safety

- Raise specific exceptions that inherit from `StandardError`, with clear
  messages. Rescue specific classes; do not rescue `Exception` or use bare
  `rescue` that hides failures.
- Use `ensure` or block forms (`File.open { }`) to release resources.
- Do not `eval`, `instance_eval`, or `Marshal.load` untrusted input, and use
  `YAML.safe_load` for untrusted YAML.
- Pass arguments to `system` and `Open3` as separate strings, not a single
  interpolated shell command.

## Documentation and Validation

- Document public classes and methods with YARD or RDoc, as the project does.
- Run the configured linter and tests, such as `bundle exec rubocop` and
  `bundle exec rspec` or `rake test`.

## References

- [Ruby documentation](https://www.ruby-lang.org/en/documentation/)
- [Ruby Style Guide](https://rubystyle.guide/) (an optional style baseline)
- [Bundler](https://bundler.io/)
- [YARD](https://yardoc.org/)
