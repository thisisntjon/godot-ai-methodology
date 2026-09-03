# 03 — Technique Catalog

> A catalog of concrete, reusable techniques for AI-assisted Godot 4.x game
> development — each with what it is, the Slay the Spire 2 evidence that
> validates it, runnable GDScript, and how it pays off when an AI agent is
> writing the code. See [References](references.md) for sourcing.

These ten techniques are the load-bearing patterns. They are deliberately
*mechanical*: each one turns a class of decisions into a single learnable shape,
which is exactly what makes them safe for an LLM to extend without re-deriving
intent every time. The recurring theme — visible in Slay the Spire 2's shipped
C# XML docs — is **segregation and seams**: separate concerns into named,
injectable, testable units so a change has a small blast radius and a machine can
verify it.

All StS2 claims below are grounded in `STS2_EVIDENCE.md` (verified
read-only observations of `sts2.xml`, the game's shipped documentation). StS2 is
C#/.NET 9 on Godot 4.5.1; every code block here is **original GDScript 4.x** that
translates the documented *pattern*, not the code (there is none to copy).

---

## 1. Seeded, segregated RNG

**What.** One `RandomNumberGenerator` per gameplay concern, each independently
seeded from a master run seed, with its `.state` saved and restored alongside the
save file — *plus* a separate "chaotic" stream for cosmetic randomness that is
deliberately **not** persisted. Determinism is opt-in per concern, so consuming
one stream never desyncs another.

**StS2 evidence.** StS2 ships a custom `Rng`: *"A custom random class which
allows predictable results when utilizing seeds,"* with a constructor *"for
creating an RNG for a specific piece of content during a run … unique among: The
run, The player SLOT, The ID of the content passed."* It segregates streams in
`PlayerRngSet` — `Rewards` (*"What cards are generated for rewards"*), `Shops`
(*"What the different shops are selling"*), `Transformations`. Crucially it also
ships `Rng.Chaotic`: *"A non-deterministic RNG instance. This will not produce the
same results after saving and loading. Good for when we need to randomize things
that don't impact gameplay."* The backing PRNG is `MegaRandom` (Xoshiro256\*\*).

**GDScript how-to.**

```gdscript
# rng_set.gd — segregated, seedable RNG streams for a run.
class_name RngSet
extends RefCounted

# Each gameplay concern gets its own stream. Consuming one never perturbs another.
var rewards: RandomNumberGenerator = RandomNumberGenerator.new()
var shops: RandomNumberGenerator = RandomNumberGenerator.new()
var transforms: RandomNumberGenerator = RandomNumberGenerator.new()

# Cosmetic-only. Never seeded deterministically, never saved. Desync-safe.
var chaotic: RandomNumberGenerator = RandomNumberGenerator.new()

const _STREAMS: PackedStringArray = ["rewards", "shops", "transforms"]

func seed_run(master_seed: int) -> void:
    # Derive a distinct, stable sub-seed per concern from the master seed so the
    # same run seed always reproduces the same streams.
    for name in _STREAMS:
        var s: RandomNumberGenerator = get(name)
        s.seed = hash("%d:%s" % [master_seed, name])
    chaotic.randomize() # explicitly non-deterministic

# Save: capture seed + state so a reloaded run continues identically.
func to_state() -> Dictionary:
    var out: Dictionary = {}
    for name in _STREAMS:
        var s: RandomNumberGenerator = get(name)
        out[name] = {"seed": s.seed, "state": s.state}
    return out # note: `chaotic` is intentionally omitted

func from_state(data: Dictionary) -> void:
    for name in _STREAMS:
        if data.has(name):
            var s: RandomNumberGenerator = get(name)
            s.seed = int(data[name]["seed"])
            s.state = int(data[name]["state"])
    chaotic.randomize()
```

`state` is the live cursor of the generator; persisting `seed` *and* `state`
means a reloaded run draws exactly the next value it would have. The chaotic
stream is omitted from `to_state()` by design — that is what makes it safe for
screen-shake or particle jitter without corrupting save reproducibility.

**AI-leverage.** A bug report becomes `seed=12345, stream=rewards`. An agent can
reproduce it deterministically, write a failing test against that seed, fix, and
prove the fix — no flaky "works on my machine." Segregation also means an agent
adding a new shop feature touches only `shops` and cannot accidentally shift the
reward sequence in an unrelated regression test.

---

## 2. Data-driven content

**What.** Express content (cards, enemies, relics, encounters) as **data**, not
control flow. Adding content is editing a table; the engine that reads the table
never changes. Two viable carriers in Godot: `.gd` const/`static var`
dictionaries, or `Resource` (`.tres`) files.

**StS2 evidence.** StS2 splits `Core.Models` (86 types: definitions like
`CardModel`, `EncounterModel`, `Cards`, `Relics`, `Powers`, `Monsters`,
`Modifiers`) from `Core.Entities` (42 types: runtime instances —
`Creatures`, `Players`, runtime `Cards`). Models are the data; Entities are the
live state spun up from that data. There is even a `SingletonModel`: *"A model
which is instantiated once for an entire run."* The split is the whole point —
content authors edit Models; the simulation operates on Entities.

**GDScript how-to.** Prefer `.gd` dictionary tables for AI-friendliness: they
diff cleanly as plain text, an agent can append an entry without opening the
editor, and there are no UID/`.import` side effects (see [References](references.md)
on `.tres` hand-edit fragility).

```gdscript
# card_db.gd — data-driven card definitions.
extends Node

# CAVEAT: `const` containers are frozen at parse time and cannot hold values
# computed by functions, nor expose helper methods. For a table you want to
# query with methods, use `static var` instead of `const`.
static var CARDS: Dictionary = {
    "strike": {
        "name": "Strike", "cost": 1, "type": "attack",
        "base_damage": 6, "tags": ["starter"],
    },
    "defend": {
        "name": "Defend", "cost": 1, "type": "skill",
        "base_block": 5, "tags": ["starter"],
    },
}

static func get_card(id: StringName) -> Dictionary:
    assert(CARDS.has(id), "unknown card id: %s" % id)
    return CARDS[id]

static func ids_with_tag(tag: String) -> Array[StringName]:
    var out: Array[StringName] = []
    for id in CARDS:
        if tag in CARDS[id]["tags"]:
            out.append(id)
    return out
```

The `const` vs `static var` distinction is the one trap. A `const Dictionary` is
fine for a literal table, but the moment you want a derived default or to attach
query helpers in the same script, switch to `static var` — `const` values are
baked at parse time and cannot be the result of a function call. Use `.tres`
`Resource`s instead when artists/designers need an inspector UI or when the
content references scenes/textures by `uid://`.

**AI-leverage.** New content is a low-risk, reviewable diff (a new dict entry),
not a code path an agent could get subtly wrong. The simulation code stays small
and stable, so the agent's context budget goes to *behavior* it must reason
about, not boilerplate it must regenerate.

---

## 3. The modifier-resolution pipeline

**What.** Instead of pairwise special-casing ("if Vulnerable and Strength
and Intangible …"), every effect contributes a **modifier record** of one of
three kinds — Additive, Multiplicative, or Cap — and a single resolver folds them
in a fixed order into a final value, with clamps. New effects compose
automatically; there is no combinatorial blow-up.

**StS2 evidence.** StS2's `Hook` is *"A static class containing all of the
gameplay hooks"* (`BeforeAttack`, `AfterModifyingDamageAmount`, …). Its
`ModifyDamageHookType` enum is exactly this taxonomy: `Additive` — *"Additive
damage hooks from effects like StrengthPower"*; `Multiplicative` —
*"Multiplicative damage hooks from effects like VulnerablePower"*; `Cap` —
*"Damage-capping hooks from effects like IntangiblePower"*; `All` — *"Include all
ModifyDamage hooks."* Backed by `AbstractModel.ModifyDamageAdditive/
Multiplicative/Cap()`. This is a modifier-resolution pipeline by another name.

**GDScript how-to.** The canonical record and resolver:

```gdscript
# modifier.gd — one record per contribution.
class_name Modifier
extends RefCounted

enum Kind { ADDITIVE, MULTIPLICATIVE, CAP }

var kind: Kind
var value: float
var source: StringName # for debugging/ordering, e.g. &"strength"

static func make(kind: Kind, value: float, source: StringName) -> Modifier:
    var m := Modifier.new()
    m.kind = kind
    m.value = value
    m.source = source
    return m
```

```gdscript
# modifier_resolver.gd — folds records into a final value, in a fixed order.
class_name ModifierResolver
extends RefCounted

# Resolution order is FIXED and total: additives first, then multipliers,
# then caps, then clamp to [floor, +inf). Determinism comes from a stable order,
# so we sort same-kind records by source before folding.
static func resolve(base: float, mods: Array[Modifier], floor_value: float = 0.0) -> int:
    var additive: float = 0.0
    var multiplier: float = 1.0
    var cap: float = INF

    var ordered := mods.duplicate()
    ordered.sort_custom(func(a: Modifier, b: Modifier) -> bool:
        if a.kind != b.kind:
            return a.kind < b.kind
        return String(a.source) < String(b.source))

    for m in ordered:
        match m.kind:
            Modifier.Kind.ADDITIVE:
                additive += m.value
            Modifier.Kind.MULTIPLICATIVE:
                multiplier *= m.value
            Modifier.Kind.CAP:
                cap = minf(cap, m.value)

    var result: float = (base + additive) * multiplier
    result = minf(result, cap)
    result = maxf(result, floor_value)
    return int(result) # damage is integral; round toward zero deliberately
```

A couple of GUT tests pin the math (see the testing doc for harness setup):

```gdscript
# test_modifier_resolver.gd
extends GutTest

func test_strength_is_additive_before_vulnerable_multiplier() -> void:
    # 6 base + 3 Strength = 9, then x1.5 Vulnerable = 13.5 -> 13
    var mods: Array[Modifier] = [
        Modifier.make(Modifier.Kind.ADDITIVE, 3.0, &"strength"),
        Modifier.make(Modifier.Kind.MULTIPLICATIVE, 1.5, &"vulnerable"),
    ]
    assert_eq(ModifierResolver.resolve(6.0, mods), 13)

func test_cap_clamps_after_additive_and_multiplier() -> void:
    # (10 + 90) * 2 = 200, capped at 1 by Intangible
    var mods: Array[Modifier] = [
        Modifier.make(Modifier.Kind.ADDITIVE, 90.0, &"rage"),
        Modifier.make(Modifier.Kind.MULTIPLICATIVE, 2.0, &"weak_enemy"),
        Modifier.make(Modifier.Kind.CAP, 1.0, &"intangible"),
    ]
    assert_eq(ModifierResolver.resolve(10.0, mods), 1)

func test_floor_prevents_negative_damage() -> void:
    var mods: Array[Modifier] = [Modifier.make(Modifier.Kind.MULTIPLICATIVE, 0.0, &"miss")]
    assert_eq(ModifierResolver.resolve(8.0, mods), 0)
```

**AI-leverage.** Adding "deal 50% more damage to Bleeding enemies" is one new
`Modifier.make(MULTIPLICATIVE, 1.5, &"bleed_synergy")` at the contribution site —
the resolver is untouched and *cannot* be broken by the addition. The fixed
resolution order is the contract; the GUT tests are the executable spec an agent
must keep green. This is the single highest-leverage pattern for letting an LLM
add combat content safely.

---

## 4. Intent vs logic (command queue + executor)

**What.** Separate *player intent* (an enqueued, replayable command — "play card
#3 on enemy #1") from *game logic* (the small mutations that intent triggers).
Intent goes through a queue and an executor; logic is plain functions. This seam
is where undo, replay, networking, and AI self-play all plug in.

**StS2 evidence.** StS2 is explicit: a `GameAction` is *"a thin wrapper around an
async task that should be run in response to player input … small units of logic
are handled by Commands … A GameAction WRAPS these commands, and should ONLY be
used for player input."* Examples to wrap: *playing a card, drinking a potion,
ending turn*; explicitly **not** to wrap: *dealing damage*. The `ActionExecutor`
is *"Responsible for pulling actions from the … queue and executing them."* Its
multiplayer cousins (`EndPlayerTurnAction`, `UndoEndPlayerTurnAction`,
`VoteForMapCoordAction`) show why the seam matters: undo and networked voting
live at the *intent* layer, not the logic layer.

**GDScript how-to.**

```gdscript
# game_action.gd — intent. One per discrete player decision.
class_name GameAction
extends RefCounted

var kind: StringName       # &"play_card", &"end_turn", &"use_potion"
var args: Dictionary = {}  # e.g. {"card": &"strike", "target": 1}

func _init(kind: StringName, args: Dictionary = {}) -> void:
    self.kind = kind
    self.args = args
```

```gdscript
# action_executor.gd — pulls intent off the queue, dispatches to logic.
class_name ActionExecutor
extends RefCounted

signal action_executed(action: GameAction)

var _queue: Array[GameAction] = []
var _combat: CombatState # injected; the logic operates on this

func _init(combat: CombatState) -> void:
    _combat = combat

func enqueue(action: GameAction) -> void:
    _queue.append(action) # could also broadcast to peers here for multiplayer

func execute_all() -> void:
    while not _queue.is_empty():
        var action: GameAction = _queue.pop_front()
        _dispatch(action)
        action_executed.emit(action)

func _dispatch(action: GameAction) -> void:
    match action.kind:
        &"play_card": _combat.play_card(action.args["card"], action.args["target"])
        &"end_turn":  _combat.end_turn()
        &"use_potion": _combat.use_potion(action.args["potion"])
        _: push_error("unknown action kind: %s" % action.kind)
```

The logic — `_combat.play_card(...)` — knows nothing about queues, input, or the
network. It is a pure-ish mutation that GUT can call directly. The executor is
the only thing that touches intent.

**AI-leverage.** An agent can add a new player action by adding one `match` arm
and one logic function, never touching input plumbing. The same seam is what a
self-play harness (technique 6) drives, and what an undo stack records — so the
agent gets replay and headless testing "for free" once the seam exists.

---

## 5. Save system (atomic, versioned, optional cloud)

**What.** Serialize state to JSON; write it **atomically** (temp file → rename)
so a crash mid-write never corrupts the live save; stamp every save with a schema
**version** and run ordered **migrations** on load; treat cloud sync as
best-effort that never blocks local saves or startup.

**StS2 evidence.** StS2's `GodotFileIo` *"Implements the ISaveStore interface …
All file I/O operations related to game saves should use this class to ensure
proper path handling, **atomic writes**, and consistent error handling."* Schema
evolution rides `IMigration<T>`: *"Strongly typed interface for migrations that
operate on a specific save type,"* plus `Migrations`/`MigrationUtil`. Cloud
policy is unambiguous: `CloudSaveStore` — *"All cloud operations are best-effort.
A cloud failure must never prevent local saves from working or the game from
starting."* The `SaveManager` is built with *"dependency injection support"* and
coordinates independent specialized managers specifically because that
*"improves testability."*

**GDScript how-to.** Atomic write via temp-then-rename:

```gdscript
# save_store.gd — atomic, versioned local save store.
class_name SaveStore
extends RefCounted

const SAVE_PATH := "user://save.json"
const TMP_PATH := "user://save.json.tmp"
const CURRENT_VERSION := 3

func save(state: Dictionary) -> Error:
    state["_version"] = CURRENT_VERSION
    var json := JSON.stringify(state, "\t")

    # 1) Write to a temp file first.
    var f := FileAccess.open(TMP_PATH, FileAccess.WRITE)
    if f == null:
        return FileAccess.get_open_error()
    f.store_string(json)
    f.flush()
    f = null # Godot 4 FileAccess has no close(); drop the ref to flush + close

    # 2) Atomically swap temp over the real file. rename() is atomic on the same
    #    volume, so a reader/crasher never sees a half-written save.
    var da := DirAccess.open("user://")
    return da.rename(TMP_PATH, SAVE_PATH)

func load() -> Dictionary:
    if not FileAccess.file_exists(SAVE_PATH):
        return {}
    var text := FileAccess.get_file_as_string(SAVE_PATH)
    var data: Variant = JSON.parse_string(text)
    if typeof(data) != TYPE_DICTIONARY:
        push_error("save corrupt or unreadable")
        return {}
    return SaveMigrator.migrate(data)
```

Versioned migrations as an ordered chain of pure functions:

```gdscript
# save_migrator.gd
class_name SaveMigrator
extends RefCounted

# Each migration is a pure function taking vN data and returning vN+1 data,
# dispatched by the FROM version. (Named funcs, not inline lambdas: GDScript's
# parser is finicky about multi-line lambdas embedded in collection literals.)
static func _v1_to_v2(d: Dictionary) -> Dictionary:
    d["gold"] = d.get("money", 0) # renamed field
    d.erase("money")
    return d

static func _v2_to_v3(d: Dictionary) -> Dictionary:
    d["relics"] = d.get("relics", []) # new field with default
    return d

static func _step(from_version: int, d: Dictionary) -> Dictionary:
    match from_version:
        1: return _v1_to_v2(d)
        2: return _v2_to_v3(d)
        _: return d

static func migrate(data: Dictionary) -> Dictionary:
    var v: int = int(data.get("_version", 1))
    while v < SaveStore.CURRENT_VERSION:
        data = _step(v, data)
        v += 1
        data["_version"] = v
    return data
```

Best-effort cloud that never blocks — wrap the local store, run cloud work off
the critical path, swallow failures:

```gdscript
# cloud_save_store.gd — decorates a local store; cloud is fire-and-forget.
class_name CloudSaveStore
extends RefCounted

var _local: SaveStore

func _init(local: SaveStore) -> void:
    _local = local

func save(state: Dictionary) -> Error:
    var err := _local.save(state) # local save is authoritative and synchronous
    if err == OK:
        _upload_async.call_deferred(state) # never awaited, never blocks
    return err

func _upload_async(state: Dictionary) -> void:
    # A failure here logs and returns; it must not surface to the caller.
    if not _cloud_available():
        push_warning("cloud unavailable; local save already succeeded")
        return
    # ... best-effort upload; reads ALWAYS come from local on next load ...

func _cloud_available() -> bool:
    return false # stub
```

**AI-leverage.** The schema can evolve safely: when an agent adds a field, it
adds one migration entry and the chain handles every old save. The atomic-write
and best-effort-cloud shapes are learnable templates an agent reproduces exactly.
DI-friendly stores (pass a fake `SaveStore` in tests) keep save logic unit-
testable without touching the disk — see technique 7.

---

## 6. Self-play smoke testing

**What.** A headless "auto-play" mode that issues *valid* inputs to actually play
the game end-to-end, guarded by a **watchdog** that dumps state and fails if
progress stalls, with a **memory-delta** check to catch leaks across a run. This
is the machine-checkable "does a full run still work?" gate.

**StS2 evidence.** StS2 ships `AutoSlayer`: *"Main orchestrator for AutoSlay.
Runs the game automatically for smoke testing"* with `Start(seed, …)`. Its
`AutoSlayConfig` has a `watchdogTimeout` — *"If no progress for this long, dump
state and fail."* The `Watchdog` has `Reset(reason)` (*"Call this whenever
meaningful progress is made"*), `Check()` (*"Throws TimeoutException if no
progress for too long"*), and `DumpState()`. `MemoryProfiler` *"Captures memory
and resource snapshots during AutoSlay runs, logging deltas from a baseline to
detect memory/resource leaks."* Handlers like `CombatRoomHandler` *"Applies massive
defensive buffs and plays all cards each turn."*

**GDScript how-to.** A `SceneTree` script you launch with
`godot --headless -s res://tools/auto_play.gd`:

```gdscript
# tools/auto_play.gd — headless self-play smoke test. Inherits SceneTree so it
# can be run with: godot --headless -s res://tools/auto_play.gd -- --seed=42
extends SceneTree

var _watchdog: Watchdog
var _baseline_mem: int

func _init() -> void:
    var seed := _parse_seed()
    _baseline_mem = OS.get_static_memory_usage()
    _watchdog = Watchdog.new(5.0) # fail if no progress for 5s

    var game := AutoGame.new(seed) # headless game model + executor
    var safety := 10_000 # hard cap on turns to bound the run

    while not game.is_over() and safety > 0:
        _watchdog.check() # aborts (and dumps) if stalled
        var action := _pick_valid_action(game)
        if action != null:
            game.executor.enqueue(action)
            game.executor.execute_all()
            _watchdog.reset("executed %s" % action.kind)
        safety -= 1

    _check_memory()
    quit(0 if game.is_won() else 1) # exit code is the CI signal

func _pick_valid_action(game: AutoGame) -> GameAction:
    # Mirror CombatRoomHandler: play everything affordable, else end the turn.
    for card in game.playable_cards():
        return GameAction.new(&"play_card", {"card": card, "target": 0})
    return GameAction.new(&"end_turn")

func _check_memory() -> void:
    var delta := OS.get_static_memory_usage() - _baseline_mem
    print("[AUTOPLAY] mem delta: %d bytes" % delta)
    if delta > 64 * 1024 * 1024: # >64 MB growth over a full run smells like a leak
        push_error("[AUTOPLAY] possible leak: %d bytes" % delta)

func _parse_seed() -> int:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--seed="):
            return int(arg.trim_prefix("--seed="))
    return 0
```

```gdscript
# watchdog.gd — fails the run if no meaningful progress is reported in time.
class_name Watchdog
extends RefCounted

var _timeout: float
var _last_progress_ms: int

func _init(timeout_seconds: float) -> void:
    _timeout = timeout_seconds
    _last_progress_ms = Time.get_ticks_msec()

func reset(reason: String) -> void:
    _last_progress_ms = Time.get_ticks_msec()

func check() -> void:
    var elapsed := (Time.get_ticks_msec() - _last_progress_ms) / 1000.0
    if elapsed > _timeout:
        dump_state()
        push_error("[WATCHDOG] stalled %.1fs with no progress" % elapsed)
        OS.crash("watchdog timeout") # hard-fail so CI sees a nonzero exit

func dump_state() -> void:
    print("[WATCHDOG] dumping state at stall ...")
    # serialize current game/scene state to user://autoplay_dump.json
```

**AI-leverage.** This is the gate an agent runs after every change: one command,
one exit code, one memory line. It catches the bugs unit tests miss —
soft-locks, unreachable states, slow leaks — that only emerge over a full run.
Because it drives the *intent* seam from technique 4, no UI or input simulation
is needed.

---

## 7. Test seams

**What.** Build deliberate seams so production systems are testable without
production coupling: inject the RNG/seed, dependency-inject stores (pass a fake),
and drive UI in headless tests by **emitting the control's signal directly**
instead of faking a mouse.

**StS2 evidence.** StS2's `TestSupport` namespace exists for exactly this.
`TestRngInjector` exposes `SetCombatCardGenerationOverride()` (*"Force specific
cards to show up"*) and `SetInitialShuffleOverride()` (*"Force a specific order
for the initial shuffle"*). `SaveManager` ships a *"Constructor with dependency
injection support"* plus a flag to *"Force all operations to be performed
synchronously. Only use in tests."* And `UiHelper.Click()` *"Clicks a clickable
control by directly emitting the Released signal. This bypasses hover/focus/pause
checks that can fail in headless/automated testing."*

**GDScript how-to.** Inject RNG and a fake store; click by signal.

```gdscript
# Production code accepts its dependencies instead of constructing them.
class_name CardFactory
extends RefCounted

var _rng: RandomNumberGenerator

func _init(rng: RandomNumberGenerator) -> void:
    _rng = rng # injected -> a test can hand in a fixed-seed generator

func draw_reward(pool: Array[StringName]) -> StringName:
    return pool[_rng.randi_range(0, pool.size() - 1)]
```

```gdscript
# test_card_factory.gd — deterministic via injected seed.
extends GutTest

func test_reward_is_deterministic_for_a_seed() -> void:
    var rng := RandomNumberGenerator.new()
    rng.seed = 999
    var factory := CardFactory.new(rng)
    var first := factory.draw_reward([&"a", &"b", &"c", &"d"])

    rng.seed = 999 # reset -> same seed must yield the same draw
    var again := CardFactory.new(rng).draw_reward([&"a", &"b", &"c", &"d"])
    assert_eq(first, again)

func test_save_uses_injected_fake_store() -> void:
    var fake := FakeSaveStore.new() # in-memory ISaveStore stand-in
    var sm := SaveManager.new(fake) # DI: no disk touched
    sm.save_progress({"gold": 50})
    assert_eq(fake.last_written["gold"], 50)

func test_button_click_via_signal_emit() -> void:
    # Headless: don't simulate a mouse. Emit the control's own signal.
    var button := Button.new()
    add_child_autofree(button)
    var clicked := [false]
    button.pressed.connect(func() -> void: clicked[0] = true)
    button.pressed.emit() # the UiHelper.Click() trick: bypass hover/focus/pause
    assert_true(clicked[0])
```

**AI-leverage.** Seams are what let an agent write *deterministic* tests against
*real* systems. Inject a seed and the test never flakes; inject a fake store and
the test never touches disk; emit the signal and the test runs headless in CI.
An agent that knows these three seams can produce a regression test for almost
any change without spinning up the full game.

---

## 8. Observability

**What.** An in-game dev console (a `LineEdit` plus a command dictionary),
compiled *out* of release builds; structured logging with consistent prefixes you
can grep; and build/version identity **baked into the binary** so any bug report
is reproducible against an exact commit.

**StS2 evidence.** StS2's `DevConsole` ships commands like `GodModeConsoleCmd`,
`GoldConsoleCmd`, `HealConsoleCmd`, `TravelConsoleCmd`, `WinConsoleCmd`, and
`GetLogsConsoleCmd` (*collects + zips logs/saves/core dumps*). Its
`ProcessCommand()` is even multiplayer-aware (networked commands enqueue a
`GameAction` to all peers). `AutoSlayLog` provides *"Structured logging … with
consistent prefixes for easy filtering."* And `ReleaseInfo`/`ReleaseInfoManager`/
`AssemblyHasher` bake *Commit/Version/Date/Branch/MainAssemblyHash* in *"for
reproducible bug reports,"* feeding `SentryService` telemetry.

**GDScript how-to.** Dev console guarded out of release with `OS.is_debug_build()`
(or a feature tag):

```gdscript
# dev_console.gd — LineEdit + command dict. Compiled-out of release.
extends CanvasLayer

@onready var _input: LineEdit = $LineEdit

# Map command name -> Callable. First-class references to the methods below;
# each handler returns a result string to echo back into the log.
var _commands: Dictionary = {
    "gold": _cmd_gold,
    "heal": _cmd_heal,
    "win": _cmd_win,
}

func _cmd_gold(args: PackedStringArray) -> String:
    Game.player.gold += int(args[0])
    return "gold += %s" % args[0]

func _cmd_heal(_args: PackedStringArray) -> String:
    Game.player.hp = Game.player.max_hp
    return "healed to full"

func _cmd_win(_args: PackedStringArray) -> String:
    Game.combat.win()
    return "combat won"

func _ready() -> void:
    if not OS.is_debug_build():
        queue_free() # never exists in a release build
        return
    _input.text_submitted.connect(_on_submit)

func _on_submit(line: String) -> void:
    var parts := line.split(" ", false)
    if parts.is_empty():
        return
    var cmd := parts[0]
    var args := parts.slice(1) as PackedStringArray
    if _commands.has(cmd):
        Log.info("console", _commands[cmd].call(args))
    else:
        Log.warn("console", "unknown command: %s" % cmd)
    _input.clear()
```

```gdscript
# log.gd — structured logging with grep-friendly prefixes (autoload "Log").
extends Node

func info(tag: String, msg: String) -> void: _emit("INFO", tag, msg)
func warn(tag: String, msg: String) -> void: _emit("WARN", tag, msg)
func error(tag: String, msg: String) -> void: _emit("ERROR", tag, msg)

func _emit(level: String, tag: String, msg: String) -> void:
    # Stable shape: [LEVEL][tag] msg @t=ticks -> grep '\[ERROR\]\[combat\]'
    print("[%s][%s] %s @t=%d" % [level, tag, msg, Time.get_ticks_msec()])
```

```gdscript
# release_info.gd — build identity baked at export time.
class_name ReleaseInfo
extends RefCounted

# Populate these from CI at export (e.g. a generated .gd or ProjectSettings).
const VERSION := "0.1.0"
const COMMIT := "59260271"
const BUILD_DATE := "2026-06-18"

static func banner() -> String:
    return "v%s (%s, %s)" % [VERSION, COMMIT, BUILD_DATE]
```

**AI-leverage.** Structured prefixes turn logs into something an agent can `grep`
and reason over (`[ERROR][combat]`). The console lets an agent (or you) jump a
live game into the exact state a bug needs. Baked `ReleaseInfo` means a pasted
report ties to a precise commit — the agent reproduces against the *same* code.

---

## 9. AI asset-generation pipeline

**What.** Batch-generate sprites and tilesets with a local Stable-Diffusion stack
(ComfyUI) driven over its HTTP API, dropping results straight into `res://` —
with hard guardrails on *consistency* and a clear line between draft assets and
hero assets.

**Research grounding.** ComfyUI exposes an HTTP API: `POST /prompt` with a JSON
workflow, poll `/history/{prompt_id}`, free VRAM via `/free`
([comfy.org](https://comfy.org/)). Character consistency is an *identity-vs-
variation* split: train a character **LoRA** on ~15–20 multi-angle references so
identity is fixed by the LoRA and variation comes from the prompt; control pose
with **OpenPose ControlNet**. Pixel-specific tools (PixelLab, Sprite AI) emit
game-exact sizes and sheets. The reality check from the digest is firm: AI is for
*drafts, bulk variation, and backgrounds*; humans own hero assets. AI is weak on
symmetry, style continuity, and performance, and carries training-data IP risk —
keep humans deciding. See [References](references.md) for all source links.

**How-to (orchestration, GDScript-adjacent).** Asset generation runs *outside*
the game (it is Python/HTTP), but you can fire and collect a batch from a Godot
editor tool using `HTTPRequest`, then let `--import` ingest the PNGs:

```gdscript
# tools/sprite_batch.gd — @tool script: submit a ComfyUI workflow per variant.
@tool
extends EditorScript

const COMFY := "http://127.0.0.1:8188"
const PROMPTS: Array[String] = [
    "goblin warrior, side view, idle",
    "goblin warrior, side view, attack",
]

func _run() -> void:
    # Submit each prompt; ComfyUI returns a prompt_id you poll on /history.
    # Identity is locked by a character LoRA in the workflow graph; only the
    # positive prompt varies per pose. Outputs land in res://art/raw/ and are
    # picked up by `godot --headless --import` before they are usable.
    for p in PROMPTS:
        var body := _build_workflow(p) # JSON graph w/ LoRA + ControlNet nodes
        print("[ASSETGEN] would POST %s/prompt for: %s" % [COMFY, p])
        # var http := HTTPRequest.new(); add_child(http)
        # http.request("%s/prompt" % COMFY, [], HTTPClient.METHOD_POST, body)

func _build_workflow(prompt: String) -> String:
    return JSON.stringify({"prompt": {"positive": prompt, "lora": "goblin_v1"}})
```

A practical batch loop lives in Python next to the repo (HF Diffusers or the
ComfyUI API directly), writing `res://art/raw/*.png`; then:

```bash
# Ingest generated PNGs into Godot's import cache before use.
godot --headless --import
```

**Consistency & production caveats (do not skip).** Lock identity with a LoRA, not
prompt-wording; pose with ControlNet, not luck. Pin checkpoint + LoRA + seed in a
manifest so a sprite is regenerable. Treat raw output as *drafts*: a human passes
every asset for symmetry, palette, and silhouette before it ships. Keep an IP
provenance note per model. AI fills the long tail (variants, backgrounds, mood
boards); humans author the heroes.

**AI-leverage.** The agent's job here is *orchestration and bookkeeping*: drive
the API, manage the batch, keep the seed/checkpoint manifest, wire `--import`, and
file results by naming convention — not to be the artist. That keeps the
human-judgment gate exactly where the research says it belongs.

---

## 10. Headless CI test runs

**What.** Run the full test suite (and ideally the self-play smoke test) on every
push with no GPU, no audio, and a deterministic import cache — exit code is the
gate.

**Research grounding.** `--headless` disables GPU + audio drivers and is the CI
baseline ([Godot CLI docs](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html)).
Pre-heat the import cache with `godot --headless --import` before any headless run,
and cache `.godot/` keyed on a hash of `project.godot` + `*.gd` + `*.tscn`. Commit
`export_presets.cfg` (do **not** gitignore it). GUT runs headlessly via its
command-line runner and its exit code reflects pass/fail (JUnit XML via
`-goutput`); gdUnit4 returns 0/100/101 and auto-generates HTML + JUnit. Docker
images (`barichello/godot-ci`, with `mono-*` tags for C#) and actions
(`firebelley/godot-export`, `gdUnit4-action`) wrap all of this. Full source list
in [References](references.md).

**How-to.** Local one-liners (Git Bash / CI shell):

```bash
# 1) Pre-heat the import cache so the first headless run isn't a cold miss.
godot --headless --import

# 2) Run the GUT suite headless; -gexit makes the runner set the process exit code.
godot --headless -s res://addons/gut/gut_cmdln.gd \
  -gdir=res://tests -ginclude_subdirs -gexit -goutput=res://test-results

# 3) Run the self-play smoke test (technique 6) as a second gate.
godot --headless -s res://tools/auto_play.gd -- --seed=42
```

A minimal GitHub Actions job using the Docker image:

```yaml
# .github/workflows/test.yml
name: test
on: [push, pull_request]
jobs:
  gut:
    runs-on: ubuntu-latest
    container: barichello/godot-ci:4.5-stable   # use a mono-* tag for C#
    steps:
      - uses: actions/checkout@v4
      - name: Cache import
        uses: actions/cache@v4
        with:
          path: .godot
          key: godot-${{ hashFiles('project.godot', '**/*.gd', '**/*.tscn') }}
      - name: Import
        run: godot --headless --import
      - name: GUT
        run: |
          godot --headless -s res://addons/gut/gut_cmdln.gd \
            -gdir=res://tests -ginclude_subdirs -gexit
```

**AI-leverage.** A green CI is the agent's definition of done. The exit-code
contract lets an agent run the exact same gate locally that the pipeline runs, so
"it passes for me" and "it passes in CI" converge. Caching `.godot/` keeps
iteration fast enough that an agent can run the suite on every change. Note for a
C#-heavy codebase (like StS2 itself): prefer gdUnit4 / gdUnit4Net and the `mono-*`
CI images; for a GDScript-only project, GUT is the lighter path.

---

## How these compose

The techniques reinforce each other into one machine-verifiable loop:

- **Seeded RNG (1)** + **test seams (7)** make every test deterministic.
- **Data-driven content (2)** + **modifier resolution (3)** make new content a
  low-blast-radius diff an agent can add safely.
- **Intent/logic split (4)** gives self-play (6) and CI (10) something headless to
  drive, and gives the save system (5) something to replay.
- **Observability (8)** turns any failure — in a test, a self-play run, or a
  player's machine — into a reproducible, grepable, commit-pinned report.
- **Asset generation (9)** stays orchestration the agent runs and a human judges.

Adopt them in roughly that order. Each one lowers the cost and risk of the next,
and together they form the substrate that lets an AI agent extend the game while
a machine — not just a human reviewer — confirms it still works. See the sibling
docs and [References](references.md) for the surrounding methodology.
