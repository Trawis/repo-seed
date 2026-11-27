# PHP Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/php.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers PHP libraries and applications.
Framework conventions, such as Laravel, add to this file. Configured tools,
such as PHP-CS-Fixer, PHP_CodeSniffer, Pint, PHPStan, or Psalm, and nearby
code take precedence over these defaults.

## Compatibility and Dependencies

- Target the PHP versions in `composer.json` (`require.php`), CI, and the
  platform config. Do not use syntax or functions newer than the minimum.
- PHP compatibility is independent of any framework. Keep framework-neutral
  libraries and vanilla applications usable on their supported runtimes; do
  not add Laravel or raise the minimum merely to match another project.
- Manage dependencies with Composer. Change `composer.json` only when the task
  requires it, and commit the matching `composer.lock` when the project tracks
  it. Do not edit `vendor/`.
- Follow the project's PSR-4 autoload mapping: one class per file, with the
  namespace and path matching the mapping.

## Style and Naming

- Follow the configured standard. Without one, use PER Coding Style, which
  extends PSR-12 for newer PHP syntax.
- Use `StudlyCaps` for classes, interfaces, traits, and enums, `camelCase` for
  methods and properties, and `UPPER_CASE` for class constants, unless the
  project differs.
- Add `declare(strict_types=1);` to new files only when the project already
  uses it. It changes how scalar arguments are coerced.
- Omit the closing `?>` tag in PHP-only files.

## Types and APIs

- Declare parameter, return, and property types where the minimum PHP version
  supports them. Prefer `?Type` or union types to undocumented `mixed`.
- Use `readonly` properties, enums, and constructor promotion only when
  supported and consistent with nearby code.
- Use PHPDoc for essential information native types cannot express, such as
  array shapes, generics, or thrown exceptions, and required API documentation.
  Do not repeat native types.
- Use strict comparison (`===`, `!==`, `in_array(..., true)`) unless loose
  comparison is intended.

## Errors and Security

- Throw specific exceptions, extending SPL or project exception types. Do not
  suppress errors with `@` or catch `Throwable` without rethrowing or reporting.
- Preserve the cause with the `$previous` argument when wrapping exceptions.
- Use prepared statements or the project's query builder; never concatenate
  input into SQL.
- Escape output for its context (HTML, attributes, JavaScript, URLs). Do not
  pass user input to `unserialize`, `eval`, `include`, or shell functions; use
  `escapeshellarg` when a shell is unavoidable.
- Use `password_hash` and `password_verify` for passwords and `random_bytes` or
  `random_int` for secrets and tokens.

## Reusable Components

Use [project-seeds](https://github.com/Trawis/project-seeds) for optional
starter foundations and [project-plugins](https://github.com/Trawis/project-plugins)
for optional components, when available. Select and verify compatible source
versions at development or build time. The consuming application owns its
routes, authentication, storage, configuration, installation and dependencies.
Do not download executable components during installation or make these
repositories runtime dependencies.

## Validation

Run the project's configured test runner (PHPUnit or Pest), static analyzer,
and formatter in check mode, for example `composer test` or the scripts in
`composer.json`. Use `php -l` for a quick syntax check. Do not reformat files
outside the change or raise the static-analysis level incidentally.

## References

- [PER Coding Style](https://www.php-fig.org/per/coding-style/)
- [PSR-12](https://www.php-fig.org/psr/psr-12/) and [PSR-4](https://www.php-fig.org/psr/psr-4/)
- [PHP manual](https://www.php.net/manual/en/)
- [PHPDoc reference](https://docs.phpdoc.org/guide/references/phpdoc/index.html)
- [PHPStan](https://phpstan.org/user-guide/getting-started) and [Psalm](https://psalm.dev/docs/)
