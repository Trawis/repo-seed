# HTML Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/html.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers HTML in pages, templates, and
components. Framework and template-engine conventions, when selected, add to
this file. Configured formatters, validators, and accessibility checks, and
nearby markup, take precedence.

## Document Structure

- Keep the doctype, `lang` on `<html>`, `<meta charset="utf-8">`, a viewport
  meta tag, and a meaningful `<title>` in full documents.
- Use landmarks (`header`, `nav`, `main`, `footer`, `aside`) and one `main` per
  page. Keep heading levels in order without skipping levels for styling.

## Semantics and Accessibility

- Use the native element for the job: `button` for actions, `a href` for
  navigation, lists for lists, and `table` with headers for tabular data. Do
  not rebuild these from `div` and `span`.
- Every interactive element must be reachable and operable by keyboard, with a
  visible focus state. Do not use positive `tabindex`.
- Give images meaningful `alt` text, or `alt=""` when decorative.
- Give icon-only controls an accessible name.
- Prefer native semantics to ARIA. Add ARIA only when no native element fits,
  and keep roles, states, and keyboard behavior consistent with the pattern.
- Do not convey information by color alone.

## Forms

- Associate every control with a `<label>`, using `for` or by nesting it.
  Placeholders are not labels.
- Use the matching `type`, `autocomplete`, and `inputmode` attributes, and
  group related controls with `fieldset` and `legend`.
- Keep client-side validation as a convenience; the server must validate
  again. Connect error messages to their fields, for example with
  `aria-describedby`.

## Safe Rendering

- Insert untrusted data through the template engine's escaping. Do not
  disable escaping or build HTML strings from user input.
- Validate user-supplied URLs before using them in `href` or `src`, and reject
  `javascript:` URLs.
- Add `rel="noopener"` or `rel="noreferrer"` to `target="_blank"` links when the
  project supports browsers that need it.
- Keep inline scripts and inline event handlers out of new markup when the
  project uses a Content Security Policy.

## Progressive Enhancement and Performance

- Keep core content and actions working with plain HTML where the project
  supports it, and enhance with scripts.
- Set `width` and `height` on images and media to reserve space. Use
  `loading="lazy"` for offscreen images only.

## Validation

Run the project's configured formatter, HTML validator, linter, and
accessibility checks. Check changed UI by keyboard, and when practical with a
screen reader or the browser's accessibility tree.

## References

- [MDN: HTML accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML)
- [MDN HTML reference](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [MDN HTML code style](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Code_style_guide/HTML)
  (an example style, not a standard)
