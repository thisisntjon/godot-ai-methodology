# StS2 Evidence Pack (grounding for the methodology doc set)

**Method.** Slay the Spire 2 (StS2) was studied **read-only** through the C# XML
documentation it publicly ships (`sts2.xml`, 99,429 lines, about 2,700 documented types,
roughly 36 lines of doc per type). The engine is **Godot 4.5.1** with **C# / .NET 9**
(not GDScript). No decompilation, no `.pck` extraction, no asset extraction. The quotes
below are short, attributed excerpts from the developers' own `<summary>` comments, used
for commentary on *techniques*; `[...]` marks elisions. No game data or code is reproduced,
and every code example in the doc set is original GDScript. The XML lives in the game's
install directory (not included in this repo).

---

## Namespace taxonomy (the namespaces the docs reference, with type counts)

- `Core.Models` (86) — data-driven definitions; `Core.Entities` (42) — runtime instances.
- `Core.GameActions` (17) — player intent; `Core.Commands` (6) — units of game logic.
- `Core.Hooks` (3) — effect/modifier resolution; `Core.Random` (2) — seeded RNG.
- `Core.Saves` (66), `Core.AutoSlay` (31), `Core.Multiplayer` (78), `Core.DevConsole` (10),
  plus `TestSupport`.

---

## Quotable developer summaries (short excerpts from `<summary>` comments)

### Intent vs logic — GameActions vs Commands
- **GameAction:** "A GameAction is a thin wrapper around an async task [...] these small units of logic are handled by **Commands** [...] A GameAction WRAPS these commands, and should ONLY be used for player input." Examples it lists to wrap: playing a card, drinking a potion, ending turn. NOT to wrap: dealing damage.
- **ActionExecutor:** "Responsible for pulling actions from the PlayerActionQueueSet and executing them." (Note: the documented type is `ActionQueueSet` under `Core.GameActions.Multiplayer`; "PlayerActionQueueSet" appears only inside this comment.)
- Other GameActions: `EndPlayerTurnAction`, `UndoEndPlayerTurnAction`, `UsePotionAction`, `DiscardPotionGameAction`, `PickRelicAction`, `MoveToMapCoordAction`, `VoteForMapCoordAction`, `VoteToMoveToNextActAction`, `ReadyToBeginEnemyTurnAction`. (Note the multiplayer voting + undo actions.)

### Determinism / RNG
- **MegaRandom:** "Xoshiro256** (xor, shift, rotate) pseudo-random number generator (PRNG)." Ported from the Redzen library; full upstream license retained. Has seed init / re-init.
- **Rng:** "A custom random class which allows predictable results when utilizing seeds." Ergonomic constructor "for creating an RNG for a specific piece of content during a run. This RNG will be unique among: The run, The player SLOT, The ID of the content passed." Uses "player _slot index_, rather than the NetId, to ensure consistent results when playing a daily run."
- **Rng.Chaotic:** "A non-deterministic RNG instance. This will not produce the same results after saving and loading. Good for when we need to randomize things that don't impact gameplay."
- **PlayerRngSet:** segregated streams — `Rewards` ("What cards are generated for rewards"), `Shops` ("What the different shops are selling"), `Transformations` ("What a transformed card will roll into").

### Data-driven content (Models vs Entities)
- `Core.Models`: definitions — `CardModel`, `EncounterModel`, `Cards`, `Relics`, `Powers`, `Potions`, `Monsters`, `CardPools`, `Acts`, `Characters`, `Modifiers`, `Orbs`, `Enchantments`, `Afflictions`, `Achievements`, `Badges`.
- **SingletonModel:** "A model which is instantiated once for an entire run. Currently only one for multiplayer scaling."
- `Core.Entities`: runtime instances — `Creatures`, `Players`, `Cards`, `Merchant`, `RestSite`, `Gold`, `Potions`, `Ascension`, `Ancients`.
- **CalculatedVar** (Localization.DynamicVars): "A special type of DynamicVar that is used for cards that include a calculation in their base behavior. For example, [a card] uses a subclass of this for its 6 base damage + 2 extra damage for each Strike."

### Modifier-resolution / hook pipeline (validates the "modifier resolver" idea)
- **Hook:** "A static class containing all of the gameplay hooks." Hook types include BeforeAttack, AfterCardPlayed, AfterCurrentHpChanged, AfterModifyingDamageAmount, etc. Signatures pass state (RunState, CombatState, Models, Creatures, ValueProps).
- **ModifyDamageHookType (enum):** `Additive` — "Additive damage hooks from effects like StrengthPower"; `Multiplicative` — "Multiplicative damage hooks from effects like VulnerablePower"; `Cap` — "Damage-capping hooks from effects like IntangiblePower"; `All` — "Include all ModifyDamage hooks. Most back-end ModifyDamage hook calls will use this." Referenced impls: `AbstractModel.ModifyDamageAdditive/Multiplicative/Cap()`.
- `Core.Hooks` also: `HpLossHookPhase`. This is the same shape as a modifier-resolution pipeline: effects contribute Additive/Multiplicative/Cap contributions that resolve to a final value, instead of pairwise special cases.

### Save system discipline
- **SaveManager:** "Implements the Singleton pattern [...] coordinates multiple specialized save managers [...] **improves testability** by allowing each save manager to be tested independently [...] Save files are stored in a user-scoped, platform-specific location: [...] <user data directory>". Also: "Constructor with dependency injection support" and a flag to "Force all operations to be performed synchronously. Only use in tests."
- **GodotFileIo:** "Implements the ISaveStore interface… All file I/O operations related to game saves should use this class to ensure proper path handling, **atomic writes**, and consistent error handling across the application."
- **CloudSaveStore:** "saves files to both local and cloud storage [...] always read from local storage [...] All cloud operations are best-effort. **A cloud failure must never prevent local saves from working or the game from starting.**"
- **IMigration<T>:** "Strongly typed interface for migrations that operate on a specific save type." Plus `Migrations`, `MigrationUtil`, `MigratingData` (JSON-manipulation API).

### Automated verification (AutoSlay = self-play smoke testing)
- **AutoSlayer:** "Main orchestrator for AutoSlay. Runs the game automatically for smoke testing." Static `IsActive`; `Start(seed, …)`/`Stop()`; type-safe `GetCurrentScreen<T>()`.
- **AutoSlayConfig:** parameterized timeouts — `runTimeout` ("Maximum time for a complete run"), `defaultRoomTimeout`, `defaultScreenTimeout`, `watchdogTimeout` ("If no progress for this long, dump state and fail").
- **Handler hierarchy:** `IHandler → IRoomHandler, IScreenHandler` with 20+ concrete handlers (CombatRoomHandler, EventRoomHandler, CardRewardScreenHandler, MapScreenHandler…). CombatRoomHandler: "Applies massive defensive buffs and plays all cards each turn."
- **Watchdog:** `Reset(reason)` ("Call this whenever meaningful progress is made"), `Check()` ("Throws TimeoutException if no progress for too long"), `DumpState()` ("Dumps the current game state for debugging").
- **WaitHelper:** `Until(condition, cancellationToken, timeout, reason)` "Also checks the watchdog periodically to detect stuck states"; `DumpSceneTreeContext()` "Dumps scene tree context when a wait times out, to help debug what's actually there."
- **AutoSlayLog:** "Structured logging for AutoSlay with consistent prefixes for easy filtering. Writes to both the standard Godot log and a dedicated autoslay.log file."
- **MemoryProfiler:** "Captures memory and resource snapshots during AutoSlay runs, logging deltas from a baseline to detect memory/resource leaks."

### TestSupport (testability seams)
- **ICardSelector:** "Interface for automated card selection, used by both test mode and AutoSlay."
- **TestMode:** `IsOn`/`IsOff` global flags.
- **TestRngInjector:** `SetCombatCardGenerationOverride()` ("Force specific cards to show up for CardFactory.GetDistinctForCombat"), `SetInitialShuffleOverride()` ("Force a specific order for the initial shuffle").
- **UiHelper.Click():** "Clicks a clickable control by directly emitting the Released signal. This bypasses hover/focus/pause checks that can fail in headless/automated testing."

### Observability
- **DevConsole** commands: `DieConsoleCmd`, `GodModeConsoleCmd`, `GoldConsoleCmd`, `HealConsoleCmd`, `RemoveCardConsoleCmd`, `TravelConsoleCmd`, `WinConsoleCmd`, `SentryConsoleCmd` ("Debug console command for testing Sentry integration"), `GetLogsConsoleCmd` (collects+zips logs/saves/Linux core dumps). `DevConsole.ProcessCommand()`: if a command "must be networked and a run is in progress, a GameAction will be enqueued to all peers before the command is executed."
- **ReleaseInfo / ReleaseInfoManager:** build identity (version, commit, date, branch) baked in for reproducible bug reports; `SemanticVersion`. `SentryService` for telemetry.

### Multiplayer (determinism-dependent)
- **CombatStateSynchronizer:** "Responsible for synchronizing all players' combat states before combat begins."
- **NetTypeCache<T>:** "Bidirectional map of types to unique integer IDs, for use in serialization. All classes which implement this type will automatically be mapped by this class."

### Assets / threading
- **AssetCache:** "preloading and caching assets… eliminate duplicate loads of the same asset. This class is thread-safe."
- **AtlasManager:** "Manages texture atlases by parsing .tpsheet files and creating AtlasTextures on demand. Thread-safe via ConcurrentDictionary caching."

### Documentation & codegen discipline (why the codebase is AI-legible)
- ~36 lines of XML doc per type on average; multi-paragraph `<summary>`, `<remarks>`, `<param>`, `<see cref>` cross-refs throughout.
- Godot SourceGenerators emit cached `StringName` lookups: nested `MethodName`/`PropertyName`/`SignalName` classes ("Cached StringNames… for fast lookup"). ~2,016 such inner classes.
- **MegaLabel idioms:** `DisposeCachedParagraph` "releases the cached TextParagraph… Uses Dispose() (not Free()) because TextParagraph is RefCounted. Nulled to guard against AdjustFontSize running during Godot's quit frames." Custom `mega_text` (MegaLabel, MegaRichTextLabel) + `Core.RichTextTags` (RichTextJitter, RichTextSine, RichTextFlyIn, RichTextFadeIn, RichTextThinkyDots, color tags) extend BBCode.

---

## StS2 trait → why it matters for AI-assisted dev (mapping for the docs)

| StS2 trait | AI-assisted-dev payoff |
| --- | --- |
| Deterministic seeded RNG, segregated streams | AI can reproduce a bug from a seed; tests are stable; daily/multiplayer consistency |
| Data-driven Models vs Entities | AI adds content by editing data, not control flow — low blast radius, reviewable diffs |
| Hook/ModifyDamage Additive·Mult·Cap resolution | New effects compose automatically; no combinatorial special-casing for AI to get wrong |
| GameAction (intent) wraps Command (logic) | Clean seam for undo/replay/multiplayer; AI changes logic without touching input plumbing |
| TestSupport: DI, TestRngInjector, headless Click | AI can write deterministic tests against real systems without production coupling |
| AutoSlay self-play + Watchdog + MemoryProfiler | A machine-checkable "does a full run still work / leak?" gate AI can run and read |
| Save: atomic writes + IMigration + best-effort cloud | Schema can evolve safely; AI follows a learnable migration pattern; optional infra never blocks |
| Observability: DevConsole, structured logs, ReleaseInfo/Sentry | AI (and you) can inspect live state, reproduce from build identity |
| Exhaustive docs + codegen conventions ("N" prefix, cached StringNames) | AI reads intent from comments; mechanical patterns are replicable; fewer wrong guesses |

## GDScript translation notes (for writers)
- C# `Models` (classes) → GDScript data as `.gd` dictionaries/`const` tables or `Resource` (.tres) — prefer `.gd` dicts for diff/AI-friendliness; note Godot's parse-time `const` limitation (use `static var` for `PackedStringArray`/containers).
- C# Hook static dispatch + ModifyDamage Additive/Mult/Cap → a GDScript `ModifierResolver` that collects modifier records and folds them (sum additives, multiply multipliers, apply caps, clamp).
- C# `Rng`/`MegaRandom` seeded → GDScript `RandomNumberGenerator` with explicit `seed`/`state`, one instance per concern (rewards/shops/etc.), plus a separate "chaotic" `randi()` for cosmetic-only randomness.
- C# AutoSlay → a GDScript headless "auto-play" mode driven by `--headless`/`-s` script that issues valid inputs, with a watchdog timer and `OS.get_static_memory_usage()` deltas.
- C# TestRngInjector → seed injection + dependency-injected RNG / override hooks in GDScript tests (GUT).
- C# DevConsole → an in-game GDScript command console (LineEdit + dispatch dict), guarded out of release builds.
- C# Sentry → optional; GDScript can ship `sentry-godot` GDExtension OR a minimal opt-in crash/log uploader; keep best-effort.
