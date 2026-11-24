# GDScript Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/gdscript.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. This covers GDScript in Godot projects. The
project's Godot version in `project.godot`, configured gdtoolkit or editor
settings, and nearby scripts take precedence. Godot 3 and Godot 4 differ in
syntax and APIs, so check the documentation for the installed version.

## Style and Naming

- Follow the GDScript style guide: `snake_case` for files, functions,
  variables, and signals, `PascalCase` for `class_name` and nodes,
  `CONSTANT_CASE` for constants and enum members, and tabs for indentation.
- Order script members as the style guide describes: signals, enums,
  constants, exported and other variables, `_init` and `_ready`, then other
  methods.
- Prefix private functions and variables with `_`. Name signals in the past
  tense, such as `health_changed`.

## Typing

- Use static typing for variables, parameters, and return values when the
  project does, including typed arrays where supported.
- Treat type warnings from the project's warning settings as errors to fix,
  not to suppress.

## Nodes and Scenes

- Keep each scene responsible for its own children. Call down to children
  directly; signal up to parents and siblings.
- Reference nodes with `@onready` and `%UniqueName` or exported node paths
  rather than long `get_node` paths that break on scene changes.
- Check `is_instance_valid` before using nodes that may have been freed, and
  free nodes with `queue_free`.
- Do not modify the scene tree or physics state from threads; defer with
  `call_deferred` where needed.

## Signals and Lifecycle

- Connect signals in code or the editor as the project does, and disconnect
  connections that outlive their emitter or receiver.
- Initialize node-dependent state in `_ready`, not `_init`, and clean up in
  `_exit_tree` or on `NOTIFICATION_PREDELETE` when needed.

## Processing and Resources

- Put physics and movement in `_physics_process` and frame-rate visuals in
  `_process`, using `delta` for time-based changes.
- Disable processing for nodes that do not need it.
- Treat loaded `Resource` instances as shared. Duplicate them before mutating
  per-instance state, or mark them local to the scene.
- Do not load untrusted resource files at runtime; they can contain scripts.

## Documentation and Validation

- Document public classes, functions, and signals with `##` documentation
  comments.
- Run the configured checks, such as gdlint and gdformat, and tests with GUT
  or gdUnit4, headless where the project supports it. Say which editor-only
  checks were not run.

## References

- [GDScript style guide](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html)
- [Static typing in GDScript](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/static_typing.html)
- [Documentation comments](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_documentation_comments.html)
- [Idle and physics processing](https://docs.godotengine.org/en/stable/tutorials/scripting/idle_and_physics_processing.html)
- [Best practices](https://docs.godotengine.org/en/stable/tutorials/best_practices/index.html)
