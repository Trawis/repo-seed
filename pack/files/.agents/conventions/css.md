# CSS Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/css.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers CSS and preprocessor stylesheets.
The project's styling architecture, such as CSS modules, utility classes,
CSS-in-JS, BEM, or a design system, and its configured formatter and Stylelint
rules take precedence. Do not introduce a new CSS framework or methodology.

## Compatibility

- Use only features supported by the project's browser targets, from
  `browserslist` or the build configuration. Rely on the configured
  autoprefixer or build pipeline rather than hand-written vendor prefixes.
- Guard newer features with `@supports` when targets require a fallback.

## Cascade and Specificity

- Keep specificity low and predictable. Prefer class selectors to IDs and
  long descendant chains, and avoid styling by element in component code.
- Do not use `!important` to win specificity battles. Reserve it for utilities
  or overrides the project documents.
- Place new rules where the project's layering or file structure expects them,
  including `@layer` order when it is used.
- Remove rules that a change makes dead, rather than adding overrides.

## Naming and Tokens

- Follow the existing naming scheme. Name classes for their purpose, not their
  appearance.
- Use the project's design tokens or custom properties for colors, spacing,
  typography, and breakpoints. Do not hard-code values that a token covers.

## Layout and Responsive Design

- Use flexbox and grid for layout, not floats or absolute positioning, unless
  the effect requires them.
- Design for small screens and content growth: avoid fixed heights and widths
  on text containers, and let content wrap.
- Use relative units such as `rem` for type and spacing where the project does,
  so text scales with user settings.
- Use the project's breakpoints, and prefer container queries or intrinsic
  layouts where they are supported and already in use.

## Accessibility

- Keep focus indicators visible. Do not remove outlines without a replacement,
  and prefer `:focus-visible` for custom styles.
- Meet the project's contrast requirements, WCAG AA at minimum, for text and
  essential UI.
- Respect `prefers-reduced-motion` for non-essential animation, and honor
  `prefers-color-scheme` and forced-colors modes where the project supports
  themes.
- Do not hide content that assistive technology needs with `display: none`;
  use the project's visually-hidden utility instead.

## Validation

- Preserve essential browser-workaround and stacking-context constraints that
  code cannot express.
- Run the project's configured formatter and Stylelint, and check changed UI at
  its supported viewport sizes and themes.

## References

- [MDN CSS reference](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [MDN: Cascade, specificity, and inheritance](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Handling_conflicts)
- [MDN: CSS and JavaScript accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/CSS_and_JavaScript)
- [Stylelint](https://stylelint.io/)
- [MDN CSS code style](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Code_style_guide/CSS)
  (an example style, not a standard)
