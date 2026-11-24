# Flutter Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/flutter.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/dart.md`. Repository rules, the
project's state management and architecture, and nearby widgets take
precedence. Do not introduce a state management package or architectural
pattern the project does not already use. Respect the Flutter SDK version the
project uses.

## Widgets

- Keep widgets small and focused. Extract reusable pieces into widget classes
  rather than helper methods that return widgets, so they rebuild
  independently.
- Use `const` constructors and widgets wherever possible.
- Keep `build` methods free of side effects and expensive work; they can run
  often.
- Use `StatelessWidget` unless the widget owns mutable state.

## State and Lifecycle

- Keep each piece of state in one owner, following the project's state
  management approach, and lift it only as far as needed.
- Dispose of controllers, focus nodes, animation controllers, and stream
  subscriptions in `dispose()`, and call `super.dispose()` last.
- Check `mounted` (or `context.mounted`) before using `BuildContext` or calling
  `setState` after an `await`.
- Do not store `BuildContext` beyond the call that received it.

## Layout, Accessibility, and Performance

- Build responsive layouts with constraints (`LayoutBuilder`, `MediaQuery`
  sizes, flexible widgets) rather than fixed device sizes, and test text
  scaling.
- Give interactive and image widgets semantic labels, keep tap targets large
  enough for the platform, and do not rely on color alone.
- Use builder constructors (`ListView.builder`) for long or unbounded lists,
  and avoid rebuilding large subtrees for small state changes.
- Avoid expensive operations such as `saveLayer`, opacity on large subtrees,
  and clipping in animations without profiling.

## Platform and Security

- Keep secrets out of the app bundle; anything shipped to devices is readable.
- Use platform channels and plugins the project already uses, and check
  permissions before using protected features.

## Testing and Validation

- Cover widget behavior with widget tests, flows with integration tests, and
  logic with unit tests, following the project's existing test layout.
- Run `flutter analyze` and `flutter test`, and the configured integration
  tests when the environment supports them.

## References

- [Flutter architecture recommendations](https://docs.flutter.dev/app-architecture/recommendations)
  (guidance, not a mandatory rewrite)
- [Performance best practices](https://docs.flutter.dev/perf/best-practices)
- [Accessibility](https://docs.flutter.dev/ui/accessibility)
- [Testing Flutter apps](https://docs.flutter.dev/testing/overview)
