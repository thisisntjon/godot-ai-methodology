# godot-guard — the lens (rules + non-goals)

What `code-review` / an adversarial spec-review step should consult when working a Godot project. Grounded in
`../../00-principles.md`, `../../03-techniques.md`, `../../04-ai-collaboration-patterns.md`, and
the StS2 case study (`../../STS2_EVIDENCE.md`). The automated half is `guard_check.py`; this
file is the judgment half.

## A. Godot-4.x idiom (errors — automatable, must fix)
| Drift | Godot 4.x |
| --- | --- |
| `export var x` / `export(Type) var x` | `@export var x: Type` |
| `onready var x` | `@onready var x` |
| `yield(obj, "sig")` | `await obj.sig` |
| `connect("sig", self, "method")` | `sig.connect(method)` (Callable) |
| `setget a, b` | setter/getter funcs, or `@export` with `set`/`get` |
| `OS.get_ticks_msec()` for timing | `Time.get_ticks_msec()` (and keep it out of gameplay — see B) |

## B. Determinism (warn — justify or fix)
- **Seeded, per-concern RNG.** Gameplay randomness uses a `RandomNumberGenerator` stream per
  concern (rewards/shops/…), seeded and saved via `.seed`/`.state`. Global `randi()/randf()/
  randomize()` in gameplay is a leak — it can't be reproduced from a seed/save. Cosmetic-only
  randomness is fine but must be a separate, non-saved stream.
- **No wall-clock in logic.** `Time.get_ticks_msec()`/dates driving gameplay break reproducibility.
- *Why:* determinism is what lets you reproduce a reported bug from a seed and write stable
  tests — the foundation the whole methodology rests on.

## C. Known traps (warn)
- **`const` typed containers.** `const X: Array[...] = [...]` / `PackedStringArray(...)` as a
  parse-time `const` fails or misbehaves — use `static var`.
- **`Dispose()` vs `Free()`** for RefCounted (C#) and freeing nodes mid-frame; null cached
  references around quit frames (StS2's `MegaLabel` lesson).
- **Node-path / signal fragility:** prefer building UI/scenes in code or exporting typed
  `NodePath`s; avoid brittle string paths.

## D. Non-goals (the architecture lens — feed these into adversarial spec review)
These are the rules an assistant most often violates by being "helpful":
- **Do NOT special-case effect/modifier combinations.** Effects emit `Modifier` records; the
  resolver folds them (additive → multiplicative → cap → clamp). No pairwise "if A and B".
- **Do NOT put game logic in input handlers.** Player intent is a `GameAction` queued + executed;
  rules live in systems. Keep the seam.
- **Do NOT add content as control flow.** New cards/enemies/items are data (`Model`/tables),
  not new branches.
- **Do NOT let optional infrastructure block the core.** Cloud/telemetry are best-effort; a
  failure must never stop a local save or startup.
- **Do NOT introduce non-determinism into the update loop.** Input and cosmetic RNG stay outside it.

## E. What a regex can't check (human/agent judgment)
- Is the RNG actually seeded *and* the seed persisted, or just nominally a RandomNumberGenerator?
- Are saves atomic (temp→rename) and migration-versioned?
- Does the change keep the modifier pipeline the single resolution path?
- Are systems testable (RNG/stores injectable)?
