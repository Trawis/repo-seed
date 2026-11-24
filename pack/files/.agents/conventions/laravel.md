# Laravel Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/laravel.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/php.md`. Repository rules, the
application's existing structure, and nearby code take precedence. Use the
documentation for the Laravel version in `composer.lock`; APIs and the default
application skeleton change between major versions.

## Structure

- Follow the existing layout and the framework's conventions for names and
  locations. Do not add repositories, service layers, actions, or other
  architectural patterns that the project does not already use.
- Generate new classes with `php artisan make:*` when it matches the project's
  layout, then adapt them to local style.
- Resolve dependencies through constructor or method injection. Prefer
  injection over facades or `app()` in classes the project tests in isolation,
  unless nearby code uses facades.
- Read configuration with `config()`. Call `env()` only in `config/` files,
  because cached configuration does not load `.env`.

## HTTP Layer

- Keep controllers thin: validate, authorize, delegate, and respond.
- Validate input with form requests or `$request->validate()`, and use only
  validated data, such as `$request->validated()`, for mass assignment.
- Authorize with policies or gates, through `authorize`, `can` middleware, or
  form request `authorize()`. Do not rely on hidden UI controls.
- Use named routes and route model binding where the project does.
- Shape API output with API resources when the project uses them, and never
  return models that expose hidden or sensitive attributes.

## Eloquent and Database

- Guard mass assignment with `$fillable` or `$guarded`, consistent with the
  model's existing approach.
- Avoid N+1 queries: eager-load relationships with `with()` or `load()`, and
  consider `Model::preventLazyLoading()` where the project enables it.
- Process large result sets with `chunkById`, `lazyById`, or cursors instead of
  loading everything.
- Wrap multi-step writes that must succeed together in `DB::transaction`.
- Use the query builder's bindings. Pass user input to `whereRaw`,
  `selectRaw`, or `DB::statement` only through bindings, and never interpolate
  it.
- Add a new migration for every schema change. Do not edit migrations that
  have already run in shared environments. Write `down()` methods when the
  project does.

## Queues, Events, and Scheduling

- Keep job payloads small and serializable. Pass model identifiers or models
  through `SerializesModels`, not large data.
- Make jobs safe to retry. Set `tries`, `backoff`, or `timeout` where failure
  behavior matters, and handle `failed()` when cleanup is needed.
- Dispatch jobs and events that depend on database changes after commit, using
  `afterCommit` or the queue's `after_commit` setting.
- Define scheduled tasks where the project's Laravel version expects them, and
  use `withoutOverlapping` or `onOneServer` when concurrent runs would conflict.

## Security

- Keep CSRF protection on state-changing web routes, and escape Blade output
  with `{{ }}`. Use `{!! !!}` only for trusted, sanitized HTML.
- Keep secrets in environment configuration, never in committed config or code,
  and never enable `APP_DEBUG` in production.
- Store uploads through the filesystem abstraction and validate type and size.

## Testing and Validation

- Run the project's test command, such as `php artisan test`, Pest, or PHPUnit.
  Use database refresh traits, factories, and fakes (`Queue::fake()`,
  `Event::fake()`, `Http::fake()`) as nearby tests do.
- Cover authorization and validation failures as well as success paths.
- Run Pint with `--test` when the project configures it, and Larastan or PHPStan
  at the configured level when present.

## References

- [Laravel documentation](https://laravel.com/docs)
- [Authorization](https://laravel.com/docs/authorization) and [Validation](https://laravel.com/docs/validation)
- [Eloquent relationships](https://laravel.com/docs/eloquent-relationships)
- [Queues](https://laravel.com/docs/queues)
- [Laravel Pint](https://laravel.com/docs/pint)
