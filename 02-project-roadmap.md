# 02 — A Zero-to-Ship Roadmap Template for a Godot Game

*A generic, reusable phase plan any Godot 4.x game can adapt — empty project to release — where each phase's acceptance criteria double as the AI's definition of done.*

> See also [Principles](00-principles.md) for the *why* behind these choices, [Techniques](03-techniques.md) for the *how* of each pattern (seeded-RNG and self-play building blocks included), and the [Checklists](05-checklists.md) for the copy-paste testing and CI gates.

---

## How to use this template

This is a **scaffold for an advanced solo dev driving Claude Code** (plan mode, subagents, skills, persistent `CLAUDE.md` context) with [GUT](https://github.com/bitwes/Gut) for tests and [ComfyUI](https://comfy.org/) for assets. Adapt the phases; do not treat them as gospel sequence law. Two rules make the whole thing work:

1. **Acceptance criteria = the AI's "definition of done."** Each phase below ships a checkbox list. Paste it into your plan-mode prompt or task spec. The agent is *not done* until every box is checkable by a command you can run, not by its say-so. This is the spec-driven-development contract — the spec and its acceptance tests are the primary artifact, the code is regenerable output (see [Principles](00-principles.md)).
2. **The Ship-Necessary Razor.** Every phase ends with *what to cut*. A solo dev's scarcest resource is finishing. If a deliverable does not move the game toward a player pressing "Start" and having fun, it is deferred or deleted. The razor names the most common scope traps for that phase.

A note on **ordering with an AI agent**: agents tend to delete failing tests or write already-passing ones. Enforce the RED phase explicitly — confirm a test fails for the right reason *before* asking for the implementation. Keep diffs small and reviewable; large multi-file generations are where correctness goes to die.

A note on **how StS2 informs this**: the published Slay the Spire 2 build ships about 2,700 documented C# types whose `<summary>` comments reveal a clean subsystem taxonomy — `Models` (data definitions) vs `Entities` (runtime instances), seeded segregated RNG, a hook-based modifier pipeline, atomic versioned saves, and an "AutoSlay" self-play smoke tester.¹ We translate those *patterns* into idiomatic GDScript below. We never copy StS2 (it is C#/.NET 9 on Godot 4.5.1, and there is no code to copy — only doc summaries).¹

---

## Phase 0 — Scaffold

**Goal:** an empty-but-alive project: it boots, ticks deterministically, runs one test, and CI is green. Nothing about gameplay yet. This is the foundation every later phase stands on.

**Representative deliverables**
- `project.godot` with the rendering driver, window size, and a single autoload registered.
- An **autoload/singleton skeleton**: `Game` (root coordinator), `RNG` (seeded streams), `Events` (signal bus), `Log`. Empty but typed.
- A `constants.gd` of `const`/`static var` tables (tunables, layer names, enums).
- A **deterministic main loop** node that advances a fixed-step simulation tick decoupled from render frames.
- The first GUT test (even if it only asserts `2 + 2 == 4`) and a headless test command that exits non-zero on failure.
- A CI workflow that imports the project and runs the test suite to green.

**Autoload registration note.** Autoloads are the GDScript equivalent of StS2's `Singleton` pattern (its `SaveManager` "implements the Singleton pattern").¹ Register them in **Project → Project Settings → Autoload** (this writes an `[autoload]` block to `project.godot`); a leading `*` means the script is loaded as a singleton accessible globally by name. Keep them *thin* — coordinators and buses, not gameplay logic.

```gdscript
# RNG.gd — registered as the "RNG" autoload.
# Segregated, seeded streams: one RandomNumberGenerator per concern, so
# reward rolls can't perturb shop rolls. (StS2 uses a PlayerRngSet with
# separate Rewards/Shops/Transformations streams for exactly this reason.¹)
extends Node

enum Stream { REWARDS, SHOPS, MAP, COMBAT }

var _streams: Dictionary = {}      # Stream -> RandomNumberGenerator
var _chaotic := RandomNumberGenerator.new()   # cosmetic-only, never persisted

func seed_run(run_seed: int) -> void:
	_streams.clear()
	for s: int in Stream.values():
		var rng := RandomNumberGenerator.new()
		# Derive a distinct seed per stream so streams stay independent.
		rng.seed = hash([run_seed, s])
		_streams[s] = rng

func stream(s: Stream) -> RandomNumberGenerator:
	return _streams[s]

# Use for VFX/audio jitter only — results need not survive save/load.
func chaotic() -> RandomNumberGenerator:
	return _chaotic
```

```gdscript
# Sim.gd — a deterministic fixed-step loop. Render frames vary; the sim does not.
# Determinism is the bedrock that makes bugs reproducible from a seed and makes
# tests stable (see Phase 5 self-play and the StS2 determinism notes¹).
extends Node

const TICK_HZ := 30
const TICK_DELTA := 1.0 / float(TICK_HZ)

signal ticked(tick: int)

var _accum := 0.0
var tick: int = 0

func _process(delta: float) -> void:
	_accum += delta
	# Clamp to avoid a death spiral after a stall (e.g. a breakpoint).
	_accum = minf(_accum, TICK_DELTA * 5.0)
	while _accum >= TICK_DELTA:
		_accum -= TICK_DELTA
		tick += 1
		_step(TICK_DELTA)
		ticked.emit(tick)

func _step(_dt: float) -> void:
	pass   # Phase 1 fills this in. Pure, side-effect-light, testable.
```

> **GDScript gotcha:** `const` containers are evaluated at parse time and cannot hold values requiring runtime construction or expose methods you can mutate. For typed arrays/dicts you need to build or iterate with helpers, use `static var` instead — e.g. `static var CARD_TIERS: PackedStringArray = ["common", "uncommon", "rare"]`.

**Acceptance criteria (definition of done)**
- [ ] `godot --headless --import` completes with no errors (pre-heats the `.godot/` cache).
- [ ] `godot --headless -s res://addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit` runs and **exits 0**.
- [ ] At least one GUT test exists under `res://tests/` and passes.
- [ ] `Sim.gd` produces identical `tick` sequences for two runs with the same seed (a test asserts this).
- [ ] All four autoloads load without error and are reachable by name.
- [ ] CI runs import + tests on push and the badge is green.
- [ ] `export_presets.cfg` is committed to VCS (never gitignored).

**Ship-Necessary Razor.** Cut: a settings menu, a save system, "engine architecture" abstractions you have no second user for yet, and any rendering-driver tuning beyond picking one. You need a green loop, not a framework.

---

## Phase 1 — Core Loop & one vertical slice

**Goal:** the smallest end-to-end "is this fun?" loop — one of every screen the player touches, wired together, playable start to finish even if ugly and content-thin.

**Representative deliverables**
- The core gameplay verb implemented in `_step()` (the thing the player does over and over).
- One vertical slice: e.g. *start → one encounter → one reward → repeat or win-state* — a single thin path through every system that will exist.
- A **command seam**: gameplay state changes flow through small `Command`-like calls, and *player input* is a separate intent layer on top. StS2 makes this split explicit — a `GameAction` "is a thin wrapper around an async task that should be run in response to player input… A GameAction WRAPS these commands, and should ONLY be used for player input. NOT to wrap: dealing damage."¹ Adopt the seam early; it is what later makes undo, replay, and tests clean.

```gdscript
# A command mutates state and is independently testable. Input never calls these
# directly; an intent layer (Phase 2) does. This is the StS2 Command vs GameAction
# split translated to GDScript.¹
class_name DealDamageCommand
extends RefCounted

var target: Object
var amount: int

func execute() -> void:
	target.hp = maxi(0, target.hp - amount)
```

**Acceptance criteria (definition of done)**
- [ ] A player can reach a terminal state (win or lose) through the slice without crashes.
- [ ] The core verb is exercised by a GUT test against a seeded state, asserting the resulting state — not the rendering.
- [ ] State mutations happen only through commands; a grep confirms input handlers don't mutate model state directly.
- [ ] The slice runs headless to completion under a fixed seed and produces the same end state twice.

**Ship-Necessary Razor.** Cut: breadth (more enemy types, more cards/items), juice (animations, screen shake), and tuning balance. One of each thing, hardcoded, is correct here. If it isn't fun with one of everything, more of everything won't save it.

---

## Phase 2 — Primary Systems

**Goal:** build the load-bearing systems the rest of the game composes from, with clean seams so content is data, not code.

Use StS2's taxonomy as *inspiration* for what "primary systems" means — its namespaces split into runtime `Entities` (`Creatures`, `Players`, `Merchant`, `RestSite`), `GameActions` (intent), `Commands` (logic), `Hooks` (effect resolution), and a `Map`/`Runs` progression layer.¹ Your game's list differs, but the shape recurs:

- **Intent layer** (`GameAction`-style): wraps commands for *player input only* — play, use, end-turn, move. This is the clean seam for undo/replay/multiplayer later.¹
- **Effect / modifier resolution.** Instead of pairwise special cases ("if Vulnerable and Strength and Intangible…"), collect contributions and fold them. StS2's damage pipeline resolves `Additive` ("effects like StrengthPower"), `Multiplicative` ("effects like VulnerablePower"), and `Cap` ("effects like IntangiblePower") hook contributions into a final value.¹ Translate to a `ModifierResolver`:

```gdscript
# Effects contribute records; the resolver folds them deterministically.
# New effects compose automatically — no combinatorial special-casing.
class_name ModifierResolver
extends RefCounted

func resolve_damage(base: int, mods: Array[Dictionary]) -> int:
	var additive := 0
	var multiplier := 1.0
	var cap := 0x7FFFFFFF
	for m: Dictionary in mods:
		match m.get("kind"):
			"additive":       additive += int(m["value"])
			"multiplicative": multiplier *= float(m["value"])
			"cap":            cap = mini(cap, int(m["value"]))
	var total := int(floor(float(base + additive) * multiplier))
	return clampi(total, 0, cap)
```

- **Progression / run structure** (map, levels, waves).
- **Entity lifecycle**: spawning, state, teardown — runtime instances distinct from their data definitions (Phase 3).

**Acceptance criteria (definition of done)**
- [ ] Each primary system has a focused GUT test file exercising it in isolation.
- [ ] `ModifierResolver` (or your equivalent) has tests proving composition: two effects together yield the folded result, order-independent within a kind.
- [ ] Input flows input → GameAction → Command → state; no layer is skipped.
- [ ] No system reaches into another's internals except through its public API/signals (signals over absolute `NodePath`s — refactor-robust and AI-robust).

**Ship-Necessary Razor.** Cut: multiplayer, networking, undo/replay *implementations* (keep only the seam that makes them possible), and any system with zero content riding on it yet. Build the seam, defer the feature.

---

## Phase 3 — Content (data-driven) & second slice

**Goal:** content becomes **data you edit, not control flow you write** — so you (and the AI) add a card/enemy/level by editing a table, with a small reviewable diff and low blast radius.

This is StS2's `Models` vs `Entities` split: `Models` are definitions (`CardModel`, `EncounterModel`, `Cards`, `Relics`, `Monsters`, `Acts`); `Entities` are the runtime instances created from them.¹ For GDScript, prefer **`.gd` dictionary tables** over `.tres` resources for the bulk of content — they diff cleanly, the AI reads and edits them confidently, and you avoid the strict `.tres` structure (`ext_resource`/`sub_resource`/`load_steps`) that hand-edits break. Reserve `.tres`/`Resource` for content that benefits from the inspector or sub-resource references.

```gdscript
# content/cards.gd — data, not code. Adding a card is a reviewable data diff.
extends Node
class_name CardDB

# static var (not const): const containers are parse-time and can't expose
# the runtime construction/lookup helpers we want.
static var CARDS: Dictionary = {
	"strike": {"name": "Strike", "cost": 1, "damage": 6, "tier": "common"},
	"guard":  {"name": "Guard",  "cost": 1, "block": 5, "tier": "common"},
}

static func get_def(id: StringName) -> Dictionary:
	assert(CARDS.has(id), "unknown card id: %s" % id)
	return CARDS[id]
```

Build a **second vertical slice** here — a different character/level/mode — to prove the data layer generalizes beyond the first slice's happy path. If the second slice needs code changes to existing systems, your data seam is leaking.

**Acceptance criteria (definition of done)**
- [ ] Adding a new content entry requires **no edits to system/control-flow code** — only a data-table change.
- [ ] A data-validation test loads every content entry and asserts required fields/types and referential integrity (every referenced id resolves).
- [ ] The second slice is playable end-to-end and reuses Phase 2 systems unchanged.
- [ ] Content ids are stable `StringName`s; no system hardcodes a content id outside the data tables.

**Ship-Necessary Razor.** Cut: the *full* content set, localization tables, and a content-authoring editor/tooling. Author enough content to validate the pipeline and the second slice — fill the game out later, after save/load and performance are proven.

---

## Phase 4 — Save/Load (atomic + versioned migrations) & performance

**Goal:** the player never loses progress to a crash mid-write, and old saves keep loading as the schema evolves. Then make it fast enough.

Follow StS2's save discipline.¹ Its `GodotFileIo` exists so "all file I/O operations related to game saves… ensure proper path handling, **atomic writes**, and consistent error handling." Its `SaveManager` splits into specialized managers (settings, progress, active runs, run history) which "improves testability by allowing each save manager to be tested independently." Schema changes go through `IMigration<T>` — "strongly typed… migrations that operate on a specific save type." Cloud is best-effort: "A cloud failure must never prevent local saves from working or the game from starting."

**Atomic write pattern in GDScript:** write to a temp file, then rename over the target (rename is atomic on the same filesystem), so a crash can never leave a half-written save.

```gdscript
# Atomic, versioned save. Write temp, then swap. Stamp a schema version so
# migrations can upgrade old files on load.
const SAVE_PATH := "user://save.json"
const SAVE_VERSION := 3

func save_game(data: Dictionary) -> Error:
	data["_version"] = SAVE_VERSION
	var tmp := SAVE_PATH + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return FileAccess.get_open_error()
	f.store_string(JSON.stringify(data))
	f.close()                                   # flush before the swap
	return DirAccess.rename_absolute(
		ProjectSettings.globalize_path(tmp),
		ProjectSettings.globalize_path(SAVE_PATH))

func load_game() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	return _migrate(data)

# Each migration upgrades exactly one version step; chain them. Old saves load.
func _migrate(data: Dictionary) -> Dictionary:
	var v := int(data.get("_version", 0))
	while v < SAVE_VERSION:
		data = _MIGRATIONS[v].call(data)        # Callable per version
		v += 1
		data["_version"] = v
	return data
```

For binary/compact saves, the same swap pattern applies with `PackedByteArray` and `store_buffer()`. Keep cosmetic-only RNG (`RNG.chaotic()`) out of saved state — it intentionally need not reproduce.

**Performance** here, not earlier: profile real slices, fix the worst offenders. Cache and preload assets (StS2's `AssetCache` is "thread-safe… eliminate duplicate loads of the same asset").¹ Measure before optimizing.

**Acceptance criteria (definition of done)**
- [ ] Save is atomic: a test that interrupts/aborts between temp-write and rename leaves the previous good save intact.
- [ ] A round-trip test (`save` → `load`) reproduces game state exactly under a fixed seed.
- [ ] A migration test loads a hand-crafted `_version: N-2` fixture and upgrades it to current with correct data.
- [ ] Save subsystems (settings vs progress vs run) are independently testable with stubs.
- [ ] Cloud/optional-infra failure path is exercised and never blocks local save or startup.
- [ ] Frame time on the heaviest slice meets your target (e.g. < 16.6 ms) on your reference hardware; recorded in a perf note.

**Ship-Necessary Razor.** Cut: cloud sync (ship local-only first; the best-effort layer is additive), save compression/encryption, and micro-optimizing code that doesn't show up in a profile. A versioned local atomic save is the non-negotiable; everything else is later.

---

## Phase 5 — Observability & self-play smoke test

**Goal:** a machine can answer "does a full run still work, and does it leak?" — and you can inspect/reproduce live state. This is the gate the AI runs and reads.

StS2 ships an **AutoSlay** self-play harness: an `AutoSlayer` that "runs the game automatically for smoke testing," started with a seed, with a `Watchdog` that you `Reset(reason)` "whenever meaningful progress is made" and that "throws… if no progress for too long" and `DumpState()`s on failure; an `AutoSlayConfig` with `runTimeout`/`defaultRoomTimeout`/`watchdogTimeout`; structured `AutoSlayLog` "with consistent prefixes for easy filtering"; and a `MemoryProfiler` that "logs deltas from a baseline to detect memory/resource leaks."¹ It also ships a `DevConsole` of commands (`Heal`, `Gold`, `Travel`, `Win`, `GetLogs`…) and bakes `ReleaseInfo` (commit/version/date/hash) into builds "for reproducible bug reports."¹

Translate to GDScript:

- A **headless auto-play mode**: a `SceneTree`/`MainLoop` script (`godot --headless -s res://tools/selfplay.gd`) that seeds a run and issues valid inputs through the GameAction layer until win/lose.
- A **watchdog timer**: reset on progress; if it expires, dump the scene tree + state and exit non-zero.
- **Leak detection**: snapshot `OS.get_static_memory_usage()` (and node counts) at a baseline and log deltas per run.
- **Structured logging** with consistent prefixes to a dedicated log file, so a grep finds the failure.
- An in-game **dev console** (a `LineEdit` + a dispatch `Dictionary` of `Callable`s), compiled out / guarded in release.
- **Build identity** baked in (commit hash, version, seed) and printed at startup and on crash, so any report is reproducible.

```gdscript
# tools/selfplay.gd — headless self-play smoke test. Exit non-zero on stuck/crash
# so CI fails loudly. Run: godot --headless -s res://tools/selfplay.gd -- --seed 42
extends SceneTree

const WATCHDOG_SEC := 8.0

var _last_progress_msec := 0
var _baseline_mem := 0

func _init() -> void:
	_baseline_mem = OS.get_static_memory_usage()
	_note_progress()
	var run_seed := 42   # not `seed` — that shadows GDScript's global seed() function
	# ... seed the run via RNG.seed_run(run_seed), drive GameActions to terminal state,
	#     calling _note_progress() on every meaningful step ...
	if _stuck():
		push_error("[SELFPLAY] watchdog: no progress for %.1fs — dumping state" % WATCHDOG_SEC)
		_dump_state()
		quit(1)
	print("[SELFPLAY] ok  mem_delta=%d bytes" % (OS.get_static_memory_usage() - _baseline_mem))
	quit(0)

func _note_progress() -> void:
	_last_progress_msec = Time.get_ticks_msec()

func _stuck() -> bool:
	return (Time.get_ticks_msec() - _last_progress_msec) / 1000.0 > WATCHDOG_SEC

func _dump_state() -> void:
	print("[SELFPLAY] scene tree:"); root.print_tree_pretty()
```

**Acceptance criteria (definition of done)**
- [ ] `godot --headless -s res://tools/selfplay.gd` completes a full seeded run and **exits 0**; a deliberately broken build exits non-zero.
- [ ] The watchdog fires and dumps state when progress stalls (covered by a forced-stall test).
- [ ] Memory delta per self-play run is logged and bounded (no unbounded growth across N runs).
- [ ] Build identity (version + commit + seed) prints at startup and is attached to crash output.
- [ ] Dev console works in debug and is absent/guarded in release exports.
- [ ] Self-play runs in CI as a smoke gate.

**Ship-Necessary Razor.** Cut: a "smart" self-play AI that plays *well* (it only needs to play *legally* to completion — StS2's combat handler just "applies massive defensive buffs and plays all cards each turn"¹), a full crash-telemetry/Sentry integration (a printed build id + local log zip is enough to ship), and a fancy console UI.

---

## Phase 6 — Audio / UX polish

**Goal:** the game *feels* finished — feedback, audio, readable UI, game feel — without changing what it *is*.

**Representative deliverables**
- Audio: music + SFX hooked to game events via the signal bus. Source with AI for drafts/variation; keep humans on hero/signature cues (see [Techniques](03-techniques.md) and the asset notes in [References](references.md)).
- Juice: tweens, transitions, screen shake, hit-stop — driven by `RNG.chaotic()` so cosmetic randomness never touches saved/deterministic state.
- UX: clear affordances, controller support if relevant, accessibility passes (text size, color, input remap).
- Asset generation pipeline (ComfyUI): `POST /prompt` with an API-format workflow, poll `/history/{id}`, `/free` VRAM between batches; a character LoRA for consistent identity across generations.

**Acceptance criteria (definition of done)**
- [ ] Every core player action has audio + visual feedback.
- [ ] Polish/juice reads only cosmetic RNG; self-play (Phase 5) still produces identical deterministic end states with polish enabled.
- [ ] A first-time player reaches the core loop without a tutorial wall (validated by an actual outside playtest).
- [ ] Accessibility baseline: adjustable text size, no information by color alone, remappable inputs.
- [ ] No new console errors/warnings introduced by polish nodes.

**Ship-Necessary Razor.** Cut: bespoke shaders you can't maintain, a full original soundtrack before the game is proven fun, and polishing screens players rarely see. Polish the 20% of moments players spend 80% of their time in.

---

## Phase 7 — Testing hardening & CI

**Goal:** the suite is trustworthy enough that green = shippable, and it runs automatically on every push.

Lean on the **testability seams** built earlier — they exist precisely so tests hit real systems without production coupling. StS2 exposes `TestMode` flags, a `TestRngInjector` to "force specific cards to show up" / "force a specific order for the initial shuffle," dependency-injected save managers, and a headless `UiHelper.Click()` that "bypasses hover/focus/pause checks that can fail in headless/automated testing."¹ Translate: inject seeds/RNG into systems under test, expose deterministic overrides, and drive UI by emitting the control's signal directly in headless tests.

**Representative deliverables**
- Coverage of every primary system, the modifier resolver's composition, save round-trip + migrations, and the self-play smoke gate.
- Deterministic RNG injection / override hooks for tests.
- A CI workflow (e.g. `firebelley/godot-export` for builds; `gdUnit4-action` or GUT-via-`gut_cmdln.gd` for tests) that imports, tests, and exits non-zero on failure. Cache `.godot/` keyed on a hash of `project.godot` + `*.gd` + `*.tscn`; pre-heat with `--headless --import`.

> **Tooling choice:** GUT for a GDScript-only project (Godot 4.0+, current 9.x). If you also have C# or want scene-input simulation and built-in HTML/JUnit reports, gdUnit4 (newer versions target Godot 4.5+) is the stronger fit. StS2 being C#/.NET leans gdUnit4Net + `mono-*` CI images — your GDScript stack does not need that. See [Techniques](03-techniques.md) and the [Checklists](05-checklists.md).

**Acceptance criteria (definition of done)**
- [ ] Tests run headless and exit-code-fail on any failure (JUnit XML emitted for CI via `-goutput`).
- [ ] RED phase enforced: every new feature has a test that demonstrably failed before its implementation existed.
- [ ] Self-play smoke test is part of CI.
- [ ] CI is green on `main` and required before merge; `.godot/` cache speeds reruns.
- [ ] Flaky tests are quarantined or fixed — a flaky suite is a lying suite.

**Ship-Necessary Razor.** Cut: chasing a coverage *percentage*, testing trivial getters/UI layout pixels, and end-to-end tests where a fast unit test on the seam suffices. Test the seams and the self-play gate; that's where regressions actually hide.

---

## Phase 8 — Store page / demo / release

**Goal:** turn a finished build into a shipped, discoverable product.

**Representative deliverables**
- A **store page up early** (wishlists compound over months — the page should exist long before launch; back-fill this if you didn't).
- A **demo / vertical-slice build** for events (e.g. Steam Next Fest). At a high level: a demo is your best Next-Fest asset and your strongest wishlist driver — cadence-wise, page first, demo when the first slices are polished, Next Fest timed near launch.
- **Steam integration via a Godot Steam binding** (e.g. GodotSteam) for achievements, cloud saves, and rich presence as needed. StS2 ships Steamworks.NET + a `CloudSaveStore`; remember its cloud policy — best-effort, never blocking local saves or startup.¹
- Release builds via headless export (`--export-release <preset> <path>` — preset names are case-sensitive and must match `export_presets.cfg`; the output directory must exist).
- Baked **build identity** (Phase 5) in shipped builds for reproducible bug reports.

**Acceptance criteria (definition of done)**
- [ ] Store page is live with wishlist enabled.
- [ ] A release export builds headless in CI and launches on a clean machine.
- [ ] Steam features (achievements/cloud) work *and* degrade gracefully when offline.
- [ ] The shipped build prints its version/commit so any report is reproducible.
- [ ] Demo build (if applicable) is a self-contained, polished slice that ends with a clear wishlist call-to-action.
- [ ] A clean-machine playtest reaches the core loop with no missing-asset/driver errors.

**Ship-Necessary Razor.** Cut: day-one DLC, every-platform-at-once, and launch-window feature creep. Ship the smallest *complete* thing on one platform; expand after release with real player data.

---

## Quick reference: phases at a glance

| Phase | Goal in one line | The gate that proves it |
| --- | --- | --- |
| 0 Scaffold | Boots, ticks deterministically, CI green | Headless tests exit 0; seeded ticks reproduce |
| 1 Core loop | One fun, end-to-end slice | Reach a win/lose state, twice, same seed |
| 2 Systems | Composable load-bearing systems | Modifier composition + per-system tests pass |
| 3 Content | Content is data, not code | Add an entry with zero code edits; validation passes |
| 4 Save & perf | No lost progress; fast enough | Atomic save survives interrupt; migration upgrades old fixture |
| 5 Observability | Machine-checkable "still works?" | Self-play exits 0; memory bounded; build id printed |
| 6 Polish | Feels finished | Feedback on every action; deterministic end state unchanged |
| 7 Testing & CI | Green = shippable | RED enforced; self-play in CI; main green |
| 8 Release | Shipped & discoverable | Page live; release export launches on clean machine |

---

¹ All StS2 claims are from the project's shipped C# XML documentation summaries, recorded read-only in `STS2_EVIDENCE.md` (no decompilation, no `.pck` extraction). StS2 is Godot 4.5.1 / C# .NET 9; every code example above is original GDScript for Godot 4.x. Tooling commands, URLs, and CI facts are from [References](references.md).
