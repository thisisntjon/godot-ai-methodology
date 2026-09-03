---
name: godot-scaffold
description: >-
  Scaffold the AI-leverageable architecture substrate into a Godot project as original
  GDScript 4.x — seeded per-concern RNG, Model/Entity (data-driven) split, a
  modifier-resolution pipeline (additive/multiplicative/cap), an intent-vs-logic action
  queue, and atomic save + versioned migration — then prove it with a project-load gate.
  Use when starting a new Godot game, when an existing project lacks these foundations, or
  when the user says "scaffold the architecture", "set up the substrate / RNG / save system /
  modifier pipeline", "give me the deterministic foundations", or "/godot-scaffold". Pairs
  with godot-context (documents what this writes) and godot-guard (reviews it).
disable-model-invocation: true
argument-hint: <project_dir> [--dir scripts/core] [--force]
---

# godot-scaffold

**The failure this prevents:** a Godot project growing without the foundations that make it
testable, reproducible, and safe for an AI assistant to extend — so randomness is
unreproducible, content is hard-coded, effects are special-cased into combinatorial spaghetti,
input and logic are tangled, and saves corrupt. This skill writes those foundations once, as
original GDScript, and **gates them** so what it emits actually compiles as a unit.

## Steps

1. **Point at the project** — the directory with `project.godot` (GDScript 4.x).
2. **Emit + gate** (zero-dep, stdlib only):
   ```bash
   python <skill-dir>/scaffold.py <project_dir>
   ```
   (`<skill-dir>` = this skill's folder: `skills/godot-scaffold/` in the repo, or `~/.claude/skills/godot-scaffold/` once installed.)
   Copies the substrate into `scripts/core/` (override with `--dir`), then runs the
   **project-load gate**: it `--import`s the project and recompiles every script via
   `GDScript.reload()` — `GATE PASS` means the whole substrate loads together. **No-overwrite**
   by default (use `--force` to replace).
3. **Wire it in** — make the systems your game needs use the substrate: construct one
   `RngStreams` per run (seed it), subclass `Model`/`Entity` for your content, emit `Modifier`
   records and resolve via `ModifierResolver`, route player input through
   `GameAction`/`ActionExecutor`, persist through `SaveStore`.
4. **Document it** — run `godot-context` so the new architecture lands in `CLAUDE.md`.

## Rules

- **The gate is the definition of done.** Never consider a scaffold (or any later GDScript
  change) complete until the project-load gate passes. `GATE PASS` requires `GDScript.reload()`
  to succeed on every script — a bare `load()` returns non-null even for broken scripts.
- **No-overwrite.** Never clobber a hand-edited file; `--force` is explicit and deliberate.
- **Emit data-driven, compose-don't-special-case substrate only.** Extend by subclassing
  `Model`/`Entity` and emitting `Modifier` records — do NOT add pairwise "if A and B" effect
  logic. That discipline is the whole point.
- **Discover the binary** (`$GODOT_BIN` → PATH → Steam path); stay Godot-4.x-version-agnostic.
- **Don't emit GUT tests here** (GUT may be absent → would fail the gate). Test scaffolding is
  `godot-test`'s job (runtime tier).

## Files

- `scaffold.py` — emit + gate runner.
- `gate.gd` — the project-load gate (injected as `__gate__.gd`, removed after).
- `templates/*.gd` — the substrate (each a readable, individually-correct GDScript class).
- `reference.md` — what each substrate file is, its StS2 grounding, and how to extend it.

<!-- Drift fuse (re-verify by 2026-12 or on misfire): templates are GDScript 4.x and pass the
     gate on engine 4.7 (2026-06-28); the gate's reload()-based check is load-bearing — do not
     "simplify" it back to load()==null. Steam fallback path tracks the installed engine. -->
