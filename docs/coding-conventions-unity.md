# Unity / C# Coding Conventions

Conventions for Unity projects that use this agent guideline pack.

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-06-25

These conventions extend `docs/coding-conventions-csharp.md`. Apply both files when working in a Unity project; Unity-specific rules here take precedence over generic C# defaults where they conflict.

---

## Quick Reference

| Area | Rule |
|------|------|
| MonoBehaviour naming | `PascalCase`, one class per file, filename matches class name |
| Lifecycle order | Awake → OnEnable → Start → Update → LateUpdate → FixedUpdate → OnDisable → OnDestroy |
| Serialized fields | `[SerializeField] private` instead of `public` for inspector-exposed fields |
| Component references | Cache in `Awake`; never call `GetComponent` in `Update` |
| Null checks | Avoid `== null` on UnityEngine.Object in hot paths; use the implicit bool conversion instead |
| Coroutines | Name with `Coroutine` suffix; store `Coroutine` handle when early stop is needed |
| Physics | Physics code in `FixedUpdate`; move `Rigidbody` via `MovePosition`/`MoveRotation` |
| Tags and layers | Use constants or enums; never compare with raw strings in code |
| Editor scripts | Keep under `Editor/` folder; wrap with `#if UNITY_EDITOR` when in shared files |
| Asset naming | `PascalCase` for prefabs and ScriptableObjects; `snake_case` acceptable for textures/audio if project already uses it |

---

## MonoBehaviour Classes

- One `MonoBehaviour` subclass per file.
- Filename must match the class name exactly.
- Do not add `MonoBehaviour` to classes that do not need it; prefer plain C# classes for pure logic.
- Do not use `new` to construct `MonoBehaviour` subclasses; always use `AddComponent` or prefab instantiation.

---

## Serialized Fields

Prefer `[SerializeField] private` over `public` for inspector-exposed data:

```csharp
// Preferred
[SerializeField] private float _speed = 5f;
[SerializeField] private Transform _target;

// Avoid — exposes field to all callers, not just inspector
public float speed = 5f;
```

Use `[Header("...")]` and `[Tooltip("...")]` when grouping or clarifying inspector fields, but only when they add genuine clarity.

---

## Lifecycle Method Order

Declare Unity lifecycle callbacks in this order:

```csharp
private void Awake()   { }   // one-time setup, component refs
private void OnEnable()  { }   // subscribe events
private void Start()   { }   // setup that depends on other components being initialized
private void Update()    { }   // per-frame logic
private void LateUpdate()  { }   // camera follow, final adjustments
private void FixedUpdate() { }   // physics
private void OnDisable() { }   // unsubscribe events
private void OnDestroy() { }   // final cleanup
```

Only include the methods the class actually uses. Do not add empty lifecycle stubs.

---

## Component References

Cache component references in `Awake`, not in `Update` or `Start`:

```csharp
private Rigidbody _rb;
private Animator _animator;

private void Awake()
{
    _rb = GetComponent<Rigidbody>();
    _animator = GetComponent<Animator>();
}
```

Never call `GetComponent`, `FindObjectOfType`, or `GameObject.Find` in `Update`, `FixedUpdate`, or `LateUpdate`.

Use `[SerializeField]` references instead of `FindObjectOfType` when the dependency is known at edit time.

---

## Null Checks on UnityEngine.Object

Unity overrides `==` on `UnityEngine.Object`, which has non-trivial overhead. In hot paths, use the implicit bool conversion:

```csharp
// Preferred in Update
if (_target)
    transform.LookAt(_target);

// Fine for one-time checks outside hot paths
if (_target == null)
    throw new InvalidOperationException("Target not assigned.");
```

Use `is null` / `is not null` (C# pattern) only for plain C# objects, not `UnityEngine.Object` subclasses, since it bypasses the Unity lifetime check.

---

## Coroutines

- Name coroutine methods with a `Coroutine` suffix: `FadeOutCoroutine`, `SpawnLoopCoroutine`.
- Store the returned `Coroutine` handle when the caller needs to stop it early:

```csharp
private Coroutine _fadeCoroutine;

private void StartFade()
{
    if (_fadeCoroutine != null)
        StopCoroutine(_fadeCoroutine);

    _fadeCoroutine = StartCoroutine(FadeOutCoroutine());
}
```

- Do not use coroutines as a substitute for proper state machines in complex, interruptible flows.
- Avoid `yield return new WaitForSeconds(...)` inside tight coroutine loops that run many instances simultaneously; cache `WaitForSeconds` instances to reduce allocation.

---

## Physics

- All physics reads (`velocity`, `position`) and writes (`AddForce`, `MovePosition`) belong in `FixedUpdate`.
- Move a `Rigidbody` via `MovePosition` / `MoveRotation`, not by setting `transform.position` directly when the object has a `Rigidbody`.
- Do not read `transform.position` inside `FixedUpdate` for physics calculations; use `Rigidbody.position` instead.
- Use `Physics.SphereCast` / `RaycastNonAlloc` variants to avoid per-frame allocation when raycasting every fixed step.

---

## Tags and Layers

Never compare tags with raw string literals scattered across code:

```csharp
// Avoid
if (other.CompareTag("Enemy")) { }

// Preferred — define once
public static class Tags
{
    public const string Enemy = "Enemy";
    public const string Player = "Player";
}

if (other.CompareTag(Tags.Enemy)) { }
```

Use `CompareTag` rather than `gameObject.tag == "..."` to avoid string allocation.

Layers should likewise be centralized in a constants class or resolved once with `LayerMask.NameToLayer` and stored.

---

## Events and Messaging

- Prefer C# events (`event Action`, `event Action<T>`) or UnityEvents over `SendMessage` / `BroadcastMessage`.
- Subscribe in `OnEnable`, unsubscribe in `OnDisable` to avoid memory leaks and duplicate callbacks when objects are toggled.
- Use `UnityEvent` for designer-configurable hooks exposed in the inspector; use C# events for pure-code subscriber patterns.

---

## ScriptableObjects

- Use `ScriptableObject` for shared data, configuration, and designer-tunable constants instead of singletons holding mutable state.
- Create factory methods with `[CreateAssetMenu]` when designers need to create instances from the Project window.
- Do not persist runtime state in `ScriptableObject` assets in builds; they are shared references.

---

## Singletons

Avoid persistent `MonoBehaviour` singletons with `DontDestroyOnLoad` unless the use case genuinely requires it (audio manager, scene loader). When a singleton is needed:

- Destroy the duplicate if a second instance is loaded, rather than replacing the existing one.
- Keep the singleton's API minimal; move logic out of it into plain C# classes that can be tested without Unity.

---

## Editor Scripts

- Place editor-only scripts under an `Editor/` folder so Unity excludes them from builds automatically.
- When editor utility code must live in a shared file, guard it with `#if UNITY_EDITOR` / `#endif`.
- Do not reference `UnityEditor` types from runtime code.

---

## Asset and File Naming

- Prefabs: `PascalCase` matching the primary component script name where possible (e.g., `PlayerController.prefab`).
- ScriptableObjects: `PascalCase` (e.g., `EnemyConfig.asset`).
- Scenes: `PascalCase` (e.g., `MainMenu.unity`, `Level01.unity`).
- Textures, audio, and other binary assets: follow the project's existing convention. `snake_case` is acceptable if that is the established style.
- Avoid spaces in filenames; they cause friction in version control and scripts.
- Do not rename assets that are referenced by GUID in prefabs or scenes without using the Unity Editor rename operation.

---

## Performance Considerations

- Avoid allocations in `Update`, `FixedUpdate`, and `LateUpdate`: no LINQ, no string concatenation, no `new` for reference types.
- Use object pooling for frequently spawned/destroyed objects (projectiles, particles, UI elements).
- Prefer `StringBuilder` for dynamic string construction in non-hot paths; avoid it in per-frame code.
- Profile with the Unity Profiler before optimizing; do not prematurely optimize code that is not on a hot path.

---

## Testing

- Pure C# logic that does not depend on `UnityEngine` types can be tested with standard NUnit tests in an `EditMode` test assembly.
- `PlayMode` tests are appropriate for integration tests that require the full Unity runtime, component lifecycle, or scene loading.
- Do not assert on `UnityEngine.Object` equality in edit-mode tests without instantiating objects first.
