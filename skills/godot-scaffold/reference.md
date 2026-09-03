# godot-scaffold — substrate reference

Each emitted file, what it's for, its Slay the Spire 2 grounding (see `../../STS2_EVIDENCE.md`
and `../../03-techniques.md`), and how to extend it. All code is original GDScript 4.x.

| File | Class | Purpose | StS2 grounding |
| --- | --- | --- | --- |
| `rng.gd` | `RngStreams` | Seeded, per-concern RNG (`rewards`/`shops`/`transforms`) + a non-saved `chaotic` stream; `save_state`/`load_state`. | `PlayerRngSet` (segregated streams), `Rng` (seeded), `Rng.Chaotic` (cosmetic, not persisted). |
| `model.gd` / `entity.gd` | `Model` / `Entity` | Definition (data) vs runtime instance — add content as data, not branches. | `Core.Models` vs `Core.Entities`. |
| `modifier.gd` | `Modifier` | One contribution (ADDITIVE/MULTIPLICATIVE/CAP) with a `source`. | `ModifyDamageHookType`. |
| `modifier_resolver.gd` | `ModifierResolver` | Folds modifiers in a fixed order (add → mult → cap → clamp). Compose, don't special-case. | `Hook` + `ModifyDamage*` resolution. |
| `game_action.gd` / `action_executor.gd` | `GameAction` / `ActionExecutor` | Player intent queued + executed — the seam between input and game logic. | `GameAction` wraps `Command`; `ActionExecutor` drains the queue. |
| `migration.gd` | `SaveMigration` | Versioned forward migration of save data. | `IMigration<T>` / `MigrationUtil`. |
| `save_store.gd` | `SaveStore` | Atomic JSON save (temp → rename); reads run migrations; cloud (if added) stays best-effort. | `GodotFileIo` (atomic writes), `CloudSaveStore` (best-effort policy). |

## How to extend (the disciplined path)
- **New content** → subclass `Model` (definition) + `Entity` (instance). No new control flow.
- **New effect** → emit `Modifier` records from the effect and let `ModifierResolver` fold
  them. Never branch on specific effect combinations.
- **New player action** → subclass `GameAction`, override `execute()`, enqueue on
  `ActionExecutor`. Keep rules in systems, not in the action.
- **Save schema change** → bump `SaveMigration.current_version()` and add a step; old saves
  load forward.

## Why the gate matters
The substrate's files reference each other by `class_name`. A per-file syntax check can pass
files that fail to load *together*; and `load()` returns a non-null object even for a script
with a compile error. The gate therefore `--import`s (building the class cache) and calls
`GDScript.reload()` on every script — the only reliable "does this project actually compile"
signal. Treat `GATE PASS` as the definition of done for any GDScript change, not just scaffolds.
