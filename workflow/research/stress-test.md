# Adversarial Stress-Test of the Hypothesis

_Date: 2026-06-28_

> **Hypothesis under test:** "There exists a definable, high-leverage set of skills
> (Claude Code skills + subagents + MCP), grounded in our StS2/methodology findings,
> that would materially improve AI-assisted Godot development."
>
> **This document's job:** build the strongest case _against_, then qualify it. For each
> objection: (a) what must be TRUE for it to hold, (b) what evidence from the sibling
> angles (env-probe, godot-mcp, existing-skills) confirms or refutes it, (c) the
> mitigation. Ends with hold-conditions, a CORE-vs-speculative split, and a refined
> hypothesis.

The hypothesis is seductive because the methodology docs are genuinely good. That is
exactly why it deserves an attack: a strong knowledge base creates a halo that makes
*any* operationalization look justified. The danger is not that the skills are bad — it
is that they may be **redundant, aspirational, or aimed at the wrong bottleneck**, and
each one carries permanent discovery + maintenance cost.

---

## Objection 1 — "Docs + a good CLAUDE.md capture most of the value"

**The attack.** Doc 04 §1 says it itself: the `CLAUDE.md`/`AGENTS.md` is "the single
highest-leverage artifact in the repo… the only thing the agent reads *before* it reads
any code." Everything in the methodology — non-goals, the modifier pipeline contract, the
RNG discipline, "no hand-edit .tscn" — is *prose the agent can already read*. A
well-structured context file that links the doc set delivers the knowledge transfer at
near-zero marginal cost, loads automatically every session, and needs no discovery. A
bespoke skill must be *recognized and triggered* to fire at all; if the knowledge is
needed on every turn (conventions, invariants), a skill is strictly worse than memory
because skills load on demand, not always-on.

**Holds if:** the methodology's value is mostly *declarative knowledge* (facts, rules,
patterns the agent applies while writing) rather than *procedural action* (multi-step
sequences with tool calls, gates, and artifacts). For pure knowledge, CLAUDE.md wins.

**Evidence that confirms / refutes:**
- _Refuted-in-part by existing-skills:_ the author's own skill library already proves the
  knowledge-vs-procedure line. the generic spec, plan, TDD, debug, and operational-hardening skills,
  `end-session-closeout` are skills precisely because they are **procedures with gates and
  artifacts**, not facts. The Godot analogue that survives this objection must likewise be
  procedural: *scaffold these 7 files*, *run this headless gate and parse the exit code*,
  *drive this self-play loop* — not "remember that RNG is seeded."
- _Confirms the attack:_ Techniques in doc 03 that are mostly "write code shaped like X"
  (seeded RNG, data tables, modifier resolver, intent/logic split) are **knowledge**. An
  agent that has read doc 03 + a CLAUDE.md pointer writes them fine. A "seeded-RNG skill"
  is a thin wrapper around a code template the agent can already produce.
- _Decisive check:_ the author's actual Godot project has **no CLAUDE.md** (none found; only the
  StS2 install, which is not his repo). The cheapest, highest-leverage move — a Godot
  `CLAUDE.md` generator — has not been done. Until it is, proposing ten skills is
  optimizing the second-order term while the first-order term is zero.

**Mitigation.** Split the deliverable: (1) a **Godot CLAUDE.md/AGENTS.md generator** that
emits the always-on declarative layer (architecture summary, invariants, non-negotiables,
the exact headless commands) — this captures the bulk of doc 04 §1 value for one cheap
skill; (2) reserve standalone skills for the **procedural** residue that a context file
genuinely cannot do (scaffolding, running gates, driving the engine). Anything that is
"the agent should know X" goes in the generated CLAUDE.md, not a skill.

---

## Objection 2 — MCP dependency risk: the best skills are thin wrappers without it

**The attack.** The skills with the highest claimed leverage — live scene-tree inspection,
self-play smoke runs, screenshot-verify, input simulation, "run it and watch it" — are all
**runtime-automation** skills. Their value is the runtime bridge, not the prompt. If no
Godot MCP / headless harness is installed and verified *in the author's environment*, these
degrade into prose that says "you should inspect the scene tree" with no tool to do it: a
thin prompt-wrapper masquerading as a capability. A skill that cannot perform its verb is
worse than no skill — it implies a capability that isn't there and wastes a discovery slot.

**Holds if:** (a) no working Godot MCP is installed in-env, AND (b) the `godot` binary is
not reliably invocable headlessly, AND (c) the team builds the runtime skills anyway on the
assumption the plumbing "will be there."

**Evidence that confirms / refutes:**
- _Confirms (b):_ env-probe signal is already negative — `godot` is **NOT on PATH** in this
  session's shell (confirmed here in both the PLAN registry and a direct `which godot`
  miss). The StS2 install ships `launch_*.bat` that hard-code a path, but the author's own project
  has no verified headless invocation. Every "run the game / run GUT / self-play" skill is
  **blocked on this single unverified assumption.**
- _Partially refutes the pessimism (a):_ the godot-mcp landscape in 2026 is **more mature
  than the PLAN assumed.** Multiple actively-developed servers exist with real runtime
  control — `godot-mcp-runtime` (screenshots, input simulation, live GDScript against the
  running tree), Godot MCP Pro (163 tools incl. record/replay), GoPeak (95+ tools, DAP
  debugger, ClassDB introspection). So the capability is *purchasable/installable*, not
  science-fiction. The risk is not "MCP doesn't exist" but "**MCP is not yet wired and
  verified in the author's env, and is third-party / version-coupled / partly paid.**"
- _Decisive check:_ does at least one Godot MCP respond to a trivial call (e.g. list the
  scene tree of a throwaway project) on the author's machine, against his Godot 4.x version? Until
  that probe is green, treat all runtime skills as **aspirational**.

**Mitigation.** Hard-gate the runtime skills behind a one-time **capability probe**: a
skill should first assert "godot binary present + chosen MCP responds" and degrade loudly
("BLOCKED: no Godot runtime bridge — install X, then re-run") instead of pretending. Build
the env-independent CORE first; defer every runtime skill until the probe is green.
Pin the MCP server + Godot version in the repo so the bridge is reproducible, not a
per-machine surprise.

---

## Objection 3 — The binding constraint is human design/taste/scope, not tooling

**The attack.** The methodology's own crux (doc 04 §2) is that the agent "has no taste
about your emergent systems" and the load-bearing artifact is the **non-goals list** — a
*design* act. The recurring failure mode it warns about (the agent special-casing your
generality away) is caught by *human judgment in plan review*, not by a tool. Doc 06's
friction table reserves the genuinely blocking steps — import settings, baking, project
settings, editor-only wiring — explicitly for the **human**, because the agent *cannot*
do them. For a solo dev building a game, the scarce resources are design clarity, scope
discipline, and art/feel taste. Skills cannot manufacture any of those. If tooling is not
the bottleneck, a skill suite is a precision answer to the wrong question.

**Holds if:** the dominant cost in the author's loop is deciding *what* to build and *whether it
feels good* (design/scope), not the mechanical cost of *writing and verifying* correct
GDScript. For a one-person project this is the likely default.

**Evidence that confirms / refutes:**
- _Confirms:_ doc 04 §2 + §6 and doc 00 (principles) repeatedly locate the irreducible
  work in the human's hands — non-goals, plan review, editor-only steps, "humans own hero
  assets" (doc 03 §9). The methodology is, by its own account, a discipline for *constraining*
  an agent's bias, i.e. a human-judgment scaffold.
- _Partially refutes:_ there is real *mechanical* friction the human shouldn't be spending
  taste on — wiring GUT/headless, scaffolding the RNG/resolver/save seams correctly the
  first time, not corrupting `.tscn`/UID files, regenerating import caches. Removing that
  toil *redirects* human attention toward the design work, which is leverage even if it
  doesn't create taste. So tooling is a *secondary* but non-zero constraint.
- _Decisive check:_ in a sample of the author's recent Godot sessions, what fraction of wall-clock
  is "deciding/designing/judging feel" vs. "fighting the engine + boilerplate + verifying"?
  If the former dominates by a wide margin, down-weight the whole suite. (existing-skills
  angle should sanity-check this against how often the spec / debug skills actually fire on Godot work.)

**Mitigation.** Aim skills at the *toil*, not the *taste*. The one place a skill can touch
design is by **forcing the human to author non-goals** before code (which spec authoring / adversarial spec review
already do) — so the Godot contribution is a *Godot-specific spec lens* (does this effect
add a contribution record or a special case? does it touch a `.tscn` it shouldn't?), not a
new design engine. Accept that the suite's ceiling is "make the mechanical part cheap so
the human spends their hours on design" — and size the investment accordingly.

---

## Objection 4 — Skill sprawl: massive overlap with the existing ~23 skills

**The attack.** the author already owns a **complete idea→spec→plan→build→ship workflow** plus
orchestration and QA. Mapped against the methodology:

| Methodology / proposed Godot capability | Already covered by existing skill |
| --- | --- |
| Spec-driven dev + EARS + non-goals (doc 04 §2) | spec authoring + adversarial spec review |
| Plan-then-implement, small diffs (doc 04 §3) | planning + phased-planning workflows |
| TDD / enforce RED (doc 04 §3, technique 7) | a red-first TDD skill |
| Root-cause debugging from a seed (technique 1+8) | a root-cause debugging skill |
| Multi-model cross-validation / auditor (doc 04 §4) | a multi-model review step |
| Asset-generation pipeline (technique 9) | an image-generation helper (already drives the local stack) |
| Operational hardening (technique 8, save robustness) | an operational-hardening pass |
| Final verification gate (technique 10) | `end-session-closeout`, `verify`, `code-review` |
| UI/visual verification | `ui-qa-orchestrator` suite (Playwright/Chrome — **web, not Godot**) |
| Roadmapping above the workflow | goal-ladder + phased-planning workflows |

Most of the methodology's "AI-collaboration patterns" are **already operationalized
generically**. A "Godot-spec" or "Godot-TDD" skill would be a re-skin that silently
duplicates the spec / TDD skills, splitting their maintenance and confusing discovery (which one
fires?). Every narrow skill also taxes the *selection* step: more skills = more
description-matching overhead = more chance the wrong one triggers. Twenty-three is already
a lot; pushing toward thirty with near-duplicates is negative-sum.

**Holds if:** the proposed Godot skills overlap the existing generic ones in *trigger and
procedure*, differing only in domain flavor that could instead live in CLAUDE.md.

**Evidence that confirms / refutes:**
- _Strongly confirms:_ the table above is direct from the existing-skills inventory. The
  generic workflow is real and shipped. the image-generation helper alone retires technique 9 as a skill
  candidate. The UI-QA suite is **web-only** (Playwright/axe/Chrome MCP) and does *not*
  transfer to a Godot game window — so "visual verification for Godot" is genuinely
  net-new, but it's a *runtime/MCP* skill (see Objection 2), not a sprawl win.
- _Refutes for a narrow set:_ scaffolding the Godot architecture, the GDScript-4.x idiom
  guard, the headless GUT/self-play gate, and live scene inspection have **no existing
  equivalent**. These are the only proposals that clear the duplication bar.

**Mitigation.** Apply a strict **net-new test**: a Godot skill ships only if it is either
(a) impossible to express as a `CLAUDE.md` fact, AND (b) not already covered by a generic
skill that could be made Godot-aware via context. Prefer **composing** existing skills
(feed the spec / TDD / debug skills a Godot context pack) over **forking** them. Cap the net-new
Godot surface at a handful; reject every "Godot-flavored X of an existing skill."

---

## Objection 5 — GDScript/engine fit can make a "skill" net-negative

**The attack.** The assistant is measurably weaker at GDScript than at C#/Python: less
training data, and a long tail of Godot-3-vs-4 API churn the docs themselves keep warning
about (`Callable` signals vs the 3.x string form; `const` vs `static var` for typed
containers; `FileAccess` has no `close()`; never hand-author `uid://`). A code-generating
skill that bakes in even one stale idiom or hallucinated API becomes a **confident,
reusable error factory** — worse than the agent reasoning from current docs each time,
because it launders a wrong pattern as a blessed template. The merge-hostility of
`.tscn`/`.tres` (doc 06) compounds it: a scaffolder that emits scenes the agent then
hand-edits actively causes corruption.

**Holds if:** the skill *generates GDScript/scenes* and its templates are not continuously
validated against the current Godot version (4.x is a moving target).

**Evidence that confirms / refutes:**
- _Confirms the risk:_ doc 03/04/06 enumerate at least five specific traps, which is itself
  evidence the assistant gets them wrong often enough to warrant warnings. A frozen template
  inherits whichever version's idioms it was written against.
- _Refutes the fatalism:_ this same weakness is the **strongest argument FOR exactly one
  kind of skill** — a *pinned, version-stamped GDScript-4.x idiom guard* that converts the
  scattered warnings into a single checked reference the agent loads before writing. The
  failure mode (stale templates) is a *maintenance* problem, not a reason to abstain; it's
  solved by a verify step (`godot --headless --check-only`) baked into the skill so a
  template that no longer parses fails loudly.
- _Decisive check:_ does the scaffolder's output **parse-check clean** on the author's Godot
  version in CI/headless? If there's no parse gate, the net-negative risk is live.

**Mitigation.** Any GDScript-emitting skill must (1) be **version-stamped** to a Godot
release, (2) end with a **parse-check gate** (`--check-only`) so stale output is caught
mechanically, and (3) emit **scripts, not scenes** wherever practical (build UI in code per
doc 06), treating `.tscn`/`.tres` as editor-owned. A skill that can't run its own parse
gate (because `godot` isn't on PATH — Objection 2) should not generate code unsupervised.

---

## Conclusions

### (a) Conditions under which the hypothesis HOLDS

The hypothesis survives — but only in a **much narrower form** than "a gold-standard suite."
It holds when ALL of these are true:

1. **The skill is procedural, not declarative.** Pure knowledge goes in a generated
   CLAUDE.md (Obj 1). A skill must *do* something a context file can't.
2. **It is net-new vs. the existing 23.** No re-skin of the generic spec / plan / TDD / debug /
   image-generation / operational-hardening skills (Obj 4). It composes them with Godot context instead.
3. **It targets toil, not taste** — boilerplate, wiring, verification — accepting design
   remains human (Obj 3).
4. **Its runtime dependency is verified in-env, or it degrades loudly.** No skill silently
   assumes a Godot MCP / headless binary that isn't proven present (Obj 2).
5. **Any generated GDScript is version-stamped and parse-gated** (Obj 5).

### (b) CORE (minimal, high-confidence) vs. SPECULATIVE (blocked-on-MCP)

**CORE — build now; env-independent; clears every objection:**

- **C1. Godot `CLAUDE.md`/`AGENTS.md` generator.** Emits the always-on declarative layer
  from doc 04 §1 (architecture seams, invariants, non-negotiables, exact headless commands,
  the GDScript-4.x traps). Highest leverage per unit cost; the author's project lacks one entirely.
  Captures most of Objection 1's value in a single skill.
- **C2. Godot architecture scaffolder.** Generates original GDScript for the load-bearing
  seams (RngSet, ModifierResolver, Models/Entities split, intent/logic executor, atomic
  save + migration chain, test seams) — techniques 1–7 as files, not prose. Net-new; pure
  text generation; ends with a `--check-only` parse gate. The one skill that front-loads
  the structural decisions everything else depends on.
- **C3. GDScript-4.x idiom guard / spec lens.** A pinned, version-stamped reference the
  agent loads before writing GDScript (Callable signals, const-vs-static-var, no hand-edit
  tscn/uid, typed everywhere) **plus** a Godot non-goals lens that plugs into the existing
  spec authoring / adversarial spec review (contribution-record-not-special-case; doesn't touch the wrong
  `.tscn`). Directly answers Objection 5; composes rather than forks (Objection 4).

**SPECULATIVE — defer until a one-time env probe is green (godot binary + a chosen MCP
respond on the author's machine/version):**

- **S1. Headless test + self-play gate** (GUT runner + AutoSlay-style watchdog/memory
  loop, techniques 6+10). Real value, but blocked on the unverified headless `godot`
  assumption.
- **S2. Live scene-tree inspector** (needs a runtime MCP).
- **S3. Run-and-verify / screenshot / input-simulation** for the game window (needs a
  runtime MCP; the existing UI-QA suite is web-only and does not transfer).
- **S4. Observability/dev-console scaffolder** — borderline; the *scaffold* is CORE-like
  text generation, but its payoff (driving a live game into a state) is MCP-gated.

**Explicitly REJECTED (sprawl/duplication):** Godot-flavored spec, plan, TDD, debug,
asset-gen, op-hardening, or cross-validation skills — all already covered generically;
inject Godot-ness via C1+C3 instead.

### (c) Refined hypothesis

> The leverage is **not** a broad "gold-standard suite." It is a **small Godot-specific
> knowledge-injection + scaffolding layer (≈3 skills) on top of the author's existing generic
> workflow**, plus a **separately-gated runtime-verification tier that ships only after a
> Godot MCP/headless bridge is proven in his environment.** The first-order win is the
> generated CLAUDE.md + architecture scaffolder + idiom guard; the runtime tier is real but
> conditional, not foundational.

---

## Verdict

**REFINED — not killed, not confirmed as stated.** The "high-leverage set of skills" exists
but is far smaller and more sharply bounded than "gold standard" implies. Most of the
methodology's collaboration patterns are already operationalized by the author's 23 skills or
belong in a context file; the genuine net-new surface is ~3 env-independent skills plus a
deferred, MCP-gated runtime tier.

- **Core vs speculative split:** CORE = {C1 CLAUDE.md generator, C2 architecture
  scaffolder, C3 GDScript-4.x idiom/spec-lens}; SPECULATIVE/blocked-on-MCP = {S1 headless
  test+self-play gate, S2 scene-tree inspector, S3 run/screenshot/input-verify, S4
  dev-console+observability}. REJECT all Godot re-skins of existing generic skills.

- **Assumption candidates (promote into the PLAN registry):**
  1. _Most methodology value is declarative → belongs in CLAUDE.md, not skills._ (Obj 1)
  2. _The binding constraint is human design/taste/scope, not tooling._ (Obj 3) — if true,
     down-weight the entire suite.
  3. _A Godot MCP responds in the author's env against his Godot 4.x version._ (Obj 2) — gates the
     entire speculative tier; currently UNVERIFIED (`godot` not on PATH).
  4. _Headless `godot` is invocable in the author's env._ (Obj 2/5) — gates S1 and every
     parse/verify gate; currently UNVERIFIED.
  5. _Scaffolder-generated GDScript parse-checks clean on the current Godot version._
     (Obj 5) — if it can't be gated, C2 risks being a net-negative error factory.
