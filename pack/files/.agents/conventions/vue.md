# Vue Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/vue.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/javascript.md`, and with
`.agents/conventions/typescript.md` for TypeScript projects. Repository rules,
the installed Vue version, configured eslint-plugin-vue rules, and nearby
components take precedence. Keep the project's API style, Composition API
(often `<script setup>`) or Options API, and its state and routing libraries.

## Components

- Use multi-word component names, and name single-file components
  consistently with the project (`PascalCase.vue` by default).
- Declare props with types and, where useful, defaults and validators. Declare
  emitted events with `defineEmits` or `emits`.
- Treat props as read-only. Emit events or use `v-model` bindings to change
  parent state instead of mutating props.
- Keep components focused; move reusable stateful logic into composables
  named `useSomething`.

## Reactivity

- Derive values with `computed` instead of watchers that copy state. Keep
  computed getters free of side effects.
- Use `watch` or `watchEffect` for side effects that respond to changes, and
  clean up timers, listeners, and requests in the cleanup callback or
  `onUnmounted`.
- Do not destructure reactive objects in ways that lose reactivity; use
  `toRefs` or access properties directly.
- Mutate reactive state, not copies, and avoid replacing whole reactive
  objects held by other code.

## Templates and Rendering

- Give `v-for` items stable, unique `:key` values. Do not put `v-if` and
  `v-for` on the same element.
- Keep template expressions simple; move logic into computed values or
  methods.
- Do not render untrusted content with `v-html`, and do not bind untrusted URLs
  or styles without validation. Never compile untrusted templates.
- Use semantic elements and accessible names in templates.

## Performance

- Split large lists and heavy components with virtualization, lazy loading, or
  `defineAsyncComponent` where profiling shows a need.
- Use `shallowRef` or `markRaw` for large immutable data or third-party
  instances that need no deep reactivity.

## Testing and Validation

- Test components through rendered output and emitted events with the
  project's tools, such as Vue Test Utils with Vitest or Jest.
- Run the configured lint, type check (for example `vue-tsc`), and tests.

## References

- [Vue Style Guide](https://vuejs.org/style-guide/)
- [Watchers](https://vuejs.org/guide/essentials/watchers.html)
- [Performance](https://vuejs.org/guide/best-practices/performance.html)
- [Security](https://vuejs.org/guide/best-practices/security.html)
- [eslint-plugin-vue](https://eslint.vuejs.org/)
