# SQL Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/sql.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers SQL in application code, migrations,
and database scripts. Language and framework conventions cover how code calls
the database. Use the documentation for the project's actual database engine
and version; syntax, null handling, locking, and isolation differ between
engines.

## Style

- Follow the configured formatter or SQLFluff dialect and rules. Without one,
  match nearby SQL.
- Follow the schema's existing naming scheme for tables, columns, constraints,
  and indexes. Do not rename existing objects incidentally.
- List columns explicitly in application queries and `INSERT` statements
  rather than using `SELECT *` or positional inserts.
- Use explicit `JOIN ... ON` syntax and qualify columns with table aliases in
  multi-table queries.

## Correctness

- Remember three-valued logic: `NULL = NULL` is not true. Use `IS NULL`,
  `IS DISTINCT FROM`, or `COALESCE` as the engine supports, and beware
  `NOT IN` with a subquery that can return `NULL`.
- Do not rely on row order without `ORDER BY`. Add a unique tiebreaker to
  ordering used for pagination.
- Check that joins cannot multiply rows unexpectedly, especially before
  aggregation.
- Enforce invariants with constraints (`NOT NULL`, `UNIQUE`, foreign keys,
  `CHECK`) where the schema owns them, not only in application code.

## Safety

- Pass values as bound parameters. Never concatenate or interpolate untrusted
  input into SQL. Allow-list identifiers such as sort columns when they must be
  dynamic.
- Wrap multi-statement changes that must succeed together in a transaction,
  and keep transactions short.
- Use the isolation level and locking (`SELECT ... FOR UPDATE`, optimistic
  version checks) that the concurrency case requires.
- Grant application roles only the privileges they need.
- Guard bulk `UPDATE` and `DELETE` statements with a `WHERE` clause, and check
  the affected row count when it matters.

## Migrations

- Use the project's migration tool. Add a new migration for each change; do not
  edit migrations that have already run in shared environments.
- Preserve data: migrate or back-fill it before dropping or narrowing columns,
  and split destructive changes into steps that existing code can survive.
- Account for locks and long rewrites on large tables, using the engine's
  online or concurrent options where available.
- Provide a down migration or a written recovery plan, following the project's
  practice, and note irreversible steps.

## Performance and Validation

- Support frequent filters, joins, and sorts with indexes, and weigh their write
  cost. Back performance claims with the engine's query plan, such as
  `EXPLAIN`, on representative data.
- Run the project's SQL linter and migrations against a real or containerized
  database of the target engine when the project's tests do. Do not treat a
  different engine, such as SQLite in place of PostgreSQL, as proof.
- Comment non-obvious invariants, locking assumptions, and data-migration steps.

## References

- [PostgreSQL SQL language reference](https://www.postgresql.org/docs/current/sql.html)
  (one dialect, not the SQL standard)
- [PostgreSQL: Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [SQLFluff](https://docs.sqlfluff.com/en/stable/)
