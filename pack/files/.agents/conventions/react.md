# React Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/react.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/javascript.md`, and with
`.agents/conventions/typescript.md` for TypeScript projects. Repository rules,
the installed React version, configured lint rules, and nearby components take
precedence. Do not introduce a state library, styling system, or component
pattern the project does not already use. HTML and CSS conventions, when
selected, still apply to rendered markup and styles.

## Rules of React

- Keep components and hooks pure during render: same inputs, same output, and
  no side effects such as mutations, subscriptions, or network calls.
- Do not mutate props, state, or values passed to hooks. Create new objects and
  arrays for updates.
- Call hooks only at the top level of components and custom hooks, never in
  conditions, loops, or callbacks. Name custom hooks `useSomething`.
- Do not call components as functions; render them as elements.

## State and Effects

- Keep state minimal and close to where it is used. Derive values during
  render instead of mirroring props or other state in state.
- Lift state only as far as the components that share it, and keep a single
  owner for each piece of state.
- Use effects only to synchronize with systems outside React, such as
  subscriptions, timers, or browser APIs. Do not use them to transform data
  or respond to user events.
- Declare every reactive value an effect uses as a dependency, and return a
  cleanup that undoes its setup. Do not suppress the hooks lint rule to omit
  dependencies.
- Use functional updates (`setCount(c => c + 1)`) when the next state depends on
  the previous one.

## Rendering

- Give list items stable, unique keys from the data. Do not use array indexes
  when items can be reordered, inserted, or removed.
- Use a `key` change to reset a component's state deliberately.
- Add memoization (`memo`, `useMemo`, `useCallback`) only when profiling or a
  stable-identity requirement justifies it. When the project uses React
  Compiler, follow its guidance instead of adding manual memoization.
- Do not render untrusted HTML with `dangerouslySetInnerHTML` unless it is
  sanitized.

## Components and Accessibility

- Keep components focused, with explicit props. Document a shared component's
  props and behavior when its contract is not obvious from types.
- Use semantic elements and accessible names in JSX, manage focus when content
  changes, and keep custom controls keyboard-operable.

## Testing and Validation

- Test behavior through the rendered output and user interactions with the
  project's testing tools, not through implementation details.
- Run the configured lint (including the hooks rules), type check, and tests.

## References

- [Rules of React](https://react.dev/reference/rules)
- [React reference](https://react.dev/reference/react)
- [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [eslint-plugin-react-hooks](https://react.dev/reference/eslint-plugin-react-hooks)
