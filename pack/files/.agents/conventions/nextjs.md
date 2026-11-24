# Next.js Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/nextjs.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/react.md`. Repository rules, the
installed Next.js version, and nearby code take precedence. Use the
documentation for the installed version and router. Caching, request APIs, and
file conventions change between major versions.

## Router and Structure

- Keep the router the project uses: App Router (`app/`), Pages Router
  (`pages/`), or both. Do not migrate between them unless the task requires it.
- Follow the router's file conventions for routes, layouts, loading and error
  states, and route handlers or API routes.

## Server and Client Boundaries

- In the App Router, components are Server Components by default. Add
  `"use client"` only to components that need state, effects, event handlers,
  or browser APIs, and keep that boundary as low in the tree as practical.
- Props passed from server to client components must be serializable. Do not
  pass secrets or full database records to client components.
- Mark modules that must never reach the browser as server-only, using the
  project's existing mechanism.

## Data, Caching, and Mutations

- Fetch data on the server where the router supports it, and avoid client-side
  waterfalls.
- Make caching and revalidation explicit, following the installed version's
  defaults. Do not cache per-user or authorized data in shared caches.
- Treat Server Actions and route handlers as public endpoints: validate input,
  authenticate, and authorize inside each one. Middleware or proxy checks
  alone are not enough.
- Revalidate or refresh affected data after mutations.

## Configuration and Security

- Only variables prefixed with `NEXT_PUBLIC_` reach the browser, and they are
  inlined at build time. Never give secrets that prefix.
- Keep security headers, image remote patterns, and redirects configured in the
  project's existing place.
- Use `next/image`, `next/link`, and `next/script` where the project does.

## Validation

Run the project's lint, type check, tests, and `next build`, which reports
server and client boundary errors and prerendering failures. Check changed
routes for both server-rendered and client-navigated loads when practical.

## References

- [Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Data security](https://nextjs.org/docs/app/guides/data-security)
- [Environment variables](https://nextjs.org/docs/app/guides/environment-variables)
- [App Router production checklist](https://nextjs.org/docs/app/guides/production-checklist)
- [Pages Router production checklist](https://nextjs.org/docs/pages/guides/production-checklist)
