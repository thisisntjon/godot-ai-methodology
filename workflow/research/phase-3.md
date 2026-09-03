# Phase 3 — Parse-gate spike (results)

_Date: 2026-06-28 · status: DONE_

## Goal
Retire the load-bearing build mechanism before building `godot-scaffold` (C2): can we
discover the Godot binary and run a **project-load gate** that reliably distinguishes a
clean GDScript project from a broken one (esp. cross-file `class_name` resolution failures)?

## What was built (`workflow/spike/`)
- `godot_gate.py` — discovers binary (`$GODOT_BIN`→PATH→Steam path), runs `--import` (builds
  the global class cache), injects `gate.gd` as `__gate__.gd` (no-overwrite), runs it headless,
  removes it. Fails on non-zero exit **or** error markers in output.
- `gate.gd` — `SceneTree` script; recursively loads every `res://*.gd`, and for GDScripts
  calls `GDScript.reload()` and checks the result. Exits 0 iff all compile.
- `sample_clean/` (modifier.gd + resolver.gd, cross-file `class_name`) and `sample_broken/`
  (resolver.gd references `GateModifier` but modifier.gd is absent → cross-file failure).
- `fixtures/` — `bad_godot3.gd`, `bad_determinism.gd`, `good_sample.gd` for C3 (Phase 6).

## Result
- Binary: **Godot 4.7.stable.steam** at `C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe` (not on PATH). Runs headless, exit 0.
- CLEAN → `GATE: exit=0 marker=None -> PASS`.
- BROKEN → `GATE-FAIL load: res://scripts/resolver.gd` … `exit=1 marker=SCRIPT ERROR -> FAIL`.

## Key finding (load-bearing for C2 `godot-scaffold` and S1 `godot-test`)
**`load()` alone is NOT a sufficient gate.** On the broken project, `load()` returned a
*non-null* GDScript object despite a parse error, so a naive `load()==null` check **passed a
broken script** (false negative). The reliable signal is **`GDScript.reload() == OK`** per
script, backed up by scanning engine output for `SCRIPT ERROR` / `Parse Error` /
`Failed to load script`. The `--import` pass is what builds the class cache so cross-file
`class_name` refs resolve; the gate run then recompiles. C2/S1 MUST use this reload-based
gate, not per-file `--check-only` and not bare `load()`.

## Caveats / notes for later phases
- Pure `--headless` renders no frame → screenshots (S3) need a headed run or offscreen context.
- Gate uses the installed 4.7 binary; projects may target an older 4.x — keep gate
  version-agnostic (it only needs the project to open).
- `gate.gd` skips `.godot`/`.import`; consider also skipping `addons/` for third-party code.
