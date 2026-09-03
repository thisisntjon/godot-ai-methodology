# 05 — Quick-Reference Checklists

> Copy-paste these. Terse gates for AI-assisted Godot 4.x dev — each item is a stop-sign, not a suggestion. The "how" lives in the sibling docs; this file is the scannable layer on top.

How to use: paste the relevant block into your spec, PR description, or `CLAUDE.md` task. An item with an unchecked box is a blocker. When a Claude Code agent reports "done," run it against the matching checklist before you believe it. Cross-links point at [00-principles.md](00-principles.md), [03-techniques.md](03-techniques.md), [04-ai-collaboration-patterns.md](04-ai-collaboration-patterns.md), and [references.md](references.md) for the reasoning.

---

## 1. Per-feature checklist

One pass per vertical slice. Drives the agent loop: spec → plan → RED → GREEN → verify → review → commit.

```text
SPEC
[ ] One-paragraph intent: what player-facing behavior changes, and why.
[ ] Acceptance criteria are testable (EARS-style "When X, the system shall Y").
[ ] NON-GOALS listed explicitly (what this slice will NOT do / touch).
[ ] Blast radius named: which files/systems change, which stay frozen.
[ ] Determinism stance declared: does this touch seeded RNG? (see §4)
[ ] Data vs logic decided: is this a data row, or new control flow?

PLAN (Claude Code plan mode — review before any code)
[ ] Plan lists files to add/edit and the test files first.
[ ] Plan reuses existing seams (modifier resolver, hooks, command layer) —
    no new special-case branches where composition would do.
[ ] You approved the plan. Disagreements resolved BEFORE implementation.

TESTS — RED
[ ] New tests written first and committed/visible.
[ ] Suite run shows the new tests FAILING for the right reason.
[ ] Agent did NOT delete/rewrite a test to make it pass, nor write an
    already-green test. (Agents do both; verify the red.) — see [04](04-ai-collaboration-patterns.md)

IMPL — GREEN
[ ] Minimal code to pass the new tests; no drive-by refactors.
[ ] Determinism-affecting code uses an injected RNG, not global randi(). (§4)
[ ] New content added as data where possible (one reviewable row).

VERIFY
[ ] Full suite passes headless (not just the new tests):
    godot --headless -s res://addons/gut/gut_cmdln.gd \
      -gdir=res://tests -ginclude_subdirs -gexit
[ ] Game actually RUNS and the feature works in-editor (not just green tests).
[ ] No new errors/warnings in the Godot output panel.

REVIEW
[ ] Diff is small and reviewable. Large diff => split the slice.
[ ] Second-model / human auditor pass on non-trivial logic. — see [references.md](references.md)
[ ] Context file (CLAUDE.md) updated if a convention/seam changed.

COMMIT
[ ] Pre-commit checklist (§2) passes.
[ ] Commit message records the DECISION and the non-goals, not just the diff.
```

---

## 2. Pre-commit checklist

The fast gate. Runs in under a minute; no excuses to skip.

```text
[ ] Full test suite green headless (GUT exit code 0). — see [04](04-ai-collaboration-patterns.md)
[ ] Parse/type check clean:
    godot --headless --check-only -s res://tools/check.gd   (or --import)
[ ] No leftover debug spew: stray print(), breakpoint(), or commented-out blocks.
[ ] No secrets/abs paths/user names committed (grep your diff).
[ ] export_presets.cfg committed if presets changed (never .gitignore it). — [refs](references.md)
[ ] .tscn/.tres edits done via the editor, not hand-typed UIDs/load_steps. — [04](04-ai-collaboration-patterns.md)
[ ] Generated/import artifacts handled per repo policy (.godot/ ignored).
[ ] Diff scoped to one concern. Unrelated changes => separate commit.
[ ] Message states WHAT changed + WHY + non-goals; references the spec/issue.
```

---

## 3. Pre-release checklist

The slow gate. Run before tagging a build. Mirrors the shipping disciplines observed in Slay the Spire 2 (`STS2_EVIDENCE.md`).

```text
SAVE / LOAD
[ ] Save -> quit -> load round-trips with identical state (new game).
[ ] Save from PREVIOUS schema version loads via migration; assert post-state.
    StS2 ships a typed IMigration<T> + MigratingData JSON API for exactly this.
[ ] Writes are atomic (temp file + rename), never partial on crash.
    StS2: "All file I/O ... should use this class to ensure ... atomic writes."
[ ] Cloud/optional infra failure NEVER blocks local save or game start.
    StS2 cloud policy: "A cloud failure must never prevent local saves from
    working or the game from starting." — keep optional infra best-effort.

DETERMINISM
[ ] A fixed seed reproduces an identical run (same rewards/shops/shuffle). (§4)
[ ] Segregated RNG streams unchanged: cosmetic ("chaotic") randomness does NOT
    perturb gameplay streams. StS2 separates Rewards/Shops/Transformations
    streams from a non-deterministic "Chaotic" RNG. — see [03](03-techniques.md)
[ ] Bug-repro-from-seed still works (paste seed -> same failure).

SELF-PLAY SMOKE TEST
[ ] Headless auto-play completes a full run on N seeds without crashing.
    Analogue of StS2 AutoSlayer: "Runs the game automatically for smoke testing."
[ ] Watchdog catches stalls: no meaningful progress within timeout => dump
    state + fail (don't hang CI). StS2 Watchdog.Check() throws on no-progress.
[ ] On failure it dumps scene-tree/state context for debugging.

LEAKS / LONG RUN
[ ] Static memory delta over a long auto-play is flat (no monotonic growth).
    StS2 MemoryProfiler "logs deltas from a baseline to detect ... leaks."
    var base_mem := OS.get_static_memory_usage()  # snapshot, compare deltas
[ ] Orphan node count stable (print_orphan_nodes() at run boundaries).
[ ] RefCounted resources released (free cached TextParagraph/atlas/etc.).

CI / BUILD
[ ] Headless CI is green on the release commit (tests + export). — see [04](04-ai-collaboration-patterns.md)
[ ] Release export produced from a clean checkout with matching templates.
[ ] BUILD IDENTITY baked in: version + commit + date + assembly/content hash
    embedded and shown in-game/logs. StS2 bakes Commit/Version/Date/Branch/
    MainAssemblyHash via ReleaseInfo for reproducible bug reports. (snippet below)
[ ] Renderer launch paths verified (e.g. Vulkan + D3D12/Metal fallback).

ERROR REPORTING (opt-in)
[ ] Crash/telemetry reporting is OFF by default and OPT-IN by the player.
[ ] Opt-in actually toggles reporting on/off; verify a test event is sent
    only when enabled. StS2 ships a SentryConsoleCmd to test the path.
[ ] A "collect logs" path zips logs + saves for manual reports.
    StS2 GetLogsConsoleCmd "collects + zips logs/saves/core dumps."
```

Build-identity stamp (generate at build time; read at runtime):

```gdscript
# res://build_info.gd  — overwritten by CI before export
class_name BuildInfo
extends RefCounted

const VERSION: String = "v0.0.0"        # CI: from tag
const COMMIT: String = "unknown"        # CI: git rev-parse --short HEAD
const BUILD_DATE: String = "1970-01-01" # CI: date -u +%Y-%m-%d
const CONTENT_HASH: String = "0000"     # CI: hash of packed content

static func line() -> String:
    return "%s (%s) %s #%s" % [VERSION, COMMIT, BUILD_DATE, CONTENT_HASH]
```

Opt-in reporting gate (best-effort, never blocks):

```gdscript
# Crash/error upload is OFF until the player opts in.
var reporting_enabled: bool = false  # persisted in user settings

func report_error(payload: Dictionary) -> void:
    if not reporting_enabled:
        return
    # Best-effort: a failed upload must never crash or stall the game.
    var err := _uploader.send(payload)   # async, fire-and-forget
    if err != OK:
        push_warning("error report dropped (best-effort): %d" % err)
```

---

## 4. "Is my codebase AI-friendly?" audit

Score yourself. Each "no" is a place an agent will guess wrong and you'll pay for it. Deep dives in [00-principles.md](00-principles.md) and [03-techniques.md](03-techniques.md).

```text
DETERMINISM QUARANTINED
[ ] All gameplay randomness flows through injectable RandomNumberGenerator
    instances with explicit .seed/.state — never bare randi()/randf().
[ ] RNG streams segregated by concern (rewards, shops, transforms, ...), so one
    feature's rolls can't shift another's. (StS2: PlayerRngSet streams.)
[ ] A separate "chaotic" stream handles cosmetic-only randomness and is fenced
    off from anything that affects save state or replay. (§3, [03](03-techniques.md))

DATA-DRIVEN CONTENT
[ ] New cards/items/enemies are DATA rows (dict tables or .tres), not new
    classes/branches. StS2 splits Models (definitions) from Entities (runtime).
[ ] Adding content touches data files, not control flow => tiny reviewable diff.
[ ] Calculated/derived values are declared declaratively, not hand-inlined.

INTENT vs LOGIC SEPARATED
[ ] Player-input intent is a thin layer over reusable logic units.
    StS2: a GameAction WRAPS Commands and "should ONLY be used for player input";
    logic like "deal damage" lives in Commands, not in the input wrapper.
[ ] This seam enables undo/replay/networking without touching game logic.

MODIFIER COMPOSITION, NOT SPECIAL-CASING
[ ] Effects CONTRIBUTE to a resolver (additive / multiplicative / cap) instead
    of pairwise if-this-buff-and-that-debuff branches.
    StS2 ModifyDamage hooks: Additive (Strength), Multiplicative (Vulnerable),
    Cap (Intangible) fold to a final number. New effects compose for free.
[ ] No combinatorial special cases an agent must enumerate. — see [03](03-techniques.md)

TEST SEAMS PRESENT
[ ] Dependency injection: systems take their RNG/clock/store as args, not via
    hard singletons. StS2 SaveManager has "Constructor with dependency injection."
[ ] RNG/shuffle/draw can be overridden for tests (force specific cards/order).
    StS2 TestRngInjector: SetCombatCardGenerationOverride / SetInitialShuffleOverride.
[ ] UI is drivable headless (emit the pressed signal directly, bypass hover/
    focus/pause). StS2 UiHelper.Click() does exactly this for automation.
[ ] A "test mode" flag exists to relax timing/animation gates. — [03](03-techniques.md)

DEV CONSOLE / LOGS
[ ] In-game dev console (LineEdit + dispatch dict) for state pokes
    (give gold, heal, win, travel), compiled out / guarded in release.
    StS2 DevConsole: GoldConsoleCmd, HealConsoleCmd, WinConsoleCmd, TravelConsoleCmd...
[ ] Structured logs with consistent prefixes you can grep, to file + stdout.
    StS2 AutoSlayLog: "consistent prefixes for easy filtering ... dedicated log."

CONTEXT FILE CURRENT
[ ] CLAUDE.md exists and names the seams above (RNG policy, data tables,
    intent/logic split, resolver, test mode) so the agent stops guessing.
[ ] It's concise and cascades correctly up the dir tree. — see [references.md](references.md)
[ ] Updated in the same PR whenever a convention changes.

SMALL SCRIPTS
[ ] Files do one thing; long god-scripts split. An agent can hold a whole file
    in context and a reviewer can read the whole diff.
[ ] Wiring prefers signals / @export refs / groups over absolute NodePaths
    (refactor-robust AND agent-robust). — see [04](04-ai-collaboration-patterns.md)

DOCS / COMMENTS
[ ] Public types/functions carry intent comments (the WHY), not restated code.
    StS2 averages ~36 lines of doc per type — that legibility is why an agent
    can read intent instead of reverse-engineering it.
[ ] Non-obvious invariants/gotchas are written down at the call site.
[ ] Naming is mechanical and consistent (predictable prefixes/conventions).
```

---

## 5. CI setup checklist

Wire these jobs once. Specifics and sources in [04-ai-collaboration-patterns.md](04-ai-collaboration-patterns.md) and [references.md](references.md).

```text
HEADLESS TEST JOB
[ ] Runs Godot headless (--headless disables GPU + audio drivers).
[ ] Pre-heats the import cache BEFORE tests:  godot --headless --import
[ ] Runs the suite and fails the build on a nonzero exit:
    godot --headless -s res://addons/gut/gut_cmdln.gd \
      -gdir=res://tests -ginclude_subdirs -gexit
[ ] Emits JUnit XML for the CI UI (GUT: -goutput; gdUnit4: auto HTML+JUnit).
[ ] If using C# tests, use gdUnit4Net + a mono-capable runner.
    (StS2 is C#/.NET 9 -> favors gdUnit4Net + barichello/godot-ci:mono-* images.)

EXPORT JOB
[ ] Runs after tests pass; uses CLI export with a preset that matches
    export_presets.cfg EXACTLY (names are case-sensitive):
      godot --headless --export-release "<Preset>" <out/path/game.exe>
[ ] Output directory is created first (export won't make it for you).
[ ] export_presets.cfg is committed (NOT gitignored).
[ ] Build-identity stamp written into the project before export (§3 snippet).
[ ] Engine + export-template versions match the editor version exactly.
[ ] Optional: firebelley/godot-export action
    (godot_executable_download_url, godot_export_templates_download_url,
     relative_project_path; optional cache / archive_output / presets_to_export).

CACHING
[ ] Export templates cached/restored across runs (slowest download — cache it).
[ ] .godot/ import cache cached, keyed on a hash of project.godot + *.gd + *.tscn,
    so headless imports don't recompute every run.
[ ] Docker image (e.g. barichello/godot-ci, mono-* for C#) pinned to a version.
[ ] Cache key busts on engine-version bump (stale templates => silent failures).
```

Reference job shape (GitHub Actions; adapt to your runner):

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container: barichello/godot-ci:4.5-stable   # mono-4.5-stable for C#
    steps:
      - uses: actions/checkout@v4
      - name: Cache import
        uses: actions/cache@v4
        with:
          path: .godot
          key: godot-${{ hashFiles('project.godot', '**/*.gd', '**/*.tscn') }}
      - name: Import (pre-heat)
        run: godot --headless --import
      - name: Tests
        run: |
          godot --headless -s res://addons/gut/gut_cmdln.gd \
            -gdir=res://tests -ginclude_subdirs -gexit
```

---

## See also

- [00-principles.md](00-principles.md) — the seams the §4 audit checks for (determinism, data/logic, intent/logic, composition).
- [03-techniques.md](03-techniques.md) — seeded RNG streams, save/migration, modifier resolver, self-play harness patterns.
- [04-ai-collaboration-patterns.md](04-ai-collaboration-patterns.md) — RED/GREEN with agents, GUT, headless runs, signal/UID wiring.
- [references.md](references.md) — sourced facts for every tool/command/URL above.
- `STS2_EVIDENCE.md` — the read-only Slay the Spire 2 observations these checklists distill.
```