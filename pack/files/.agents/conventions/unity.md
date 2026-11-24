# Unity / C# Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/unity.md`
**Local editing**: Do not customize this synced copy

Apply this with `.agents/conventions/csharp.md`. Repository rules and nearby code take precedence.
Check APIs against the project's Unity version in
`ProjectSettings/ProjectVersion.txt`. Some names change between releases; for
example, Unity 2023.1 deprecated `FindObjectOfType` and Unity 6 renamed
`Rigidbody.velocity` to `linearVelocity`.

## Components and Lifecycle

- Keep one `MonoBehaviour` per file, with a matching filename.
- Use plain C# classes for logic that needs no Unity lifecycle or serialization.
- Prefer `[SerializeField] private` over public inspector fields.
- Repo Seed source-order default for used callbacks: `Awake`, `OnEnable`,
  `Start`, `Update`, `LateUpdate`, `FixedUpdate`, `OnDisable`, `OnDestroy`.
  This orders the source file only. At runtime `FixedUpdate` runs on the
  physics timestep, zero or more times per frame and before `Update`.
- Do not rely on the order in which the same callback runs on different
  objects. Use explicit initialization or the project's Script Execution Order
  settings when order matters.
- `Awake` runs even when the component is disabled, if its GameObject is
  active. `Start` runs only once the component is enabled.
- Cache component references in `Awake`. Do not look up components or objects
  every frame.
- Subscribe in `OnEnable` and unsubscribe in `OnDisable`.
- Do not add empty lifecycle methods.

## Unity Objects and Coroutines

- `UnityEngine.Object` overloads `==`, so a destroyed object compares equal to
  `null`. `is null`, `?.`, and `??` bypass that check; do not use them on Unity
  objects.
- `Destroy` takes effect at the end of the frame, so a destroyed object stays
  usable until then.
- In hot paths, use the implicit Unity object check when it is clear.
- Give coroutine methods a `Coroutine` suffix.
- Coroutines stop when their GameObject is deactivated or destroyed, but not
  when the component is disabled. Keep a `Coroutine` handle and stop it
  explicitly when early cancellation is required.
- For async code, use the version's supported APIs, such as `Awaitable` and
  `destroyCancellationToken`, and stop work when the object is destroyed.
- Use explicit state machines for complex interruptible flows.

## Serialization

- Unity serializes fields, not properties. Serialized fields must be public or
  `[SerializeField]`, not static, const, or readonly, and of a supported type.
  Check the target version's serialization rules for collections and
  polymorphic types; `[SerializeReference]` is needed for the latter.
- Serialized values from scenes and prefabs override field initializers.
- Renaming a serialized field drops existing data. Use
  `[FormerlySerializedAs]` when renaming one that assets already use.

## Physics and Performance

- Perform physics work in `FixedUpdate`. Read input in `Update`.
- Move rigid bodies through `Rigidbody` APIs, not transforms.
- Avoid repeated allocations, LINQ, string construction, and component lookup in frame callbacks.
- Pool frequently created gameplay objects where profiling justifies it.
- Profile before speculative optimizations.

## Project Structure

- Prefer C# events or `UnityEvent` over `SendMessage`.
- Use `ScriptableObject` for shared configuration, not mutable runtime state.
- Keep editor-only code under `Editor/` folders or editor-only assembly
  definitions, or guard it with `#if UNITY_EDITOR`.
- Do not reference `UnityEditor` from runtime assemblies; player builds fail.
- Centralize tags and layers. Use `CompareTag`, not direct tag-string equality.
- Follow existing asset naming. Rename referenced assets through the Unity Editor.
- Keep `.meta` files with their assets, and do not edit their GUIDs.

## Testing

Use Edit Mode tests for pure logic and Play Mode tests for lifecycle, scenes, and runtime integration. Keep Unity-dependent behavior out of plain classes when practical, so it stays easy to test.
When the Editor is unavailable, say which Unity tests and builds were not run.

## References

- [Order of execution for event functions](https://docs.unity3d.com/Manual/execution-order.html)
- [Serialization rules](https://docs.unity3d.com/Manual/script-serialization-rules.html)
- [Coroutines](https://docs.unity3d.com/Manual/coroutines.html)
- [Unity C# formatting best practices](https://unity.com/how-to/formatting-best-practices-c-scripting-unity)
  (a style reference, not a requirement)
