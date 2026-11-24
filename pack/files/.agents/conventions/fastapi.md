# FastAPI Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/fastapi.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/python.md`. Repository rules, the
installed FastAPI and Pydantic versions, and the application's existing
structure take precedence. Pydantic v1 and v2 APIs differ; use the version the
project installs.

## Structure

- Follow the existing router and module layout. `APIRouter` composition is a
  tool, not a required architecture; do not add layers the project lacks.
- Keep settings in the project's settings object, read from the environment,
  and never commit secrets.

## Contracts and Validation

- Declare request bodies, query parameters, and responses with type hints and
  Pydantic models. Set `response_model` or a return type so that output is
  filtered and documented.
- Keep separate input and output models when they differ, so internal or
  sensitive fields never reach responses.
- Use the declared status codes and `HTTPException` for expected errors, and
  document them in the route when the project does.

## Dependencies and Lifecycle

- Use `Depends` for shared resources, authentication, and authorization. Use
  dependencies with `yield` for per-request resources such as sessions, so they
  are released.
- Create and close application-wide resources, such as connection pools and
  clients, in the lifespan handler.

## Async and Blocking Work

- Define a route as `async def` only when everything it awaits is async. Do
  not call blocking I/O or CPU-heavy code inside `async def`; use `def` routes,
  `run_in_threadpool`, or a worker.
- Use async clients for databases and HTTP inside async routes, with timeouts.

## Security

- Authenticate and authorize in dependencies applied to every protected route,
  and check object-level access, not only authentication.
- Configure CORS explicitly for the allowed origins; do not allow all origins
  with credentials.
- Do not log secrets, tokens, or sensitive request data.

## Testing and Validation

- Test endpoints with `TestClient` or an async HTTPX client as nearby tests do,
  overriding dependencies through `app.dependency_overrides`. Cover validation
  and authorization failures.
- Run the configured lint, type checker, and pytest.

## References

- [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
  (router composition, not a required architecture)
- [Concurrency and async/await](https://fastapi.tiangolo.com/async/)
- [Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [Lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/)
