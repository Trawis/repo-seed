# Rails Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/rails.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/ruby.md`. Repository rules, the
installed Rails version, and the application's existing structure take
precedence. Use the Rails Guides for the installed version. Do not add gems,
service layers, or architectural patterns the project does not already use.

## Structure and Routing

- Follow Rails naming and file conventions so autoloading (Zeitwerk) resolves
  constants. Generate files with `bin/rails generate` when it matches the
  project's layout.
- Prefer resourceful routes, and keep controllers thin: authorize, permit
  parameters, delegate, and render.
- Read configuration from `config/` and credentials or environment variables.
  Never commit secrets or the master key.

## Parameters and Authorization

- Permit attributes explicitly with strong parameters (`params.expect` or
  `params.require(...).permit(...)`, depending on the Rails version). Never
  mass-assign unfiltered params.
- Authorize every action with the project's mechanism, and scope record
  lookups to the current user where data is per-user, for example
  `current_user.posts.find(id)`.

## Models and Queries

- Avoid N+1 queries with `includes`, `preload`, or `eager_load`; process large
  sets with `find_each` or `in_batches`.
- Use query interface placeholders for conditions. Never interpolate input
  into `where`, `order`, or `find_by_sql` strings.
- Back model validations with database constraints for uniqueness and
  required data.
- Keep callbacks for persistence concerns, and document non-obvious ones.
  Avoid callbacks with external side effects; use `after_commit` when they are
  needed.
- Wrap multi-record writes that must succeed together in a transaction.

## Migrations

- Add a new migration for each schema change, and do not edit migrations that
  have run in shared environments. Commit the updated `schema.rb` or
  `structure.sql`.
- Preserve data and stage destructive changes; consider locks, defaults, and
  index creation on large tables.
- Keep migrations reversible, with `change` or explicit `up` and `down`.

## Jobs and Views

- Pass identifiers or Global ID records to jobs, not large objects, and make
  jobs idempotent and retry-safe.
- Rely on ERB escaping; use `html_safe` and `raw` only for trusted, sanitized
  content. Keep CSRF protection enabled.

## Testing and Validation

- Use the project's framework (Minitest or RSpec), fixtures or factories as
  nearby tests do, and cover authorization and validation failures.
- Run the tests and the configured RuboCop and Brakeman checks.

## References

- [Rails Guides](https://guides.rubyonrails.org/)
- [Action Controller overview](https://guides.rubyonrails.org/action_controller_overview.html)
- [Active Record migrations](https://guides.rubyonrails.org/active_record_migrations.html)
- [Active Job basics](https://guides.rubyonrails.org/active_job_basics.html)
- [Securing Rails applications](https://guides.rubyonrails.org/security.html)
- [Testing Rails applications](https://guides.rubyonrails.org/testing.html)
