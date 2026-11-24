# Django Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/django.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/python.md`. Repository rules, the
installed Django version, and the project's app structure take precedence. Use
the documentation for the installed release. Django's own coding style is for
contributions to Django, not a requirement for applications.

## Structure

- Follow the existing app boundaries and module layout. Do not add service
  layers or patterns the project does not use.
- Keep settings in the project's settings modules, read secrets and
  environment-specific values from the environment, and never commit secrets.

## Models and Queries

- Avoid N+1 queries: use `select_related` and `prefetch_related`, and check
  query counts for changed views.
- Use `only`, `values`, `exists`, `count`, and `iterator` where they avoid
  loading unneeded data.
- Use the ORM or parameterized `raw` and `cursor` calls. Never format user
  input into SQL strings or `extra()`.
- Use `transaction.atomic` for multi-step writes that must succeed together,
  and `select_for_update` or `F()` expressions to avoid lost updates.
- Use `transaction.on_commit` for side effects, such as tasks or emails, that
  depend on committed data.

## Migrations

- Generate migrations with `makemigrations` for every model change, and review
  them. Do not edit migrations that have already run in shared environments.
- Split schema and data changes, keep data migrations reversible where
  practical, and use historical models through `apps.get_model` in them.
- Consider locking and table rewrites for large tables.

## Views, Forms, and Security

- Validate input with forms or serializers, and use `cleaned_data` or
  validated data only.
- Enforce authentication and permissions in every view, with decorators,
  mixins, or the project's permission system. Scope querysets to the
  requesting user where data is per-user.
- Keep CSRF protection enabled, rely on template auto-escaping, and use
  `mark_safe` only for trusted, sanitized content.
- Keep production settings safe: `DEBUG` off, `ALLOWED_HOSTS` set, and secure
  cookie and HTTPS settings as the project configures them.

## Testing and Validation

- Use the project's test runner (`manage.py test` or pytest-django), with
  factories or fixtures as nearby tests do. Cover permission and validation
  failures.
- Run `manage.py check` (with `--deploy` for production settings),
  `makemigrations --check`, and the tests.

## References

- [Database access optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Security in Django](https://docs.djangoproject.com/en/stable/topics/security/)
- [Deployment checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
