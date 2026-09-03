# 01 — The Per-Feature Phased Workflow (with Claude Code)

> The repeatable loop for building **one** feature with an AI coding assistant: a
> disciplined pass from spec to commit that keeps diffs small, tests honest, and
> the agent on rails.

This is the core loop of the method. Run it once per feature, end to end. Each
phase has a clear deliverable, a clear hand-off to the agent, and a copy-paste
prompt template. The phases are deliberately separated so the agent never
"helpfully" jumps ahead — the most common failure mode of AI coding is writing
code before the contract exists.

The seven phases:

```
SPEC  ->  PLAN  ->  TESTS (RED)  ->  IMPLEMENT (GREEN)  ->  VERIFY  ->  REVIEW  ->  COMMIT & DOCUMENT
```

Two rules hold across all of them:

1. **One feature per loop.** If the spec needs the word "and" between two
   capabilities, it is two features. Run the loop twice.
2. **Small diffs.** A reviewable change is a few hundred lines at most. If the
   plan implies more, decompose until each step is independently reviewable. See
   [AI Collaboration Patterns](04-ai-collaboration-patterns.md) for why diff size
   is the single biggest lever on review quality.

Before the first loop in a session, prime the agent with context — see
[Priming the session](#priming-the-session-claudemd) below.

---

## Phase 1 — SPEC

**Goal:** an unambiguous, testable contract. No code, no design.

**What to do.** Write acceptance criteria in **EARS** notation (Easy Approach to
Requirements Syntax) — a small set of sentence templates that force each
requirement to be singular and checkable:

- **Ubiquitous:** *The system shall \<requirement\>.*
- **Event-driven:** *When \<trigger\>, the system shall \<response\>.*
- **State-driven:** *While \<state\>, the system shall \<response\>.*
- **Unwanted:** *If \<condition\>, then the system shall \<response\>.*
- **Optional:** *Where \<feature present\>, the system shall \<response\>.*

Then write **NON-GOALS** explicitly. This is the highest-leverage part of the
spec for AI work: the agent will pad scope unless you fence it out. A non-goal is
a promise of what the diff will *not* touch.

The spec is the durable artifact; the code is regenerable output from it
(spec-driven development). Keep the spec in the repo next to the feature.

**Hand the agent:** nothing yet, or use the agent only to *critique* your draft
spec for ambiguity and missing edge cases — not to write it.

**Prompt template:**

```text
You are a requirements reviewer. Do NOT write code or design.
Here is a draft feature spec for a Godot 4.x game system:

<paste draft>

Tasks:
1. Rewrite each acceptance criterion in EARS notation (ubiquitous / event /
   state / unwanted / optional). Flag any criterion that is not singular or not
   testable.
2. List edge cases and failure conditions I omitted.
3. Propose 3-5 explicit NON-GOALS for this feature.
Return only the revised spec. Ask me before assuming any behavior.
```

> **StS2 validation.** StS2 ships content as **data-driven Models vs runtime
> Entities** — `CardModel`, `RelicModel`, etc. are definitions separate from the
> `Creatures`/`Cards` instances that use them (`Core.Models` / `Core.Entities`).
> Writing the spec as *data shape first* mirrors that split and keeps the eventual
> diff confined to a table rather than smeared across control flow.

---

## Phase 2 — PLAN

**Goal:** an agreed implementation approach. **Still no code.**

**What to do.** Use Claude Code's **plan mode** (Shift+Tab to toggle). In plan
mode the agent reads files, asks questions, and proposes an approach but is
prevented from editing. You approve the plan before any write happens. For
larger or unfamiliar areas, spawn a **Plan subagent** (or several in parallel) to
explore different parts of the codebase independently and report back — parallel
exploration without polluting the main thread's context. See
[AI Collaboration Patterns](04-ai-collaboration-patterns.md) for the subagent
fan-out pattern.

A good plan names: files to be touched, the new functions/signals, the data
shape, the test list, and which existing code is reused. If the plan invents new
systems where existing ones would do, push back.

**Hand the agent:** the approved spec, the relevant existing files (or let it
discover them in plan mode), and the project's `CLAUDE.md`.

**Prompt template:**

```text
[Enter plan mode first.]
Read the spec below and the relevant existing code. Produce an implementation
plan ONLY — no code.

Spec:
<paste EARS spec + non-goals>

Your plan must list:
- Exact files to change/create (respect the non-goals — touch nothing else).
- New functions, signals, and exported vars, with type signatures.
- The data shape (dictionary/Resource layout) for any new content.
- The GUT test list you will write in the next phase (one bullet per test).
- Which EXISTING code/systems you will reuse instead of adding new ones.
Stop and ask if the spec is ambiguous. Wait for my approval before coding.
```

---

## Phase 3 — TESTS (RED)

**Goal:** failing GUT tests that encode the acceptance criteria. The test suite
must run and **fail for the right reason** before any implementation exists.

**What to do.** Write GUT tests first, one per acceptance criterion where
practical. Then **run them and confirm RED.** Agents have two notorious TDD
failure modes: writing tests that already pass (testing nothing) and silently
deleting a failing test to "make it green." You must see the red.

Install GUT by copying `addons/gut/` into the project and enabling the plugin.
Tests extend `GutTest`; methods named `test_*` auto-run. Run headless:

```bash
godot --headless -s res://addons/gut/gut_cmdln.gd \
  -gdir=res://tests -ginclude_subdirs -gexit
```

The runner's exit code reflects pass/fail, so it gates cleanly in scripts and CI
(`-goutput` emits JUnit XML). At this phase you *want* a non-zero exit.

**Hand the agent:** the approved plan's test list, the GUT conventions, and the
target script's intended signature (from the plan).

**Prompt template:**

```text
Write GUT tests ONLY — do not create or modify the implementation.
Implement exactly the test list from the approved plan:

<paste test list>

Rules:
- Tests extend GutTest; one behavior per test_* method; use before_each() for setup.
- Cover the unwanted-behavior (If/then) criteria, not just the happy path.
- For anything random, seed a RandomNumberGenerator so the test is deterministic.
- Do NOT write the production code. Do NOT weaken a test to make it pass.
After writing, tell me the exact headless command to run, and predict which
assertions will fail and why.
```

> **StS2 validation.** StS2's `TestSupport` namespace exists precisely to make
> real systems testable without production coupling: `TestRngInjector` can
> `SetInitialShuffleOverride()` to force a deterministic draw order, and
> `UiHelper.Click()` "bypasses hover/focus/pause checks that can fail in
> headless/automated testing" by emitting the control's signal directly. Build
> the same seams in GDScript — inject the RNG, drive controls by emitting their
> signals — so headless tests exercise production code paths.

---

## Phase 4 — IMPLEMENT (GREEN)

**Goal:** the **smallest** change that turns the suite green. Nothing more.

**What to do.** Let the agent write production code against the failing tests.
Constrain it to the files named in the plan. Resist refactors, extra features,
and "while I'm here" cleanups — those are separate loops. Keep the diff small so
the later REVIEW phase is tractable.

**Hand the agent:** the red test output, the plan, and the target files.

**Prompt template:**

```text
Make the failing GUT tests pass with the SMALLEST change that satisfies them.

Constraints:
- Only edit the files named in the approved plan. Do not touch anything else.
- Do not add features beyond the spec. Do not modify the tests.
- Idiomatic Godot 4.x: typed vars, `signal x` / `x.emit()` / `x.connect(callable)`,
  @export / @onready, RandomNumberGenerator for randomness.
- Prefer reusing existing helpers over adding new ones.
Run the headless GUT command after each change and report the pass/fail counts.
Stop when all target tests are green; do not gold-plate.
```

---

## Phase 5 — VERIFY

**Goal:** independent confirmation that it actually works — in tests **and** in
the running game.

**What to do.** Three gates, in order:

1. **Headless tests** — re-run the full suite (not just the new file) and confirm
   green with a clean exit code. Pre-heat the import cache first with
   `godot --headless --import` so the run is stable.
2. **Run the game** — launch it and exercise the feature by hand. Tests prove the
   contract; they don't prove the feature *feels* right or wires into scenes
   correctly.
3. **Visually confirm** — for anything on screen, look at it. The `/verify` and
   UI-QA tooling can drive this; for game feel there is no substitute for
   watching it.

For randomized features, verification must be **reproducible**: fix a seed and
the run is identical every time.

**Hand the agent:** the run/verify commands and the seed.

**Prompt template:**

```text
Verify the feature end to end:
1. Run: godot --headless --import   (pre-heat), then the full GUT suite headless.
   Report total pass/fail and the process exit code.
2. Launch the game with a FIXED seed and walk through the spec's acceptance
   criteria one by one. For each, state PASS/FAIL with the observed behavior.
3. Re-run step 2 with the SAME seed and confirm identical results (determinism).
If anything fails, stop and report — do not patch silently.
```

> **StS2 validation.** StS2 makes verification reproducible by construction. Its
> seeded RNG (`Rng`, "a custom random class which allows predictable results when
> utilizing seeds") uses **segregated streams** (`PlayerRngSet`: `Rewards`,
> `Shops`, `Transformations`) so one subsystem's draws can't perturb another's —
> a bug reproduces from a seed. And **AutoSlay** is a self-play smoke test:
> `AutoSlayer` "runs the game automatically for smoke testing" from a seed, with a
> `Watchdog` that dumps state and fails "if no progress for this long." Treat an
> AutoSlay-style headless self-play run as your top-level VERIFY gate — "does a
> full session still complete from seed N?" — above per-feature unit tests. See
> [Techniques](03-techniques.md) for building the seeded-RNG and smoke-test
> harness in GDScript.

---

## Phase 6 — REVIEW

**Goal:** catch correctness bugs and unnecessary complexity before it lands.

**What to do.** Run a focused review of the working diff. Use `/code-review` for
bug-hunting and `/simplify` for reuse/altitude cleanups. The highest-value review
is **independent**: spawn a review subagent (or a second model) that did not write
the code, so it critiques rather than rationalizes. Value comes from the reviewer
*challenging* the author, not agreeing. See
[AI Collaboration Patterns](04-ai-collaboration-patterns.md).

Look specifically for: behavior outside the non-goals, missing edge cases from
the spec, duplicated logic that should reuse an existing system, and special-cased
branches that hint a general mechanism is missing.

**Prompt template:**

```text
You are an independent reviewer; you did NOT write this code. Review the current
diff only (git diff). Check against this spec and its non-goals:

<paste spec + non-goals>

Report, by severity:
- Correctness bugs and unhandled edge cases (cite file:line).
- Anything that violates a non-goal or exceeds the spec.
- Duplication that should reuse existing code; branches that suggest a missing
  general mechanism (a resolver/table) instead of pairwise special cases.
Do not rewrite yet — list findings with proposed fixes for me to approve.
```

> **StS2 validation.** StS2's damage pipeline is the antidote to special-casing:
> the `ModifyDamageHookType` enum resolves effects as `Additive` (e.g. Strength),
> `Multiplicative` (e.g. Vulnerable), and `Cap` (e.g. Intangible) and folds them
> to a final value, so new effects compose automatically instead of adding pairwise
> branches. If review finds a stack of `if effect == X` cases, that's the smell —
> point the agent at a resolver. Detailed in [Techniques](03-techniques.md).

---

## Phase 7 — COMMIT & DOCUMENT

**Goal:** land the change and record the *why* — especially tuning numbers and
decisions an agent (or future you) can't re-derive from code.

**What to do.** Commit with a message that states the behavior and references the
spec. Then record anything non-obvious: balance/tuning values and why, design
trade-offs taken, and any deviation from the plan. Update `CLAUDE.md` if the
feature established a pattern future sessions should follow.

**Prompt template:**

```text
1. Stage only the files for this feature. Write a commit message: a one-line
   summary, then a body stating which acceptance criteria are met and naming the
   spec file. Do not commit unrelated changes.
2. Append a short DECISIONS note to the feature doc: tuning values chosen and
   why, trade-offs, and anything that diverged from the plan.
3. If this established a reusable pattern, propose a 2-4 line addition to CLAUDE.md.
```

> **StS2 validation.** StS2 bakes build identity into the binary — `ReleaseInfo`
> carries commit, version, date, and a `MainAssemblyHash` so any bug report is
> reproducible against an exact build. Your commit + decisions note is the
> small-scale version: it ties observed behavior to a recoverable point in
> history.

---

## Priming the session (CLAUDE.md)

Before the loop, prime the agent. Claude Code automatically reads hierarchical
`CLAUDE.md` memory files that cascade up the directory tree, so put project-wide
rules at the repo root and area-specific notes deeper. Keep it concise — it is
loaded into every session.

A useful game-dev `CLAUDE.md` includes:

```markdown
# Project memory (loaded every session)

## Stack
- Godot 4.x, GDScript only. Tests: GUT in res://tests.
- Run tests: godot --headless -s res://addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit

## Conventions
- Logic lives in plain .gd scripts (unit-testable). Treat .tscn/.tres/.import as
  editor-owned, regenerable outputs — do not hand-edit their structure.
- Randomness: inject a RandomNumberGenerator; never call global randi() in gameplay.
- Wire with signals / exported refs / groups, not absolute NodePaths.

## Workflow
- Follow the phased loop: SPEC -> PLAN (plan mode) -> RED tests -> GREEN -> VERIFY -> REVIEW -> COMMIT.
- One feature per change. Small diffs. Ask before exceeding the spec.
```

**Claude Code features that map onto the loop:**

- **Plan mode** — the PLAN phase guardrail (design without writing).
- **Subagents** — parallel exploration in PLAN; an independent reviewer in REVIEW;
  each runs in its own context window so the main thread stays clean.
- **Skills** — package the repeatable bits (e.g. a project skill that runs the
  headless GUT suite and summarizes failures, or launches the game at a fixed
  seed) so VERIFY is one invocation.
- **Context files (`CLAUDE.md`)** — persistent priming so you don't re-explain the
  stack every loop.

> **Why this works on a Godot codebase.** StS2 is heavily documented — roughly 36
> lines of XML doc per type — which is *why* an AI can read intent from it. You
> get the same legibility cheaply via `CLAUDE.md` plus EARS specs plus tests:
> together they tell the agent what the code is *for*, not just what it does.

---

## Worked micro-example: a "Bleed" stacking status

A tiny feature taken through every phase. **Bleed** deals 1 damage per stack at
the start of the owner's turn, then loses one stack.

**SPEC (EARS + non-goals).**

- *When* a creature with Bleed > 0 starts its turn, the system *shall* deal
  damage equal to the current Bleed stack count to that creature.
- *When* Bleed damage has been applied, the system *shall* reduce that creature's
  Bleed by 1.
- *If* a creature's Bleed reaches 0, *then* the system *shall* remove the Bleed
  status from that creature.
- **Non-goals:** no UI/tooltip; no interaction with Block or other modifiers; no
  save/load; no multiplayer sync.

**PLAN (abridged).** New `res://systems/status/bleed.gd` (pure logic, no nodes).
Operates on a `creature` object exposing `hp: int` and a `statuses: Dictionary`.
Tests in `res://tests/test_bleed.gd`. Reuse the existing `RandomNumberGenerator`
injection pattern (none needed here — Bleed is deterministic). No scene changes.

**TESTS (RED).**

```gdscript
extends GutTest

const Bleed := preload("res://systems/status/bleed.gd")

var creature: Object

func before_each() -> void:
	creature = _make_creature(20)        # hp = 20
	creature.statuses["bleed"] = 3

func test_deals_damage_equal_to_stacks() -> void:
	Bleed.on_turn_start(creature)
	assert_eq(creature.hp, 17, "3 stacks should deal 3 damage")

func test_loses_one_stack_after_ticking() -> void:
	Bleed.on_turn_start(creature)
	assert_eq(creature.statuses["bleed"], 2, "Bleed should drop by 1")

func test_removed_when_it_hits_zero() -> void:
	creature.statuses["bleed"] = 1
	Bleed.on_turn_start(creature)
	assert_false(creature.statuses.has("bleed"), "Bleed should be removed at 0")

func test_no_op_without_bleed() -> void:
	creature.statuses.erase("bleed")
	Bleed.on_turn_start(creature)
	assert_eq(creature.hp, 20, "No Bleed means no damage")
```

Run headless — expect failures: `bleed.gd` doesn't exist yet (RED confirmed).

**IMPLEMENT (GREEN).**

```gdscript
extends RefCounted
## Stacking damage-over-time status. Pure logic; no scene dependencies.
## Loaded by path (no `class_name`) so the test's `preload` const owns the name.

const KEY := "bleed"

## Applies one tick of Bleed at the owner's turn start, then decays one stack.
static func on_turn_start(creature: Object) -> void:
	var stacks: int = creature.statuses.get(KEY, 0)
	if stacks <= 0:
		return
	creature.hp -= stacks
	stacks -= 1
	if stacks <= 0:
		creature.statuses.erase(KEY)
	else:
		creature.statuses[KEY] = stacks
```

Re-run headless: 4/4 green.

**VERIFY.** Full suite green, clean exit code. In-game, apply Bleed 3 to an
enemy, end turn, confirm it takes 3 then 2 then 1 and the status icon clears.
Because the logic is deterministic, the same scripted scenario reproduces
identically every run.

**REVIEW.** Independent reviewer notes Bleed reads `creature.hp` directly rather
than routing through a damage entry point, so future Block/Intangible effects
won't apply. That's *correctly* out of scope here (non-goal), but worth a
`# TODO: route through damage resolver when modifiers land` and a line in the
decisions note — a signal that the general mechanism (a damage resolver, à la
StS2's Additive/Mult/Cap fold) is the next feature.

**COMMIT & DOCUMENT.**

```text
feat(status): add stacking Bleed DoT (ticks at turn start, decays 1/turn)

Implements bleed.gd per spec specs/bleed.md. Deals stack-count damage at owner
turn start, decays one stack, removes at 0. Deterministic; no Block interaction
yet (non-goal). Decision: bypasses damage resolver pending the resolver feature.
```

---

## The loop on one line

> **SPEC** the contract (EARS + non-goals) → **PLAN** in plan mode (no code) →
> **TESTS** first and confirm **RED** → **IMPLEMENT** the smallest **GREEN** →
> **VERIFY** headless + in-game + reproducibly from a seed → **REVIEW**
> independently for bugs and over-complexity → **COMMIT & DOCUMENT** the why.

Keep each diff small, prime with `CLAUDE.md`, and let plan mode and subagents
enforce the separation between thinking and typing. Continue to
[Techniques](03-techniques.md) for the building blocks each phase leans on
(seeded RNG, modifier resolvers, data-driven content, smoke-test harnesses) and
[AI Collaboration Patterns](04-ai-collaboration-patterns.md) for getting the most
out of plan mode, subagents, and independent review.
