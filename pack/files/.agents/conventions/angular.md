# Angular Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/angular.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/typescript.md` and
`.agents/conventions/javascript.md`. Repository rules, the installed Angular
version, configured angular-eslint rules, and the application's existing
structure take precedence. Use the documentation for the installed version;
standalone components, signals, control flow syntax, and zoneless change
detection arrived in different releases.

## Structure and Naming

- Follow the project's file layout and naming. Without a local rule, follow the
  Angular Style Guide for the installed version.
- Keep the project's component model, standalone components or NgModules. Do
  not migrate between them incidentally.
- Keep components focused on presentation, and move shared logic and data
  access into services.

## Dependency Injection

- Inject dependencies with `inject()` or constructor injection, as nearby code
  does, and provide services at the narrowest scope that fits.
- Do not create service instances with `new` when they should come from the
  injector.

## State, Signals, and RxJS

- Use signals or RxJS as the project does. Derive values with `computed` or
  operators rather than duplicating state.
- Unsubscribe from long-lived observables with the `async` pipe,
  `takeUntilDestroyed`, or `DestroyRef`. Do not leave manual subscriptions
  open.
- Avoid nested subscriptions; compose streams with operators such as
  `switchMap`.

## Templates

- Track items in `@for` with `track`, or `trackBy` with `*ngFor`, using a
  stable identity.
- Keep template expressions simple and side-effect free; move logic into the
  component, `computed`, or pure pipes.
- Use `OnPush` change detection for new components when the project does.

## Forms and Security

- Use the project's forms approach, reactive or template-driven, with
  validators on the client and validation again on the server.
- Rely on Angular's built-in sanitization. Do not bypass it with
  `DomSanitizer.bypassSecurityTrust*` for untrusted content, and do not build
  templates from user input.
- Enforce authorization on the server; route guards only improve the user
  experience.

## Testing and Validation

- Test components through their templates and inputs and outputs, and services
  with the injector, using the project's test runner and harnesses.
- Run the configured lint, the production build (`ng build`), and tests.

## References

- [Angular Style Guide](https://angular.dev/style-guide)
- [Dependency injection](https://angular.dev/guide/di)
- [Signals](https://angular.dev/guide/signals)
- [takeUntilDestroyed](https://angular.dev/ecosystem/rxjs-interop/take-until-destroyed)
- [Security](https://angular.dev/best-practices/security)
