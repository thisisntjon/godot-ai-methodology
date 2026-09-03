# godot-context — section reference

Why each section of the generated `CLAUDE.md` earns its place. (Grounded in the methodology
docs `../../00-principles.md`, `../../04-ai-collaboration-patterns.md`, and the Slay the Spire 2
case study `../../STS2_EVIDENCE.md`.)

| Section | Purpose | Why it matters for an AI assistant |
| --- | --- | --- |
| **Engine & build** | Pin the exact engine version + the discovered binary path. | Stops the assistant assuming `godot` is on PATH or guessing the version → prevents Godot-3 API drift (the #1 recurring AI failure in Godot work). |
| **Commands** | Editor / run / headless-import / test commands, using `$GODOT_BIN`. | Gives the assistant copy-paste-correct ways to run and verify, instead of inventing flags. |
| **Architecture (autoloads)** | List singletons in dependency order + each one's responsibility. | The assistant edits the right system and respects load order instead of re-discovering it. |
| **Deterministic update order** | The single tick order; input + cosmetic RNG stay outside it. | Determinism is what makes bugs reproducible and tests stable; documenting the order keeps the assistant from inserting non-deterministic work into the loop. |
| **GDScript 4.x rules** | The idioms + traps (`const` vs `static var`, signals, typing, seeded RNG, `FileAccess`). | Directly counters the most common AI mistakes; pairs with the `godot-guard` lens at review time. |
| **Non-negotiables** | Determinism quarantine · data-driven content · compose-don't-special-case · intent/logic seam · test seams. | These are the architecture's load-bearing rules; stated as non-goals they stop the assistant "helpfully" special-casing and eroding the design. |
| **Conventions** | Naming, directory layout, signal hygiene, save/migration. | Keeps generated code consistent with the codebase so diffs stay small and reviewable. |

## Curation tips
- Keep it **short and true** — a context file the assistant can read in one pass beats an
  exhaustive one that drifts. Regenerate the *facts* (engine/version/autoloads) with the
  helper; hand-curate the *judgment* sections.
- The **deterministic update order** and **non-negotiables** are the highest-value sections —
  they encode what an assistant can't infer and most often gets wrong.
- If the project is C#, note it, but the methodology's worked examples are GDScript.
