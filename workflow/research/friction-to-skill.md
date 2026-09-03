# Friction → Skill Catalog (seed)

_Date: 2026-06-28_

> The seed catalog for the "gold-standard" set of AI-assistant skills for Godot game
> development. Method: enumerate the concrete frictions an AI coding assistant
> hits while building a Godot game, then for each friction propose **one** candidate
> skill that removes it. Every candidate traces to a finding in `STS2_EVIDENCE.md`,
> `01-phased-workflow.md`, `03-techniques.md`, `04-ai-collaboration-patterns.md`, or
> the author's unpublished StS2 study notes (not in this repo). Citations use short forms: **EVID §** = `STS2_EVIDENCE.md`
> section; **01 P\<n\>** = phased-workflow phase; **03 T\<n\>** = technique number;
> **04 §\<n\>** = AI-collaboration section; **NOTES §\<n\>** = study notes section.
>
> Forms: **CC skill** = Claude Code skill (packaged repeatable action) · **subagent**
> = an agent type run in its own context · **MCP** = tool-server · **hybrid** = skill
> that drives an MCP/subagent or shells out to headless Godot.

This is a *seed* — concrete and grounded, deliberately wider than the final set so
the next pass can prune, merge, and rank. Assumption candidates (things this catalog
takes on faith and that the next pass should validate) are listed at the end.

---

## Category: Scaffold

### 1. `godot-architecture-scaffold`
- **Form:** CC skill (hybrid — writes `.gd` files, runs `--check-only`).
- **Trigger:** Use when starting a new Godot game repo, or onboarding the methodology
  into one that lacks the AI-leverageable substrate (no seeded RNG, no intent/logic
  split, no atomic save, no test seams).
- **Inputs:** target repo root; chosen language (GDScript default); list of subsystems
  wanted (combat/save/rng/console).
- **Outputs/artifacts:** `res://systems/rng_set.gd`, `modifier_resolver.gd`,
  `game_action.gd` + `action_executor.gd`, `save_store.gd` + `save_migrator.gd`,
  `log.gd` autoload, `tests/` dir with GUT installed; a starter `CLAUDE.md`.
- **Operationalizes:** EVID §"StS2 trait → AI payoff" (the whole substrate); 03 T1–T8
  ("Adopt them in roughly that order"); NOTES §6 items 3–6,10.
- **Dependencies:** headless Godot (for `--check-only`/`--import`); GUT addon.
- **Leverage:** **high** — every other skill assumes this substrate exists; it converts
  a generic Godot project into one a machine can verify.

### 2. `ui-in-code-generator`
- **Form:** CC skill.
- **Trigger:** Use when a feature needs UI/a scene and the agent would otherwise
  hand-edit a `.tscn`/`.tres` (which it silently corrupts).
- **Inputs:** a UI spec (controls, layout, bindings) + target script path.
- **Outputs/artifacts:** a `Control`-subclass `.gd` that builds the tree in `_ready()`
  with a typed `bind()` — diffable, headlessly testable, merge-safe.
- **Operationalizes:** 04 §6 (".tscn/.tres are merge-hostile… build UI in code");
  04 §7 anti-pattern "hand-editing .tscn/.tres/UIDs"; EVID GDScript-translation notes.
- **Dependencies:** none beyond Godot.
- **Leverage:** **high** — removes the single most common Godot edit-hostility failure
  by keeping the agent's whole surface inside reviewable text.

---

## Category: Feature-loop

### 3. `ears-spec-author`
- **Form:** subagent (read-only; critiques, does not code).
- **Trigger:** Use at SPEC phase to turn a rough feature idea into an EARS contract
  with explicit non-goals — or to critique a draft for ambiguity/missing edge cases.
- **Inputs:** a draft feature description.
- **Outputs/artifacts:** `specs/<feature>.md` with EARS acceptance criteria
  (ubiquitous/event/state/unwanted/optional) + a NON-GOALS list.
- **Operationalizes:** 01 P1 (SPEC, EARS templates, non-goals); 04 §2 (SDD + EARS,
  "the value of this system is what it refuses to do"); EVID §"Models vs Entities"
  (data-shape-first specs).
- **Dependencies:** none.
- **Leverage:** **high** — non-goals are the documented antidote to the agent's
  special-casing default; cheapest place to prevent scope-pad and emergent-system erosion.

### 4. `red-test-gate`
- **Form:** hybrid (writes GUT tests, runs them headless, asserts non-zero exit).
- **Trigger:** Use at TESTS phase to author failing tests from the plan's test list and
  *prove RED* before any implementation.
- **Inputs:** approved plan's test list; target script signatures; the seed for any RNG.
- **Outputs/artifacts:** `tests/test_<feature>.gd`; a RED run report (which assertions
  failed and why); guard that the run exited non-zero for the right reason.
- **Operationalizes:** 01 P3 (RED, the two TDD anti-patterns); 04 §3 ("enforce the RED
  phase"); EVID §TestSupport (inject RNG, drive controls by signal); 03 T7.
- **Dependencies:** headless Godot + GUT; seeded-RNG substrate (skill 1).
- **Leverage:** **high** — closes the "test that already passes / silently deleted test"
  hole that makes agent TDD untrustworthy.

### 5. `feature-loop-orchestrator`
- **Form:** subagent (drives sub-skills 3,4,6,8,17 in order).
- **Trigger:** Use to run one feature end-to-end through SPEC→PLAN→RED→GREEN→VERIFY→
  REVIEW→COMMIT with one diff, one feature.
- **Inputs:** a feature idea; repo `CLAUDE.md`.
- **Outputs/artifacts:** the spec, plan, RED proof, GREEN diff, VERIFY report, REVIEW
  findings, and a commit + DECISIONS note — gated so it stops on any failure.
- **Operationalizes:** 01 (entire loop, "one feature per loop, small diffs"); 04 §3.
- **Dependencies:** plan mode; skills 3,4,6,8,17,19.
- **Leverage:** **med** — high value but mostly composition of other skills; main win is
  enforcing phase separation so the agent never jumps ahead.

---

## Category: Testing/Verification

### 6. `gut-headless-runner`
- **Form:** CC skill (or thin MCP) — shells `godot --headless`.
- **Trigger:** Use to run the GUT suite (or one file) and get a clean pass/fail summary;
  the self-check after every implementation iteration.
- **Inputs:** test dir/file glob; optional JUnit output path.
- **Outputs/artifacts:** pass/fail counts, failing-assertion digest, process exit code;
  pre-heats the import cache (`--headless --import`) first.
- **Operationalizes:** 01 P5 gate 1; 03 T10 (headless CI, exit-code contract,
  pre-heat import).
- **Dependencies:** headless Godot + GUT.
- **Leverage:** **high** — turns "did it pass" into one deterministic invocation the
  agent can run on every change; the exit code is its definition of done.

### 7. `self-play-smoke-runner`
- **Form:** hybrid (launches a headless self-play `SceneTree` script from a seed).
- **Trigger:** Use as the top-level VERIFY gate — "does a full run still complete from
  seed N without crash/soft-lock/leak?" — above per-feature unit tests.
- **Inputs:** a seed; turn/time caps; memory-delta threshold.
- **Outputs/artifacts:** run exit code (won/stuck/crashed), watchdog state dump on stall,
  memory-delta line; an `autoplay.log`.
- **Operationalizes:** 03 T6 (AutoSlay-lite, watchdog, memory delta); 01 P5 StS2-validation
  ("treat an AutoSlay-style run as your top-level VERIFY gate"); EVID §AutoSlay; NOTES §6 #10.
- **Dependencies:** headless Godot; intent/logic seam (skill 12) to drive valid actions;
  seeded RNG (skill 1).
- **Leverage:** **high** — catches the bugs unit tests miss (soft-locks, unreachable
  states, slow leaks) that only emerge over a full run.

### 8. `determinism-auditor`
- **Form:** subagent (read-only scan + property test).
- **Trigger:** Use when touching gameplay/combat/RNG, or in REVIEW, to catch determinism
  leaks before they corrupt saves/multiplayer/repro.
- **Inputs:** the diff or system dir; a seed.
- **Outputs/artifacts:** findings list (`randi()` in gameplay, `Time`/wall-clock or
  dict-iteration-order dependence in gameplay paths) with file:line; a same-seed
  reproducibility property test.
- **Operationalizes:** 03 T1 + T7; 04 §4 determinism property test; 04 §5 ("deterministic
  code") + §7 anti-pattern "non-deterministic tests"; EVID §Determinism (segregated streams,
  `Rng.Chaotic`).
- **Dependencies:** seeded-RNG substrate; headless Godot to run the property test.
- **Leverage:** **high** — a single leaked `randi()` silently breaks daily runs, netcode,
  and bug-repro; this makes the leak loud and machine-checkable.

---

## Category: Content

### 9. `content-entry-adder`
- **Form:** CC skill.
- **Trigger:** Use to add a card/relic/enemy/encounter as a **data-table entry**, never
  as a new control-flow branch.
- **Inputs:** content type; the field values; target data table (`.gd` dict or `.tres`).
- **Outputs/artifacts:** one new entry in the data table + a schema/validation check that
  the entry has required fields and no stray `if id ==` was introduced.
- **Operationalizes:** 03 T2 (data-driven content, const-vs-static-var trap); 04 §2/§3
  ("adding content is an edit to a data table… low blast radius"); EVID §"Models vs
  Entities"; NOTES §6 #3.
- **Dependencies:** data-driven content tables present (skill 1).
- **Leverage:** **high** — keeps new content a trivially-reviewable diff and structurally
  blocks the special-case failure mode.

### 10. `modifier-record-author`
- **Form:** CC skill (+ may invoke skill 8/17).
- **Trigger:** Use to implement a new combat effect (e.g. "+50% vs Bleeding") as a
  `Modifier` contribution record — and to refactor any existing `if effect == X` chain
  into the resolver.
- **Inputs:** the effect's rule (additive/multiplicative/cap + value + source); the
  contribution site.
- **Outputs/artifacts:** one `Modifier.make(...)` at the contribution site; a GUT test
  pinning the fold order; the resolver itself untouched.
- **Operationalizes:** 03 T3 (modifier-resolution pipeline, "single highest-leverage
  pattern for letting an LLM add combat content safely"); 01 P6 StS2-validation; 04 §2
  non-goals example; EVID §"Modifier-resolution / hook pipeline" (`ModifyDamageHookType`).
- **Dependencies:** `ModifierResolver` present (skill 1).
- **Leverage:** **high** — new effects compose automatically; the resolver *cannot* be
  broken by the addition, which is exactly where LLMs are most dangerous.

---

## Category: Architecture

### 11. `save-migration-author`
- **Form:** CC skill (+ generates a migration test).
- **Trigger:** Use whenever a change alters the save schema — adds/renames/removes a
  persisted field — so old saves keep loading.
- **Inputs:** the schema delta; current `CURRENT_VERSION`.
- **Outputs/artifacts:** a new `_vN_to_vN+1` pure migration step, a version bump, and a
  GUT test loading a fixture old save and asserting the migrated shape; preserves
  atomic-write + best-effort-cloud invariants.
- **Operationalizes:** 03 T5 (atomic/versioned/optional-cloud save); 04 §4 (save/migration
  as cross-validation-worthy critical logic); EVID §"Save system discipline"
  (`IMigration<T>`, atomic writes, cloud error policy); NOTES §6 #6–7.
- **Dependencies:** `SaveStore`/`SaveMigrator` substrate (skill 1).
- **Leverage:** **high** — a forgotten migration corrupts every existing player's save;
  this makes the migration step + its test mechanical and unforgettable.

### 12. `intent-logic-seam-keeper`
- **Form:** CC skill (scaffold + guard).
- **Trigger:** Use when adding a new player action, or when UI/scene code is about to
  mutate game state directly instead of enqueuing a `GameAction`.
- **Inputs:** the new action kind + args; the logic function it should dispatch to.
- **Outputs/artifacts:** one new `ActionExecutor` match arm + one logic function; a flag
  if any UI script mutates `CombatState` directly (bypassing the seam).
- **Operationalizes:** 03 T4 (intent vs logic, command queue + executor); EVID
  §"GameAction vs Command" ("a GameAction WRAPS commands, ONLY for player input");
  NOTES §4 GameActions-vs-Commands + #4.
- **Dependencies:** `GameAction`/`ActionExecutor` substrate (skill 1).
- **Leverage:** **med-high** — preserves the seam that gives undo/replay/multiplayer/
  self-play "for free"; eroding it is invisible in a diff until those features break.

---

## Category: Observability

### 13. `observability-bootstrap`
- **Form:** CC skill.
- **Trigger:** Use to add the observability surface to a project: structured logging, an
  in-game dev console compiled out of release, and build identity baked at export.
- **Inputs:** repo root; CI build metadata (commit/version/date) source.
- **Outputs/artifacts:** `log.gd` autoload (grep-friendly `[LEVEL][tag]` prefixes),
  `dev_console.gd` (LineEdit + command dict, `OS.is_debug_build()` guard), `release_info.gd`
  populated from CI.
- **Operationalizes:** 03 T8 (observability); EVID §Observability (`DevConsole`,
  `AutoSlayLog`, `ReleaseInfo`/`AssemblyHasher`); NOTES §6 #8.
- **Dependencies:** none beyond Godot; CI to inject build identity (skill 16).
- **Leverage:** **med** — turns failures into grepable, commit-pinned, reproducible reports;
  enabling tech for skill 14 rather than directly shipping a feature.

### 14. `seed-repro-harness`
- **Form:** hybrid (builds a failing test / launches the game at a reported state).
- **Trigger:** Use to reproduce a reported bug — given `seed=N, stream=rewards` (or a dev
  console state) construct a deterministic repro.
- **Inputs:** seed + stream/concern; optional dev-console command sequence; expected vs
  observed behavior.
- **Outputs/artifacts:** a failing GUT test seeded to the report, or a launch script that
  jumps the live game into the bug state via the dev console.
- **Operationalizes:** 03 T1 (bug report → `seed=12345, stream=rewards`); 03 T8 (console
  jumps to a bug state); 01 P5 (reproducible verification); EVID §Determinism.
- **Dependencies:** seeded RNG (skill 1), dev console (skill 13), GUT.
- **Leverage:** **high** — converts a vague report into a deterministic failing test the
  agent can fix and prove; eliminates "works on my machine."

---

## Category: Asset-gen

### 15. `sprite-batch`
- **Form:** hybrid (drives the local ComfyUI HTTP API; writes a manifest; runs `--import`).
- **Trigger:** Use to batch-generate **draft** sprites/tilesets/backgrounds/variants with
  consistency guardrails — not hero assets.
- **Inputs:** prompt list; character LoRA + ControlNet pose refs; checkpoint + seed.
- **Outputs/artifacts:** PNGs in `res://art/raw/`; a regenerability manifest pinning
  checkpoint+LoRA+seed per asset; an IP-provenance note; `--import` ingest.
- **Operationalizes:** 03 T9 (AI asset pipeline; identity-by-LoRA, pose-by-ControlNet;
  "drafts/variants/backgrounds — humans own heroes"); EVID GDScript notes (asset gen runs
  outside the game).
- **Dependencies:** local ComfyUI (an image-generation helper / local install); headless Godot
  for `--import`.
- **Leverage:** **med** — real bulk-art leverage, but bounded: humans must judge every
  asset, so it is orchestration/bookkeeping, not authorship.

---

## Category: CI

### 16. `godot-ci-scaffold`
- **Form:** CC skill.
- **Trigger:** Use to wire headless CI: run the GUT suite (and the self-play gate) on every
  push with import-cache caching and an exit-code gate.
- **Inputs:** repo + CI provider (GitHub Actions default); whether C# (mono image) or
  GDScript-only (GUT).
- **Outputs/artifacts:** `.github/workflows/test.yml` (preheat import, GUT, self-play),
  `.godot/` cache keyed on project+scripts hash; ensures `export_presets.cfg` is committed.
- **Operationalizes:** 03 T10 (headless CI, Docker images, cache key, commit export_presets);
  01 §"Priming" (skills package the headless gate).
- **Dependencies:** headless Godot in CI; skills 6 and 7 for the actual gates.
- **Leverage:** **med** — green CI is the agent's definition of done and makes "passes for
  me" and "passes in CI" converge; one-time setup, recurring payoff.

---

## Category: Review

### 17. `independent-diff-auditor`
- **Form:** subagent (adversarial; starts from the spec, not the author's narrative).
- **Trigger:** Use at REVIEW to challenge a diff: hunt special cases, hidden state, missing
  tests, scope beyond non-goals, and `.tscn` edits that shouldn't exist.
- **Inputs:** `git diff`; the feature spec + non-goals.
- **Outputs/artifacts:** findings by severity with file:line and proposed fixes —
  correctness bugs, non-goal violations, duplication that should reuse, and branches that
  signal a missing general mechanism (resolver/table).
- **Operationalizes:** 01 P6 (independent review, "value comes from challenging"); 04 §4
  (worker/auditor split, concrete auditor checklist); 04 §7 anti-patterns; EVID
  §"Modifier-resolution" (the `if effect == X` smell).
- **Dependencies:** none (a second agent/model); benefits from skill 8 for the determinism check.
- **Leverage:** **high** — the diff-level catch-all that stops the special-case-generator
  failure mode from landing.

### 18. `critical-logic-cross-validator`
- **Form:** subagent (multi-model — generate with one model, validate with another).
- **Trigger:** Use only for logic where a silent bug is catastrophic: save/load, migrations,
  combat math, RNG/determinism.
- **Inputs:** the critical module + its tests; a second model.
- **Outputs/artifacts:** an agreement/disagreement report; disagreements flagged for a human
  gate; extra property tests where models diverge.
- **Operationalizes:** 04 §4 ("multi-model cross-validation for critical logic… two models,
  one human, on the code you cannot afford to get wrong"); EVID §"Save system discipline"
  (testability via independent managers).
- **Dependencies:** access to a second model; the modules under skills 1/10/11.
- **Leverage:** **med** — narrow scope but the highest-consequence code; agreement across
  independent models is real signal, disagreement is a cheap human-gate trigger.

---

## Category: Context-maintenance

### 19. `claude-md-curator`
- **Form:** CC skill.
- **Trigger:** Use at COMMIT when a feature established a reusable pattern/invariant, or
  when `CLAUDE.md` has drifted from the code (new commands, new seams, new non-negotiables).
- **Inputs:** the landed diff + DECISIONS note; current `CLAUDE.md`.
- **Outputs/artifacts:** a focused `CLAUDE.md` edit (architecture summary, update-order
  invariants, conventions, non-negotiables, commands) kept concise; optional `AGENTS.md`
  mirror.
- **Operationalizes:** 04 §1 (CLAUDE.md is "the single highest-leverage artifact"); 01 P7
  (record the why; update CLAUDE.md when a pattern is established); 01 §"Priming"; EVID
  §"Documentation discipline" (intent-stating docs are *why* the code is AI-legible).
- **Dependencies:** none.
- **Leverage:** **high** — the only thing the agent reads before any code; a current
  CLAUDE.md is what makes every other session start on-rails instead of re-discovering.

---

## Compact table

| # | Skill | Cat | Form | Friction removed | Grounding | Deps | Lev |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | godot-architecture-scaffold | Scaffold | CC/hybrid | Project lacks the AI-leverageable substrate | EVID trait-map; 03 T1–T8; NOTES §6 | godot, GUT | high |
| 2 | ui-in-code-generator | Scaffold | CC | .tscn/.tres edit-hostility & corruption | 04 §6/§7; EVID notes | godot | high |
| 3 | ears-spec-author | Feature-loop | subagent | Agent codes before contract; scope-pad | 01 P1; 04 §2 | — | high |
| 4 | red-test-gate | Feature-loop | hybrid | Tests that pre-pass / silent deletion (no RED) | 01 P3; 04 §3; 03 T7 | godot, GUT | high |
| 5 | feature-loop-orchestrator | Feature-loop | subagent | Manual phase orchestration; jumping ahead | 01 (all); 04 §3 | skills 3,4,6,8,17,19 | med |
| 6 | gut-headless-runner | Testing | CC/MCP | GUT/headless/import/exit-code wiring | 01 P5; 03 T10 | godot, GUT | high |
| 7 | self-play-smoke-runner | Testing | hybrid | Can't see the running game; soft-locks/leaks | 03 T6; 01 P5; EVID AutoSlay | godot, skills 1,12 | high |
| 8 | determinism-auditor | Testing | subagent | Determinism leaks (randi/time/dict order) | 03 T1/T7; 04 §4/§5 | godot, skill 1 | high |
| 9 | content-entry-adder | Content | CC | Data content special-cased into branches | 03 T2; 04 §2/§3 | skill 1 | high |
| 10 | modifier-record-author | Content | CC | Pairwise effect special-casing | 03 T3; 04 §2; EVID hooks | skill 1 | high |
| 11 | save-migration-author | Architecture | CC | Save schema evolves without migration | 03 T5; 04 §4; EVID saves | skill 1 | high |
| 12 | intent-logic-seam-keeper | Architecture | CC | UI mutates state; intent/logic seam erodes | 03 T4; EVID GameAction | skill 1 | med-high |
| 13 | observability-bootstrap | Observability | CC | No structured logs / console / build identity | 03 T8; EVID observ. | godot, skill 16 | med |
| 14 | seed-repro-harness | Observability | hybrid | Can't reproduce a reported bug | 03 T1/T8; 01 P5 | skills 1,13, GUT | high |
| 15 | sprite-batch | Asset-gen | hybrid | Asset gen: consistency, manifest, import | 03 T9 | ComfyUI, godot | med |
| 16 | godot-ci-scaffold | CI | CC | CI: headless/import-cache/exit-gate wiring | 03 T10; 01 priming | godot CI, skills 6,7 | med |
| 17 | independent-diff-auditor | Review | subagent | Author rationalizes own code; special cases land | 01 P6; 04 §4/§7 | 2nd agent | high |
| 18 | critical-logic-cross-validator | Review | subagent | Silent bugs in save/RNG/combat | 04 §4 | 2nd model | med |
| 19 | claude-md-curator | Context-maint. | CC | CLAUDE.md goes stale; patterns unrecorded | 04 §1; 01 P7 | — | high |

---

## Assumption candidates (for the next pass to validate)

1. **GDScript-only is the default target.** The methodology writes GDScript even though
   StS2 is C#. If a candidate game is C#, skills 1/4/6/16 must switch to gdUnit4/gdUnit4Net
   and `mono-*` CI images (per 03 T10 note) — the catalog assumes the GDScript path.
2. **Headless Godot is on PATH in dev and CI.** Skills 1,4,6,7,8,14,16 all shell out to
   `godot --headless`; if it isn't reliably invocable, these degrade to scaffold-only.
3. **GUT, not gdUnit4, is the test runner.** Chosen for the GDScript path; the C# path
   would flip this.
4. **The substrate exists before content/loop skills run.** Skills 7–14 depend on skill 1's
   RngSet/ModifierResolver/GameAction/SaveStore; order of adoption matters.
5. **Some skills are really subagents/multi-model, not packaged actions.** 3,5,8,17,18 derive
   value from *independent context/another model* (04 §4). Whether the harness can spawn a
   genuinely independent (different-model) auditor is unverified — if not, 18 collapses into 17.
6. **Form boundaries blur (CC skill vs MCP vs hybrid).** gut-headless-runner and
   self-play-smoke-runner could each be a thin MCP tool-server instead of a shell-out skill;
   chosen as hybrids for portability. Worth deciding once, globally.
7. **Local ComfyUI availability gates asset-gen.** Skill 15 assumes the local ComfyUI
   skill + a trained character LoRA; without them it cannot enforce consistency and drops
   to low leverage.
8. **The feature-loop-orchestrator may be redundant with the human running the loop.** If
   the human drives phases via plan mode, skill 5 is overhead; it earns its place only for
   unattended/batch feature runs.
9. **Overlap to resolve in pruning:** determinism-auditor (8) ⊂ independent-diff-auditor (17)
   scope; modifier-record-author (10) overlaps content-entry-adder (9) at the
   data-vs-branch boundary; observability-bootstrap (13) + seed-repro-harness (14) may merge.
10. **A scene/UID-repair skill was omitted.** UID/`.import` breakage (04 §6) is handled
    preventively by skill 2 (build UI in code) rather than a curative "regenerate .tscn/UID"
    skill — the next pass should decide whether a curative skill is also warranted.
