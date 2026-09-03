# Runtime Tier — Spec (gated; build after enablement)

_Date: 2026-06-28 · status: SPEC (not built) · Phase 7 deliverable_

The runtime/verification skills are high-value but **gated**: they need the game actually
running under the assistant's control. The CORE skills (`godot-context`, `godot-scaffold`,
`godot-guard`) are env-independent and already built; these are the next tranche.

## Gate condition (must ALL be true before building S1–S4)
1. **Headless `godot` proven** — binary discovery green (`$GODOT_BIN`→PATH→Steam path) and
   `--headless --version` runs. ✅ already verified (4.7.stable, Phase 3).
2. **Test substrate present** — GUT (or gdUnit4) installed in the target project. ❌ today
   (env-probe: GUT not installed) → S1 must scaffold it.
3. **Runtime bridge proven (for S2–S4)** — a Godot MCP / autoload bridge installed and
   answering in-env at the project's Godot version. ❌ not yet (ecosystem mature — Erodenn
   `godot-mcp-runtime` zero-footprint autoload pattern, `tugcantopaloglu/godot-mcp`,
   Godot MCP Pro — but not wired locally). **Do not build S2–S4 until a probe returns green.**

## One-time enablement (do once, then S2–S4 unlock)
1. Install a runtime MCP (recommend the **Erodenn zero-footprint auto-injected autoload**
   pattern so projects need no committed bridge code). Pin to the project's Godot 4.x version.
2. Register it with Claude Code; **curate the tool surface** (servers expose 149–175 tools —
   expose only run / read-scene-tree / input / screenshot / read-logs to avoid context blow).
3. Write a `godot-runtime-probe` check: start the project headless via the bridge, read back
   the scene tree root, drive one input, capture one screenshot, read the log. Green = unlock.

---

## S1 · `godot-test`  (spec — deep; build first, needs only gate #1–#2)
- **Trigger:** "add/run Godot tests", "set up GUT", "test this GDScript", `/godot-test`.
- **Inputs:** project dir; optionally a target script/class to test.
- **Outputs:** GUT installed under `addons/gut/` if absent; test files under `tests/`; a headless
  run with parsed pass/fail + exit code.
- **Steps:** (1) discover binary; (2) ensure GUT (download/scaffold `addons/gut/` + `.gutconfig`
  if missing — never assume it); (3) generate/locate tests (RED first, per the red-first TDD workflow); (4) run
  `"$GODOT_BIN" --headless --path . -s res://addons/gut/gut_cmdln.gd -gdir=res://tests -gexit`;
  (5) parse summary, surface failures as file:line, set exit code. Reuse the Phase-3
  **reload() gate** as a pre-test compile check so test failures aren't masked by parse errors.
- **Acceptance test:** on a project with one passing + one failing GUT test, the skill reports
  1 pass / 1 fail and exits non-zero; on all-pass, exits 0.
- **Failure it prevents:** "tests" that never run (no GUT/headless wiring), or green runs that
  silently skipped compile-broken files.
- **Composition:** the Godot executor for the TDD RED→GREEN loop; pairs with `godot-guard`
  (compile/idiom) and `godot-scaffold` (test seams).

## S2 · `godot-smoke`  (stub — needs gate #3)
Self-play smoke test: drive valid inputs through a run via the runtime bridge; a **watchdog**
dumps scene-tree state on stall; a **memory-delta** check (`OS.get_static_memory_usage()`
baseline vs end) flags leaks. Acceptance: a seeded self-play run completes within a timeout and
reports no leak over N loops. Prevents soft-locks/leaks shipping unseen. (StS2 `AutoSlayer` /
`Watchdog` / `MemoryProfiler`.)

## S3 · `godot-inspect` + `godot-verify`  (stub — needs gate #3)
`godot-inspect`: read the live scene tree / node props headlessly. `godot-verify`: run the game,
drive an input, **screenshot**, and confirm a change visually (pairs with an existing
screen-capture helper). Note: pure `--headless` renders no frame → visual verify needs a headed/offscreen
context. Prevents "can't see the running game" blind spots.

## S4 · `godot-observe`  (stub — env-independent-ish, low gate)
Scaffold an in-game **dev console** (LineEdit + command dict, guarded out of release), structured
logging, and baked build/version identity (commit/version/hash) for reproducible bug reports.
(StS2 `DevConsole` / `ReleaseInfo`.) Could actually build alongside CORE later — it's mostly
scaffolding, not live automation.

---

## Build order once unlocked
S1 (`godot-test`) → S4 (`godot-observe`, cheap) → enablement → S2/S3 (bridge-dependent).
Keep the set **curated** — resist the documented sprawl failure (49-agent / 175-tool packs).
