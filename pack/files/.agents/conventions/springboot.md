# Spring Boot Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/springboot.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/java.md`, or with the project's JVM
language convention. Repository rules, the existing architecture, and nearby
code take precedence. Use the documentation for the Spring Boot and Spring
Framework versions in the build; major versions change baselines, namespaces,
and defaults.

## Structure and Injection

- Follow the existing package and layer structure. Do not add layers,
  modules, or patterns the project does not use.
- Use constructor injection with `final` fields. Avoid field injection in new
  code.
- Keep beans stateless, or make shared state thread-safe.

## Configuration and Secrets

- Bind related settings with `@ConfigurationProperties` and validate them
  (`@Validated`) where the project does.
- Keep secrets out of committed configuration files. Read them from the
  environment or the project's secret store, and do not log them.
- Use profiles for environment differences, following the project's existing
  profile names.

## Web Layer

- Validate request bodies and parameters with Bean Validation (`@Valid`,
  `@Validated`), and return errors through the project's existing exception
  handling.
- Do not expose JPA entities directly in API responses when the project uses
  separate DTOs.
- Enforce authorization on the server with Spring Security configuration or
  method security. Do not rely on client checks or hidden endpoints.
- Do not disable CSRF protection for browser sessions without a documented
  reason.

## Persistence and Transactions

- Put `@Transactional` on the service boundary that owns the unit of work.
  It applies only through the Spring proxy, so calls within the same class do
  not start a transaction.
- Mark read-only work `@Transactional(readOnly = true)` where the project does.
- Avoid N+1 queries; use fetch joins, entity graphs, or projections, and check
  generated SQL for changed queries.
- Change the schema through the project's migration tool, such as Flyway or
  Liquibase, not through `ddl-auto`, outside local development.

## Operations

- Expose only the Actuator endpoints the project intends, and secure them.
- Make scheduled and asynchronous work safe to retry and to run in multiple
  instances.

## Testing and Validation

- Use the narrowest test that covers the change: plain unit tests, slice tests
  such as `@WebMvcTest` or `@DataJpaTest`, or `@SpringBootTest` for full
  integration.
- Use the project's approach for real dependencies, such as Testcontainers, and
  do not replace an integration test with mocks when the database behavior
  matters.
- Run the build's test and check tasks.

## References

- [Externalized configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)
- [Testing Spring Boot applications](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html)
- [Declarative transactions](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)
- [Method security](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)
- [Actuator endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)
