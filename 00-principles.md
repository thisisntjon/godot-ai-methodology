# 00 — Principles of AI-Leverageable Game Architecture

> Purpose: the foundational, language-agnostic principles that make a Godot game both *shippable at scale* and *safely buildable, testable, and extendable by an AI assistant* — with each principle grounded in Slay the Spire 2's shipped architecture and translated into idiomatic Godot 4.x GDScript.

## Thesis

The traits that let a small team ship and maintain a large game are the same traits that let an AI assistant work on it without breaking things. Determinism, data-driven content, clean seams, composition over special-casing, observability, and disciplined documentation are not "nice to have" for AI — they are the *substrate* that turns an LLM from a plausible-code generator into a contributor whose changes you can verify.

Slay the Spire 2 (StS2) is a useful witness here. It ships on **Godot 4.5.1** in **C# / .NET 9**, and — unusually — it shipped its full XML documentation (`sts2.xml`, ~99k lines, about 2,700 documented types). We study it **read-only**, from those plainly-shipped doc comments and loose JSON manifests; no decompilation, no `.pck` extraction. Every StS2 quote below is the developers' own `<summary>` text, cited from the evidence pack. We do not copy their code (there is none to copy) — we translate the *patterns* into original GDScript for the GDScript stack.

Read this doc as the conceptual backbone. Later docs operationalize it: see the [Technique Catalog](03-techniques.md), [Working With AI Coding Assistants](04-ai-collaboration-patterns.md), and [References](references.md) for tool names, commands, and sources.

---

## 1. Determinism: seed everything, segregate streams, quarantine chaos

**The principle.** All gameplay randomness flows through explicit, *seeded* generators, partitioned into independent streams by concern. Anything that must *not* be reproducible (cosmetic jitter, idle animation timing) is isolated into a clearly-labelled non-deterministic generator and is forbidden from touching game state. A run is a pure function of `(seed, inputs)`.

**StS2 evidence.** StS2 runs a custom seeded PRNG and segregates it aggressively:

- `MegaRandom`: *"Xoshiro256** (xor, shift, rotate) pseudo-random number generator (PRNG)."*
- `Rng`: *"A custom random class which allows predictable results when utilizing seeds"* — with an ergonomic constructor *"for creating an RNG for a specific piece of content during a run. This RNG will be unique among: The run, The player SLOT, The ID of the content passed,"* and it deliberately uses the *"player slot index, rather than the NetId, to ensure consistent results when playing a daily run."*
- `Rng.Chaotic`: *"A non-deterministic RNG instance. This will not produce the same results after saving and loading. Good for when we need to randomize things that don't impact gameplay."*
- `PlayerRngSet`: explicitly separate streams — `Rewards` (*"What cards are generated for rewards"*), `Shops` (*"What the different shops are selling"*), `Transformations` (*"What a transformed card will roll into"*).

**Why it helps an AI assistant.** Determinism is the single highest-leverage trait for AI-assisted work. When a run reproduces from a seed, an AI can **reproduce any bug you report** ("seed 12345, floor 3 reward is wrong") instead of guessing. Tests become *stable* — no flaky assertions, no "ran twice, got different results," which is exactly the failure mode that makes an agent silently weaken or delete a test. Segregated streams mean an AI editing the *shop* logic cannot accidentally shift the *reward* sequence, so a behavioral diff stays local and reviewable. And quarantining cosmetic randomness gives the agent a bright-line rule: "if it affects gameplay, it comes from a seeded stream; `randf()` is for sparkles only."

**GDScript application.** One RNG per concern, seeded deterministically from the run seed; a single labelled chaotic stream for cosmetics.

```gdscript
class_name RngSet
extends RefCounted

## Deterministic, segregated RNG streams for a run.
## Each stream is reproducible from (run_seed, stream name, player_slot).

const STREAMS := ["rewards", "shops", "transformations", "combat", "map"]

var _streams: Dictionary = {}              # String -> RandomNumberGenerator
var chaotic := RandomNumberGenerator.new() # cosmetic ONLY; never gates game state

func _init(run_seed: int, player_slot: int = 0) -> void:
    for name in STREAMS:
        var rng := RandomNumberGenerator.new()
        # Derive a stable per-stream seed; hashing keeps streams independent.
        rng.seed = hash("%d:%d:%s" % [run_seed, player_slot, name])
        _streams[name] = rng
    chaotic.randomize() # explicitly NON-deterministic, by design

func stream(name: String) -> RandomNumberGenerator:
    assert(_streams.has(name), "unknown RNG stream: %s" % name)
    return _streams[name]

## Save/restore is exact: capture seed+state per stream so a loaded
## game continues the identical sequence (chaotic is intentionally NOT saved).
func snapshot() -> Dictionary:
    var out := {}
    for name in _streams:
        var r: RandomNumberGenerator = _streams[name]
        out[name] = {"seed": r.seed, "state": r.state}
    return out

func restore(data: Dictionary) -> void:
    for name in data:
        var r: RandomNumberGenerator = _streams[name]
        r.seed = data[name]["seed"]
        r.state = data[name]["state"]
```

Rule of thumb for the agent's context file: *"Gameplay randomness MUST come from `RngSet.stream(...)`. `RandomNumberGenerator.randomize()`, `randi()`, and `randf()` are banned outside the `chaotic` stream."*

---

## 2. Data-driven content: definitions separate from runtime instances

**The principle.** A *definition* (the immutable template — a card's base damage, a relic's rarity) lives in data, separate from the *instance* (the mutable runtime object — this card, in this hand, with +2 upgrade, owned by this player). Adding content means adding data; changing behavior at runtime means mutating an instance. The two never blur.

**StS2 evidence.** StS2 splits this into two namespaces:

- `Core.Models` — definitions: `CardModel`, `EncounterModel`, `Cards`, `Relics`, `Powers`, `Potions`, `Monsters`, `CardPools`, `Acts`, `Characters`, `Modifiers`, `Orbs`. A `SingletonModel` is *"A model which is instantiated once for an entire run."*
- `Core.Entities` — runtime instances: `Creatures`, `Players`, `Cards`, `Merchant`, `RestSite`, `Gold`, `Potions`, `Ascension`.

The same noun (`Cards`) exists in *both* namespaces — once as a definition, once as a live instance — which is the pattern stated plainly.

**Why it helps an AI assistant.** This is the lowest-blast-radius way to grow a game. Asking an AI to "add a new card" should mean *adding a row of data*, not threading a new branch through combat control flow. A data addition is a tiny, reviewable diff that cannot break existing cards. It also gives the agent a crisp mental model: "Models are read-only truth; Entities are the mutable copy." That separation prevents the classic LLM error of mutating a shared template and corrupting every instance of a type.

**GDScript application.** Definitions as plain `.gd` data tables (more diff- and AI-friendly than `.tres` for bulk content; see [Working With AI Coding Assistants](04-ai-collaboration-patterns.md) §6 on why text logic beats binary-ish resources for agents). Instances as lightweight objects that *reference* a definition and hold only the mutable delta.

```gdscript
# card_db.gd — definitions. Pure data; no behavior, no node references.
class_name CardDb

# Godot const containers are parse-time frozen and can't hold methods, but a
# plain dictionary of dictionaries is fine and stays fully diffable.
const CARDS := {
    "strike":  {"name": "Strike",  "cost": 1, "damage": 6,  "type": "attack"},
    "defend":  {"name": "Defend",  "cost": 1, "block": 5,   "type": "skill"},
    "bash":    {"name": "Bash",    "cost": 2, "damage": 8,  "type": "attack",
                "applies": {"vulnerable": 2}},
}

static func definition(id: StringName) -> Dictionary:
    assert(CARDS.has(id), "unknown card id: %s" % id)
    return CARDS[id]
```

```gdscript
# card_instance.gd — runtime instance. References a definition, holds the delta.
class_name CardInstance
extends RefCounted

var id: StringName
var upgrades: int = 0

func _init(card_id: StringName) -> void:
    id = card_id

# Derived from the definition + this instance's mutable state.
func damage() -> int:
    var base: int = CardDb.definition(id).get("damage", 0)
    return base + (3 * upgrades) # upgrade adds +3, never edits the template
```

When the agent adds "Cleave," it appends one entry to `CARDS`. No control flow changes; no existing card is touched.

---

## 3. Separate intent from logic

**The principle.** *What the player asked for* (intent) is a distinct, queueable object from *what the game does in response* (logic). Intent is the network/undo/replay boundary; logic is the small, composable units that mutate state. Input plumbing and game rules evolve independently.

**StS2 evidence.** This is the StS2 distinction stated outright:

> *"A GameAction is a thin wrapper around an async task [...] these small units of logic are handled by **Commands** [...] A GameAction WRAPS these commands, and should ONLY be used for player input."*

Examples it lists to wrap as `GameAction`: playing a card, drinking a potion, ending turn. Explicitly *not* a GameAction: dealing damage (that is a Command). The `ActionExecutor` is *"Responsible for pulling actions from the [action queue] and executing them,"* and the GameAction roster includes multiplayer-aware verbs like `UndoEndPlayerTurnAction`, `VoteForMapCoordAction`, and `ReadyToBeginEnemyTurnAction`.

**Why it helps an AI assistant.** The intent/logic seam is where undo, replay, and multiplayer live — the highest-stakes, easiest-to-corrupt parts of a game. By giving the AI a rule ("player input becomes an `Action`; rules live in `Command`s; never call a Command directly from a button handler"), you keep it from wiring UI directly into combat math. The agent can rebalance damage (logic) without ever touching input routing, and can add an input verb without understanding the full rules engine. Each layer is independently testable: feed Actions to assert queue/undo behavior; run Commands to assert state changes.

**GDScript application.** Actions are records pushed onto a queue; Commands mutate state and are reversible.

```gdscript
# action.gd — INTENT. Serializable, queueable, the undo/replay/network unit.
class_name Action
extends RefCounted

var verb: StringName          # &"play_card", &"end_turn", &"use_potion"
var payload: Dictionary       # e.g. {"card": <CardInstance>, "target": <id>}

func _init(p_verb: StringName, p_payload: Dictionary = {}) -> void:
    verb = p_verb
    payload = p_payload
```

```gdscript
# command.gd — LOGIC. Small, composable, reversible. Knows nothing about input.
class_name Command
extends RefCounted

func execute(state: CombatState) -> void:
    push_error("Command.execute must be overridden")

func undo(state: CombatState) -> void:
    push_error("Command.undo must be overridden")


class DealDamage extends Command:
    var target_id: int
    var amount: int
    var _absorbed: int = 0 # captured for exact undo

    func _init(p_target: int, p_amount: int) -> void:
        target_id = p_target
        amount = p_amount

    func execute(state: CombatState) -> void:
        _absorbed = state.apply_damage(target_id, amount)

    func undo(state: CombatState) -> void:
        state.restore_hp(target_id, _absorbed)
```

```gdscript
# action_executor.gd — the seam. Translates intent into logic; owns undo history.
class_name ActionExecutor
extends RefCounted

var _state: CombatState
var _history: Array[Command] = []

func run(action: Action) -> void:
    var commands := _compile(action) # one Action -> many Commands
    for c in commands:
        c.execute(_state)
        _history.append(c)

func undo_last_action(count: int) -> void:
    for i in count:
        var c := _history.pop_back() as Command
        if c: c.undo(_state)
```

A `Button.pressed` handler emits an `Action`; it never news up a `DealDamage`. That single discipline is what makes undo and (later) multiplayer tractable.

---

## 4. Compose, don't special-case

**The principle.** When many effects modify the same value (damage, cost, block), they each *contribute* to a resolution pipeline rather than being handled by pairwise special cases. New effects register a contribution and compose automatically; you never write `if has_strength and has_vulnerable and not intangible` ladders.

**StS2 evidence.** StS2 resolves damage through a typed hook pipeline:

- `Hook`: *"A static class containing all of the gameplay hooks"* (e.g. `BeforeAttack`, `AfterModifyingDamageAmount`), with signatures that pass shared state.
- `ModifyDamageHookType` enum: `Additive` — *"Additive damage hooks from effects like StrengthPower"*; `Multiplicative` — *"Multiplicative damage hooks from effects like VulnerablePower"*; `Cap` — *"Damage-capping hooks from effects like IntangiblePower"*; `All` — *"Include all ModifyDamage hooks. Most back-end ModifyDamage hook calls will use this."*

Strength, Vulnerable, and Intangible don't know about each other. Each declares *how* it contributes (add / multiply / cap), and the resolver folds them in a fixed order.

**Why it helps an AI assistant.** Combinatorial special-casing is where LLMs (and humans) silently introduce bugs — they cannot hold the full N×N interaction matrix in mind, so they bolt on one more `if` and break a distant case. A composition pipeline collapses that to a single, ordered fold: an AI adds a new effect by writing one contribution function and registering it. There is *no* place to get the cross-product wrong, because there is no cross-product — only "additive, multiplicative, or cap?"

**GDScript application.** A resolver that collects typed contributions and folds them deterministically (sum additives → apply multipliers → clamp to caps).

```gdscript
class_name DamageResolver
extends RefCounted

enum Kind { ADDITIVE, MULTIPLICATIVE, CAP }

# A modifier is just data + a Callable that yields its contribution.
# fn(ctx: Dictionary) -> float   ctx carries source, target, base, etc.
class Modifier:
    var kind: DamageResolver.Kind
    var fn: Callable
    func _init(p_kind: DamageResolver.Kind, p_fn: Callable) -> void:
        kind = p_kind
        fn = p_fn

var _mods: Array[Modifier] = []

func add(kind: Kind, fn: Callable) -> void:
    _mods.append(Modifier.new(kind, fn))

func resolve(base: float, ctx: Dictionary) -> int:
    var value := base
    # 1) additives (Strength, etc.)
    for m in _mods:
        if m.kind == Kind.ADDITIVE:
            value += m.fn.call(ctx)
    # 2) multiplicatives (Vulnerable, etc.)
    for m in _mods:
        if m.kind == Kind.MULTIPLICATIVE:
            value *= m.fn.call(ctx)
    # 3) caps (Intangible, etc.) — each cap clamps the running value
    for m in _mods:
        if m.kind == Kind.CAP:
            value = minf(value, m.fn.call(ctx))
    return int(maxf(0.0, value))
```

```gdscript
# Registering effects — each is independent and order-stable.
resolver.add(DamageResolver.Kind.ADDITIVE,       func(_c): return strength)
resolver.add(DamageResolver.Kind.MULTIPLICATIVE, func(_c): return 1.5 if vulnerable else 1.0)
resolver.add(DamageResolver.Kind.CAP,            func(_c): return 1.0 if intangible else INF)
var final_damage := resolver.resolve(6.0, {"source": attacker, "target": defender})
```

Adding "Weak" (a 0.75× multiplier) is one `resolver.add(...)` line. Nothing else changes, and the fold order guarantees the same result every time.

---

## 5. Testability via seams: DI, injectable RNG, headless input

**The principle.** Production systems expose *seams* — dependency injection points, override hooks, and input shims — so tests exercise the *real* code paths deterministically, without spinning up the whole game or the renderer. The seams ship in the product (guarded), not as a parallel test-only fork.

**StS2 evidence.** StS2 ships a `TestSupport` surface and DI throughout:

- `TestRngInjector`: `SetCombatCardGenerationOverride()` — *"Force specific cards to show up for CardFactory.GetDistinctForCombat"* — and `SetInitialShuffleOverride()` — *"Force a specific order for the initial shuffle."*
- `ICardSelector`: *"Interface for automated card selection, used by both test mode and AutoSlay."*
- `UiHelper.Click()`: *"Clicks a clickable control by directly emitting the Released signal. This bypasses hover/focus/pause checks that can fail in headless/automated testing."*
- `SaveManager` ships a *"Constructor with dependency injection support"* and a flag to *"Force all operations to be performed synchronously. Only use in tests,"* and notes the specialized-manager split *"improves testability by allowing each save manager to be tested independently [...]"*

**Why it helps an AI assistant.** Seams are what let an agent practice real TDD instead of testing a hollow mock. With injectable RNG, the agent writes "force the shuffle, assert the outcome" — a deterministic test against production logic. With a headless click helper, it can drive UI under `--headless` in CI without a GPU. And DI lets it test a save subsystem against a fake store. Crucially, this defuses the agent's worst test-writing habits (mocking everything, or writing tests that already pass) because the seam makes the *real* path cheaply controllable. (See the [Technique Catalog](03-techniques.md) for the GUT workflow and the [phased workflow](01-phased-workflow.md) for red-phase enforcement.)

**GDScript application.** Inject the `RngSet`; expose override hooks; click via signal emission.

```gdscript
# Production class takes its RNG by injection — no global singleton reach-in.
class_name CardFactory
extends RefCounted

var _rng: RandomNumberGenerator
var _override: PackedStringArray = [] # test seam; empty in production

func _init(rng: RandomNumberGenerator) -> void:
    _rng = rng

# Test-only seam, mirroring SetCombatCardGenerationOverride.
func set_generation_override(ids: PackedStringArray) -> void:
    _override = ids

func draw(pool: PackedStringArray) -> StringName:
    if not _override.is_empty():
        return _override[0]
    return pool[_rng.randi_range(0, pool.size() - 1)]
```

```gdscript
# tests/test_card_factory.gd — runs headless via GUT.
extends GutTest

func test_draw_is_seed_stable() -> void:
    var rng := RandomNumberGenerator.new()
    rng.seed = 42
    var factory := CardFactory.new(rng)
    var first := factory.draw(["strike", "defend", "bash"])
    rng.seed = 42 # reset
    var factory2 := CardFactory.new(rng)
    assert_eq(factory2.draw(["strike", "defend", "bash"]), first,
        "same seed must yield same draw")

func test_override_forces_card() -> void:
    var factory := CardFactory.new(RandomNumberGenerator.new())
    factory.set_generation_override(["bash"])
    assert_eq(factory.draw(["strike", "defend"]), &"bash")
```

```gdscript
# A headless-safe click that bypasses hover/focus/pause, like UiHelper.Click().
static func headless_click(button: BaseButton) -> void:
    button.pressed.emit()
```

Run headless: `godot --headless -s res://addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit` (exit code reflects pass/fail; JUnit XML via `-goutput`).

---

## 6. Observability: dev console, structured logs, build identity, telemetry

**The principle.** You can inspect and manipulate live game state, logs are structured for filtering, and every build is *identifiable* (version, commit, hash) so any report is reproducible. Crash/error telemetry is opt-in and best-effort.

**StS2 evidence.** StS2 is heavily instrumented:

- `DevConsole` commands: `DieConsoleCmd`, `GodModeConsoleCmd`, `GoldConsoleCmd`, `HealConsoleCmd`, `TravelConsoleCmd`, `WinConsoleCmd`, plus `GetLogsConsoleCmd` (*collects + zips logs/saves/core dumps*). `DevConsole.ProcessCommand()` notes that if a command *"must be networked and a run is in progress, a GameAction will be enqueued to all peers before the command is executed"* — i.e. even cheats respect the intent layer (Principle 3).
- `AutoSlayLog`: *"Structured logging ... with consistent prefixes for easy filtering. Writes to both the standard Godot log and a dedicated autoslay.log file."*
- `ReleaseInfo` / `AssemblyHasher`: *"Commit/Version/Date/Branch/MainAssemblyHash baked in for reproducible bug reports."* The shipped `release_info.json` carries `v0.107.1`, commit `59260271`, date `2026-06-18`.
- `SentryService` for crash/error telemetry.

**Why it helps an AI assistant.** Observability is how an agent *sees what actually happened* instead of theorizing. A dev console lets it set up an exact game state to reproduce a bug ("god mode, travel to boss, seed X"). Consistently-prefixed structured logs are greppable — the agent can search for `[combat]` and read only what matters. And build identity closes the loop on bug reports: "this happened on commit `59260271`" lets the agent check out the exact code. Telemetry being best-effort (a failure never blocks the game) is itself a rule the agent should respect.

**GDScript application.** A command-dispatch console (guarded out of release), prefixed logging, and baked-in build identity.

```gdscript
# dev_console.gd — autoload; only active in debug/dev builds.
extends Node

var _commands: Dictionary = {} # StringName -> Callable

func _ready() -> void:
    if not OS.is_debug_build():
        set_process(false)
        return
    register(&"heal", func(args): GameState.player.heal(int(args[0])))
    register(&"gold", func(args): GameState.player.add_gold(int(args[0])))
    register(&"travel", func(args): MapService.travel_to(args[0]))

func register(name: StringName, fn: Callable) -> void:
    _commands[name] = fn

func process_command(line: String) -> void:
    var parts := line.split(" ", false)
    if parts.is_empty(): return
    var name := StringName(parts[0])
    if not _commands.has(name):
        Log.warn("console", "unknown command: %s" % name)
        return
    _commands[name].call(parts.slice(1))
```

```gdscript
# log.gd — structured, prefixed logging. Greppable: "[combat] ...".
class_name Log

static func info(tag: String, msg: String) -> void:
    print("[%s] %s" % [tag, msg])

static func warn(tag: String, msg: String) -> void:
    push_warning("[%s] %s" % [tag, msg])

static func error(tag: String, msg: String) -> void:
    push_error("[%s] %s" % [tag, msg])
```

```gdscript
# release_info.gd — generated at build time; printed into every log + bug report.
class_name ReleaseInfo

const VERSION := "v0.1.0"
const COMMIT  := "unknown"   # injected by CI: sed/template before export
const DATE    := "unknown"

static func banner() -> String:
    return "build %s (%s) %s" % [VERSION, COMMIT, DATE]
```

Optional crash telemetry: ship the `sentry-godot` GDExtension or a minimal opt-in uploader — keep it best-effort so a telemetry failure never blocks startup or saves.

---

## 7. Automated verification: self-play smoke tests

**The principle.** Beyond unit tests, the game can *play itself* end-to-end — a headless agent that drives valid inputs through a full run, guarded by a watchdog that fails fast on stalls and a profiler that catches leaks. This is the machine-checkable "is the game still completable?" gate.

**StS2 evidence.** StS2's `AutoSlay` is exactly this:

- `AutoSlayer`: *"Main orchestrator for AutoSlay. Runs the game automatically for smoke testing."* It exposes `Start(seed, …)`/`Stop()` and a type-safe `GetCurrentScreen<T>()`.
- `AutoSlayConfig`: parameterized timeouts — `runTimeout` (*"Maximum time for a complete run"*), `defaultRoomTimeout`, `watchdogTimeout` (*"If no progress for this long, dump state and fail"*).
- A handler hierarchy (`IRoomHandler`, `IScreenHandler`) with 20+ concrete handlers; `CombatRoomHandler` *"Applies massive defensive buffs and plays all cards each turn."*
- `Watchdog`: `Reset(reason)` (*"Call this whenever meaningful progress is made"*), `Check()` (*"Throws TimeoutException if no progress for too long"*), `DumpState()`.
- `MemoryProfiler`: *"Captures memory and resource snapshots ... logging deltas from a baseline to detect memory/resource leaks."*

**Why it helps an AI assistant.** Unit tests prove a function; self-play proves the *game still works after the agent's change*. This is the single most valuable signal you can give an AI contributor: a deterministic, seeded, headless run that either reaches the end (pass) or stalls/crashes/leaks (fail with a state dump). The agent runs it as a pre-merge gate and *reads the dump* to self-correct. The watchdog converts "hangs forever" (useless to an automated loop) into "fails in 30s with context."

**GDScript application.** A `SceneTree` script that drives seeded inputs with a watchdog and memory baseline.

```gdscript
# auto_play.gd — run: godot --headless -s res://tools/auto_play.gd -- --seed=12345
extends SceneTree

var _watchdog_deadline_ms: int
const WATCHDOG_MS := 30_000

func _init() -> void:
    # Named run_seed (not "seed") to avoid shadowing GDScript's global seed().
    var run_seed := _arg_int("--seed", 0)
    var rng_set := RngSet.new(run_seed)
    var baseline := OS.get_static_memory_usage()
    _reset_watchdog("start")

    var game := AutoGame.new(rng_set)
    while not game.is_run_over():
        game.step()                              # issues one valid input
        if game.made_progress():
            _reset_watchdog(game.last_action())
        elif Time.get_ticks_msec() > _watchdog_deadline_ms:
            push_error("[autoplay] watchdog: no progress; state=%s" % game.dump_state())
            quit(1)
            return

    var leaked := OS.get_static_memory_usage() - baseline
    Log.info("autoplay", "run complete seed=%d mem_delta=%d bytes" % [run_seed, leaked])
    quit(0 if game.won() else 2)

func _reset_watchdog(reason: String) -> void:
    _watchdog_deadline_ms = Time.get_ticks_msec() + WATCHDOG_MS
    Log.info("autoplay", "progress: %s" % reason)

func _arg_int(flag: String, default: int) -> int:
    for a in OS.get_cmdline_user_args():
        if a.begins_with(flag + "="):
            return a.get_slice("=", 1).to_int()
    return default
```

Wire this into CI as a gate (exit code 0 = run completed). It composes with Principle 1: the same seed makes any failure reproducible on your machine.

---

## 8. Documentation & convention discipline: write for the next reader (who is an AI)

**The principle.** Every public type and non-obvious method carries a doc comment stating *intent*, not just mechanics. Naming and structure follow mechanical, predictable conventions so patterns are replicable. The codebase is *legible* — readable as prose by a contributor who has never seen it before.

**StS2 evidence.** StS2 shipped its docs precisely because it leaned on this:

- ~36 lines of XML doc per type *on average*; multi-paragraph `<summary>`, `<remarks>`, `<param>`, and `<see cref>` cross-references throughout (about 2,700 documented types).
- Mechanical naming conventions: an `"N"` prefix on Godot-`Node`-derived scene classes; consistent suffixes (`...Model`, `...ConsoleCmd`, `...Handler`, `...Action`).
- Codegen discipline: Godot SourceGenerators emit *"Cached StringNames ... for fast lookup"* via nested `MethodName`/`PropertyName`/`SignalName` classes — ~2,016 such inner classes, all following the identical pattern.

The doc comments aren't decoration; they encode *why* (e.g. `MegaLabel.DisposeCachedParagraph` explains it uses `Dispose()` not `Free()` *"because TextParagraph is RefCounted"* and is nulled to guard against quit-frame races).

**Why it helps an AI assistant.** An AI assistant's accuracy is bounded by what it can read in context. Intent-stating doc comments let it infer *why* code exists and avoid "correcting" a deliberate choice. Mechanical naming lets it *predict* names it hasn't seen (`CleaveCard` → `CleaveCardModel`), so generated code fits the first time. Consistent structure means the patterns it learns from one file transfer to the next. In practice: a class named `PlayerActionQueue` with a one-line summary and a `## ` doc comment per public method is worth more to an agent than ten pages of external wiki. This is also why a project should keep a concise `CLAUDE.md` capturing these conventions (see [Working With AI Coding Assistants](04-ai-collaboration-patterns.md) §1).

**GDScript application.** Use Godot's `##` documentation comments (they surface in the editor's built-in help) and a written convention table the agent can follow.

```gdscript
## Plays a card from hand: validates cost, pays energy, runs the card's commands,
## then moves the card to the discard pile.
##
## This is INTENT only — it enqueues an Action (see Principle 3); it does not
## mutate combat state directly. Call from input handlers, never from rules code.
##
## [param card] the CardInstance currently in hand
## [param target_id] entity id the card targets, or -1 for untargeted
## Returns false if the player cannot afford the card.
func play_card(card: CardInstance, target_id: int = -1) -> bool:
    if GameState.energy < CardDb.definition(card.id)["cost"]:
        Log.info("combat", "play rejected: insufficient energy for %s" % card.id)
        return false
    _action_queue.push(Action.new(&"play_card",
        {"card": card, "target": target_id}))
    return true
```

A minimal convention table to put in the project's context file:

| Concern | Convention |
| --- | --- |
| Definitions | `*_db.gd`, immutable data tables, no behavior |
| Runtime instances | `*_instance.gd`, holds mutable delta, references a definition |
| Player intent | `Action` records, verb = `StringName` (`&"play_card"`) |
| Game logic | `Command` subclasses with `execute`/`undo` |
| RNG | always `RngSet.stream(name)`; `chaotic` for cosmetics only |
| Logging | `Log.info/warn/error(tag, msg)`, tag = subsystem |
| Tests | `tests/test_*.gd` extending `GutTest` |

---

## The through-line

Every principle above points at the same target: **shrink the blast radius of any single change, and make its effect observable.** Determinism makes a change *reproducible*; data-driven content makes it *local*; the intent/logic split makes it *layered*; composition makes it *additive instead of combinatorial*; seams make it *testable in isolation*; observability makes it *visible*; self-play makes it *end-to-end verifiable*; and documentation makes the whole thing *legible*. A human team needs this to ship a large game without drowning in regressions. An AI assistant needs the *exact same* properties for a different reason: an LLM cannot hold the whole system in its head, so it can only contribute safely where changes are small, reproducible, and machine-checkable. That is the entire methodology in one sentence — architect the game so that the safe way to change it and the AI-leverageable way to change it are the same way. The remaining docs turn each principle into concrete workflow.
