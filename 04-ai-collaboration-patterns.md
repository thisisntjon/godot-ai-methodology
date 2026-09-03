# 04 — Working With AI Coding Assistants

*How to collaborate with coding agents (Claude Code: plan mode, subagents, context
files) on a Godot 4.x project so the codebase stays correct, reviewable, and
AI-legible — using Slay the Spire 2's documentation discipline as the model.*

> Prerequisites: [01 — The Per-Feature Phased Workflow](01-phased-workflow.md) for
> the spec → plan → RED → GREEN loop these patterns plug into, and
> [05 — Quick-Reference Checklists](05-checklists.md) for the scannable gates. Tool
> names, commands, and URLs are sourced in [references.md](references.md).

The premise of this doc: an agent is only as good as the structure you give it.
A coding agent has no persistent memory of your project, no taste about your
emergent systems, and a strong bias toward "helpfully" completing whatever it
sees. Every pattern here exists to constrain that bias — to make the right change
the easy change and the wrong change loud in review.

---

## 1. Context files (CLAUDE.md / AGENTS.md)

Claude Code reads hierarchical `CLAUDE.md` memory files that cascade up the
directory tree and are loaded into every session
([Claude Code memory docs](https://code.claude.com/docs/en/memory)). This is the
single highest-leverage artifact in the repo: it is the only thing the agent
reads *before* it reads any code. Treat it as the project's onboarding doc for a
competent contributor who has no context and will forget everything tomorrow.

Keep it concise — it costs tokens on every turn. Put **stable, load-bearing**
facts in it; link out to longer docs (this doc set) rather than inlining them.

**What belongs in it:**

- **Architecture summary** — one paragraph: the major systems and how data flows
  between them. Name the seams (e.g. "intent/input is separate from logic" — the
  GameAction-wraps-Command pattern surfaced in the skeleton below).
- **Update order / invariants** — the sequence systems must be touched in. StS2's
  damage pipeline resolves contributions as *Additive → Multiplicative → Cap*
  (`ModifyDamageHookType`, evidence pack §"Modifier-resolution / hook pipeline");
  an agent that doesn't know this order will produce subtly wrong combat math.
- **Conventions** — naming (StS2 prefixes scene-node classes with `N`, evidence
  pack §"Namespace taxonomy"), file layout, where data lives vs where logic lives.
- **Non-negotiables** — the rules that must never be violated: "all gameplay RNG
  goes through the seeded streams, never `randi()`"; "no new singletons";
  "scenes are editor-owned, build UI in code."
- **Commands** — the exact, copy-pasteable invocations for test/lint/run so the
  agent can verify its own work (see [references.md](references.md) §1–2):

A short skeleton:

```markdown
# Project — Agent Context

## Architecture
- Data-driven: content lives in `res://data/*.gd` tables; logic in `res://systems/`.
- Intent vs logic: UI emits *intents*; `CommandRunner` executes *commands*. UI never
  mutates game state directly.
- Combat damage resolves through `ModifierResolver` in fixed order:
  additive → multiplicative → cap → clamp. Never special-case a pairwise effect.

## Conventions
- Typed GDScript everywhere (`var n: int`, typed signals, typed returns).
- One responsibility per script; if a file passes ~200 lines, split it.
- Scenes (.tscn/.tres) are editor-owned. Prefer building UI in code.

## Non-negotiables
- All gameplay randomness uses `RngStreams` (seeded). `randi()` is cosmetic-only.
- No hidden global state. State is passed in or read from an injected context.
- Don't invent special cases for content. Add data, not branches.

## Commands
- Tests:  godot --headless -s res://addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit
- Parse-check a script:  godot --headless --check-only -s <path>
- Import cache (run before headless): godot --headless --import
```

`AGENTS.md` is the cross-tool equivalent (same content, vendor-neutral name); if
you use multiple agents, keep one canonical file and symlink/point the other at
it rather than letting them drift.

---

## 2. Spec-driven development with EARS + explicit non-goals

Spec-driven development (SDD) treats the **spec as the primary artifact** and code
as regenerable output
([Pluralsight](https://www.pluralsight.com/resources/blog/software-development/spec-driven-development-with-AI-SDD),
[Microsoft](https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering)).
For a game, the spec is where you do the design thinking; the agent turns it into
GDScript. A practical lifecycle: **spec → clarify → plan → tasks → implement →
validate** ([Augment Code](https://www.augmentcode.com/guides/spec-driven-development-ai-agents-explained)).

Write acceptance criteria in **EARS** (Easy Approach to Requirements Syntax) — a
small set of sentence patterns that produce unambiguous, testable requirements
([Pluralsight](https://www.pluralsight.com/resources/blog/software-development/spec-driven-development-with-AI-SDD)).
The core templates:

- **Ubiquitous:** *The system shall …*
- **Event-driven:** *When `<trigger>`, the system shall …*
- **State-driven:** *While `<state>`, the system shall …*
- **Unwanted:** *If `<condition>`, then the system shall …*
- **Optional:** *Where `<feature present>`, the system shall …*

Example spec fragment for a status effect:

```markdown
## Feature: Vulnerable (damage-taken multiplier)

### Acceptance criteria (EARS)
- When a creature with Vulnerable takes attack damage, the system shall multiply
  the post-additive damage by 1.5 before applying caps.
- While a creature has 0 stacks of Vulnerable, the system shall apply no multiplier.
- When a turn ends for a creature with Vulnerable, the system shall reduce its
  Vulnerable stacks by 1.
- If a damage source is non-attack (e.g. loss-of-HP), then the system shall not
  apply the Vulnerable multiplier.

### Non-goals (do NOT implement)
- Do NOT special-case Vulnerable in any card or monster script. It is a modifier
  that contributes a *multiplicative* record to ModifierResolver; nothing else
  should know it exists.
- Do NOT add a "double Vulnerable" or boss-immunity branch. If such a rule is
  needed later, it will be its own modifier record, not a condition here.
- Do NOT change the resolution order or clamp behavior.
```

**Why non-goals matter — this is the crux for emergent systems.** An agent's
default failure mode is to make the immediate test pass by the most direct route,
which is almost always a special case: an `if card.id == "...":` branch, a
hard-coded threshold, a one-off flag. Each special case is locally correct and
globally corrosive — it breaks the composition that makes emergent systems work.
StS2's design is the counter-example: effects contribute typed *contributions*
(`Additive` from Strength, `Multiplicative` from Vulnerable, `Cap` from
Intangible) that fold into a final number, "instead of pairwise special cases"
(evidence pack §"Modifier-resolution / hook pipeline"). New content composes
automatically *because no effect knows about any other effect.* A non-goals list
is how you tell the agent: the value of this system is what it *refuses* to do.
Without it, the agent will helpfully special-case your generality away.

---

## 3. Plan-then-implement, TDD, small diffs

### Plan mode first

For anything bigger than a one-liner, have the agent produce a plan and stop —
Claude Code's plan mode does exactly this. You review the plan (files it will
touch, the approach, the test it will write) *before* a single line is written.
Cheap to redirect a plan; expensive to unwind a wrong implementation across a
dozen files. The plan is also where you catch the agent reaching for the editor,
inventing a special case, or missing a non-goal.

### TDD with agents — enforce the RED phase

Agents are notorious for two TDD anti-patterns: writing a test that already
passes, or deleting a failing test to "fix" the suite. The discipline is to
enforce the **red** phase explicitly — confirm the test fails *for the right
reason* before implementing
([Simon Willison](https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/)).
Specs define *what*; tests are runtime proof
([Augment Code](https://www.augmentcode.com/guides/spec-tdd-shippable-ai-generated-code)).
With GUT ([references.md](references.md) §1):

```gdscript
extends GutTest

# RED: written against the spec in §2, run BEFORE any implementation exists.
func test_vulnerable_multiplies_attack_damage() -> void:
    var resolver := ModifierResolver.new()
    resolver.add_additive(6)            # base attack
    resolver.add_multiplicative(1.5)    # one Vulnerable stack
    assert_eq(resolver.resolve(), 9, "6 * 1.5 == 9 after additive→mult fold")

func test_non_attack_damage_ignores_vulnerable() -> void:
    var resolver := ModifierResolver.new()
    resolver.add_additive(6)
    # No multiplicative record is added for loss-of-HP sources.
    assert_eq(resolver.resolve(), 6, "non-attack damage is unmodified")
```

Workflow: agent writes the test → you run it and confirm it fails → agent
implements → you run it green → review the diff. Make the test command from your
`CLAUDE.md` the agent's self-check on every iteration.

### Small reviewable diffs

Decompose work into small, reviewable diffs backed by tests and observability,
not ad-hoc prompting
([DEV](https://dev.to/austinwdigital/ai-assisted-development-in-2026-best-practices-real-risks-and-the-new-bar-for-engineers-3fom),
[arXiv](https://arxiv.org/html/2602.00180v1)). A diff you can hold in your head is
a diff you can actually review; a 600-line diff gets rubber-stamped, which is how
special cases and hidden state slip in. Data-driven architecture pays off here:
adding content is an edit to a data table (low blast radius, trivially
reviewable), not a change to control flow. This is the AI-assisted-dev payoff of
StS2's "Models vs Entities" split — "AI adds content by editing data, not control
flow" (evidence pack §"StS2 trait → why it matters").

---

## 4. Multi-agent patterns

A single agent in a single context is a single point of failure. Splitting work
across agents (or models) buys you parallelism *and* independent judgment.

### Parallel exploration subagents

Claude Code can dispatch subagents that work in their own context windows. Use
them for **read-only, fan-out investigation** where the findings — not the
edits — are what you want: "find every call site that mutates combat state,"
"map how save data flows from disk to runtime," "list every place `randi()` is
called." Each subagent returns a digest; you synthesize. This keeps your main
context clean and lets independent searches run concurrently. Exploration
subagents should not edit — they report.

### Worker / auditor split

Have one agent **implement** and a second, independent agent **audit** — review
the diff against the spec and non-goals, hunt for special cases, hidden state,
and missing tests. The auditor must start from the spec, not from the worker's
narrative, or it will simply agree. The value comes from the auditor *challenging*
the work, not ratifying it
([Bizzmark](https://bizzmarkblog.com/the-mechanics-of-shared-context-why-your-llm-thread-needs-a-multi-model-auditor/)).
A good auditor prompt enumerates concrete failure modes: "Does any new code branch
on a content ID? Does it introduce global mutable state? Does every acceptance
criterion have a test? Does it touch a `.tscn` it shouldn't?"

### Multi-model cross-validation for critical logic

For logic where a silent bug is catastrophic — **save/load, migrations, combat
math, RNG/determinism** — generate with one model and validate with a different
one. Different models fail differently; agreement across independent models is
real signal, disagreement is a flag for a human gate
([Bizzmark](https://bizzmarkblog.com/the-mechanics-of-shared-context-why-your-llm-thread-needs-a-multi-model-auditor/)).
StS2 treats exactly these areas as high-discipline: save uses **atomic writes**
and strongly-typed `IMigration<T>` migrations, and the save architecture is split
into specialized managers specifically because it "improves testability… tested
independently with appropriate mocks and stubs" (evidence pack §"Save system
discipline"). Cross-validation is the agent-era version of that discipline: two
models, one human, on the code you cannot afford to get wrong.

A determinism property test is the kind of artifact this produces — easy for any
model to write, decisive when run:

```gdscript
func test_seeded_run_is_reproducible() -> void:
    var a := RngStreams.new(12345)
    var b := RngStreams.new(12345)
    var draws_a: Array[int] = []
    var draws_b: Array[int] = []
    for i in 100:
        draws_a.append(a.rewards.randi())
        draws_b.append(b.rewards.randi())
    assert_eq(draws_a, draws_b, "same seed → identical reward stream")
```

---

## 5. Keeping the codebase AI-legible

Everything above works better when the code itself is easy for an agent to read
and hard to misread. StS2 is the reference: ~36 lines of XML doc per type,
multi-paragraph `<summary>`/`<remarks>` with `<see cref>` cross-refs, and
mechanical naming conventions throughout — which is *why* its intent is legible to
both humans and machines (evidence pack §"Documentation & codegen discipline").
Translate that discipline to GDScript:

- **Doc comments that state intent, not mechanics.** Say *why* and *what
  invariant holds*, not what the next line obviously does.

  ```gdscript
  ## Resolves a damage value by folding modifier contributions in a fixed order:
  ## additive (Strength) → multiplicative (Vulnerable) → cap (Intangible) → clamp ≥ 0.
  ## Effects contribute records; no effect knows about any other. Do not add
  ## content-specific branches here — add a contribution record instead.
  class_name ModifierResolver
  extends RefCounted
  ```

- **Deterministic code.** No reliance on dictionary iteration order, frame timing,
  or wall-clock for anything that affects gameplay. Route all gameplay randomness
  through seeded streams; reserve a separate "chaotic" source for cosmetic-only
  randomness. StS2 segregates streams by concern (`Rewards`, `Shops`,
  `Transformations`) and marks its non-deterministic instance explicitly as
  "Good for when we need to randomize things that don't impact gameplay"
  (evidence pack §"Determinism / RNG"). Determinism is what lets an agent
  *reproduce a bug from a seed*.

- **Small, focused scripts.** One responsibility per file. A 60-line script with a
  clear name fits in an agent's working set and is reviewable at a glance; a
  600-line god-object does not.

- **Data over code.** Express content as data the agent edits, not branches it
  writes. Note Godot's parse-time `const` limitation: a `const` container is fine
  as a literal, but if you need typed containers with methods or that other code
  mutates/initializes, use `static var`:

  ```gdscript
  class_name Cards

  # Literal lookup table — const is fine here.
  const DEFINITIONS := {
      "strike":  {"cost": 1, "damage": 6, "tags": ["attack"]},
      "defend":  {"cost": 1, "block": 5,  "tags": ["skill"]},
  }

  # Typed array that other systems append to / query → static var, not const.
  static var attack_ids: PackedStringArray = PackedStringArray(["strike"])
  ```

- **Naming conventions.** Consistent, mechanical naming (StS2's `N` prefix for
  node classes, plus its Models-vs-Entities split — `CardModel`/`EncounterModel`
  definitions in `Core.Models` vs. runtime `Creatures`/`Players` in
  `Core.Entities`) lets an agent infer a type's role from its name and replicate
  the pattern correctly.

- **No hidden state.** Pass state in or read it from an injected context; avoid
  globals that mutate behavior from afar. Hidden state is the bug an agent cannot
  see in the diff and cannot reproduce in a test. Prefer typed signals and
  explicit dependencies:

  ```gdscript
  signal damage_resolved(target: Creature, amount: int)

  # emit:
  damage_resolved.emit(target, final_amount)
  # connect (Godot 4 Callable form — never the 3.x string form):
  damage_resolved.connect(_on_damage_resolved)
  ```

---

## 6. Godot-specific friction & mitigations

Godot's editor-centric workflow fights agents in specific, predictable ways. Know
them and mitigate structurally.

| Friction | Why it hurts an agent | Mitigation |
| --- | --- | --- |
| `.tscn`/`.tres` are text but **merge-hostile** | They look diffable, so an agent will hand-edit them. The format has strict structure (`ext_resource`/`sub_resource`/`load_steps`) that hand-edits silently corrupt ([TSCN format](https://docs.godotengine.org/en/stable/engine_details/file_formats/tscn.html)). | Treat scenes/resources as **editor-owned, regenerable outputs**. Build UI/scenes in code where practical; keep logic in scripts. |
| Fragile node paths & signal wiring | Absolute `NodePath`s and editor-wired signals break on refactor and are invisible to an agent reading scripts. | Prefer **signals, exported references, and groups** over hard-coded tree paths ([Godot best practices](https://docs.godotengine.org/en/stable/tutorials/best_practices/godot_interfaces.html)). Wire signals in code, not the inspector. |
| **UID** references (`uid://…`) | UID bookkeeping lives in `.godot/` and `.uid` files; a hand-authored UID is wrong and breaks loads. | Never hand-author UIDs. Let the editor or `--import` generate/resave them ([CLI tutorial](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html)). |
| Editor-vs-code split | Some steps (import settings, baking, project settings) only exist in the editor; an agent can't perform them. | Identify editor-only steps in the plan and have the **human** do them; the agent does everything that lives in scripts. |

**Build UI in code where practical.** A scene built in script is reviewable in a
diff, testable headlessly, and free of merge conflicts and invisible wiring:

```gdscript
## Card UI assembled in code — no .tscn, fully diffable and unit-testable.
class_name CardView
extends Control

var _title := Label.new()

func _ready() -> void:
    var box := VBoxContainer.new()
    add_child(box)
    box.add_child(_title)

func bind(card_id: StringName) -> void:
    var def: Dictionary = Cards.DEFINITIONS[card_id]
    _title.text = "%s (%d)" % [card_id, def["cost"]]
```

The throughline: **logic in scripts, composition via Resources/data, scenes as
thin regenerable shells, editor-only steps reserved for the human.** That keeps
the agent's entire working surface inside text it can read, edit, and test —
which is also exactly the surface CI can verify headlessly
([references.md](references.md) §2).

---

## 7. Anti-patterns

- **Letting the agent invent special cases.** An `if x.id == "...":` branch in a
  system script is the default agent failure mode and the death of an emergent
  system. Catch it in plan review and the auditor pass (§§2–4); make "add a
  contribution record, not a branch" a non-negotiable in `CLAUDE.md`.
- **Giant multi-purpose scripts.** God-objects exceed the agent's reliable working
  set and turn every change into a risky one. Split by responsibility.
- **Non-deterministic tests.** Tests that depend on timing, iteration order, or
  unseeded randomness fail flakily; agents "fix" flaky tests by deleting them.
  Seed everything; assert on values, not luck.
- **Hand-editing `.tscn`/`.tres`/UIDs.** Looks fine in the diff, corrupts the
  resource at load. Regenerate through the editor instead.
- **Skipping the RED phase.** A test written after the code, or one that never
  failed, proves nothing. Confirm failure first (§3).
- **Hidden global state.** State an agent can't see in the diff is state it will
  break. Inject dependencies; pass context explicitly (§5).
- **Mega-diffs.** A diff too large to review is a diff that hides the other
  anti-patterns on this list. Keep changes small (§3).
- **Trusting agreement over challenge.** Two agents that agree because they share
  context have told you nothing. Make the auditor adversarial and start it from
  the spec (§4).

---

### The model to internalize

Slay the Spire 2 is legible to tooling not by accident but by discipline:
exhaustive intent-stating docs, deterministic seeded RNG, data-driven content,
composition over special-casing, and testability seams baked into the
architecture (evidence pack §"StS2 trait → why it matters"). None of that
requires C#, an LLM, or their engine. It requires deciding that the codebase
should be *readable by something that has no memory and no taste* — and then
holding that line in every spec, every diff, and every context file. Do that, and
the agent becomes a force multiplier instead of a special-case generator.

> See also: [01 — The Per-Feature Phased Workflow](01-phased-workflow.md) ·
> [05 — Quick-Reference Checklists](05-checklists.md) ·
> [references.md](references.md)
