# Gold-Standard AI Skills for Godot Game Dev — Plan (living document)

> This is the investigation log that produced the doc set, kept as provenance. Dated phases refer to the author's private session history.

Format: a phased-investigation workflow. Triage depth: **Deep** — architectural, novel, and expensive to get wrong; the goal is a force-multiplier toolkit, so a wide fan-out + adversarial prioritization is warranted.
Current stage: done (CORE built, verified, and promoted to ~/.claude/skills)
Last updated: 2026-06-28

> **Home:** This is the effort's source of truth. Findings live in `workflow/research/`;
> built skills under `skills/` (and/or `~/.claude/skills/` once promoted). Builds directly
> on the StS2 case study (the author's unpublished StS2 study notes) and the methodology
> doc set in the parent folder (`..\00-principles.md` … `references.md`, `STS2_EVIDENCE.md`).

## Problem

**Problem:** General-purpose AI coding assistants are not optimized for Godot game
development. We now have the *knowledge* (the StS2-grounded methodology doc set), but it is
inert prose — not yet **operationalized as executable skills** an assistant can invoke. The
friction remains: Godot scenes/resources are merge- and edit-hostile to AI; verification
requires running the game; testing requires GUT/headless wiring; content is data-driven and
easy to special-case wrong; there is no turnkey way to scaffold the AI-leverageable
architecture, run a self-play smoke test, or inspect a live scene tree.

**Why now:** Findings are fresh and concrete (StS2 evidence pack + 8-doc methodology just
completed), and the author actively builds Godot games with AI assistants and feels the friction
daily. Converting methodology → skills turns a one-time study into a compounding capability.

**Original hypothesis (the author, lightly paraphrased):** "What would be the gold-standard set of skills for AI
coding assistants for creating a game in Godot based on our findings" — i.e. *there exists a
definable, high-leverage set of skills (skills + subagents + MCP) that, grounded in our
findings, would materially improve AI-assisted Godot development.*

## Goal

Produce (1) a **prioritized blueprint** of the gold-standard Godot-dev AI skill suite — each
entry naming its form (Claude Code skill / subagent type / MCP tool-server), trigger,
inputs/outputs, the finding/StS2 trait it operationalizes, and its dependencies — and then
(2) **author the top 1–3 highest-leverage skills** as real, working Claude Code skills that
follow the author's existing skill conventions and demonstrably function. Reusable, project-agnostic,
GDScript-focused, within the legal/ethical boundary (no StS2 code or assets — techniques only).

## Success criteria (checkable)

1. A blueprint catalog exists (in `research/friction-to-skill.md` + `SYNTHESIS.md`, consolidated by this `## Phasing`) listing each candidate skill with: name, form (skill/subagent/MCP), trigger, inputs/outputs, the methodology doc + StS2 trait it operationalizes, and dependencies. *(Produced by Phases 1–2.)*
2. Each catalog entry is traceable to a specific finding (a `STS2_EVIDENCE.md` trait and/or a methodology doc section) — no skill proposed without grounding. *(Phases 1–2.)*
3. Overlap with the author's **22** existing skills is explicitly resolved (each proposal is either net-new or a justified Godot-specific specialization, not a silent duplicate). *(Phases 1–2; see `existing-skills.md` + `stress-test.md`.)*
4. The skills to build are selected with written rationale scoring leverage × feasibility incl. environment constraints. *(Phase 2.)*
5. Each built skill is a valid Claude Code skill (conforming `SKILL.md` per house conventions), is **locally activated and demonstrated** in its build phase, and meets its **per-skill acceptance bar**:
   - **C1 `godot-context`** — emitted context file contains all required sections (architecture, deterministic update order, GDScript-4.x rules, non-negotiables, discovered binary + commands) AND the binary/commands it records actually run.
   - **C2 `godot-scaffold`** — the scaffolded substrate passes the **project-load gate** (exit 0; a deliberately-broken variant exits non-zero), proving cross-file GDScript loads, not just per-file syntax.
   - **C3 `godot-guard`** — flags the seeded GDScript defects (Godot-3 drift, determinism leak, `const`/`static var` trap, etc.) with **zero false positives** on a clean sample, and is shown being consulted by a host review step (code review / adversarial spec review).
6. Boundary respected: all skill code/templates are **original GDScript for Godot 4.x**; spot-check confirms no block reproduces StS2 identifiers/structure (StS2 ships no source — only XML doc text — so the risk is paraphrase-to-code, checked by inspection). *(All build phases.)*
7. The gated runtime tier is specced to a **spec-completeness checklist** (each skill: name · trigger · inputs/outputs · step sequence · acceptance test · failure-it-prevents) with an explicit **testable gate condition** (MCP installed AND `--headless` probe green). `godot-test` specced deeply; S2–S4 as thin stubs to avoid spec-rot. *(Phase 7.)*

## Assumption registry

<!-- Update the moment evidence arrives — during execution, not at evaluation.
     A flipped load-bearing assumption = stop and run pivot-check.md. -->

- Assumption: A definable, high-leverage "gold-standard" skill set exists that materially improves AI-assisted Godot dev (vs. the docs being sufficient on their own).
  Source: the author's hypothesis
  Status: **REFINED (2026-06-28, SYNTHESIS.md)** — yes, but it is a small *curated core* (3 Godot-specific knowledge-injection + scaffolding skills layered on the existing generic workflow) + a *gated runtime tier* (4 skills), NOT a broad suite. Convergent across existing-skills, stress-test, prior-art.
  | Affects: all phases

- Assumption: Claude Code skills + custom subagents + MCP are the right delivery vehicles.
  Source: the author's choice (this session)
  Status: holding — strengthened (prior-art: subagents for review isolation; MCP confirmed mature). NOTE: **deferred, not retired** — all 3 CORE skills are plain skills; subagents/MCP appear only in the Phase 7 runtime-tier *spec*, so this vehicle remains unproven by this effort's builds.
  | Affects: Phase 2 (form selection), Phase 7 (runtime-tier spec)

- Assumption: A usable Godot **MCP / runtime-automation** path exists (or is feasible to build) for live scene-tree inspection, running the project, reading logs, and driving inputs.
  Source: prior research → re-verified (godot-mcp.md)
  Status: **VERIFIED at ecosystem level (2026)** — Erodenn/godot-mcp-runtime, tugcantopaloglu/godot-mcp v2 (149 tools), Godot MCP Pro; all capabilities available/buildable. **BUT unverified in the author's env** (not installed/wired) → gates the runtime tier.
  | Affects: runtime-tier skills (godot-test / godot-smoke / godot-inspect / godot-observe)

- Assumption: The `godot` binary is invocable **headlessly** in the author's environment.
  Source: env-probe.md → **VERIFIED (Phase 3, 2026-06-28)**
  Status: **VERIFIED** — binary is **Godot 4.7.stable.steam** at `C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`; **NOT on PATH** → skills must discover (`$GODOT_BIN`→PATH→Steam path). `godot_gate.py` runs it headless and distinguishes clean (exit 0) vs broken (exit 1).
  | Affects: godot-test / godot-smoke / scaffolder parse-gate / CI skills

- Assumption: GDScript-focused, project-agnostic, reusable scope.
  Source: the author's choice
  Status: holding (deliberate target) — NOTE (env-probe): the only on-disk Godot project (a C# project) is **C# / 4.3**; the GDScript project is docs-only. GDScript stays the chosen target; skills should be language-aware.
  | Affects: all built skills

- Assumption: **GUT is NOT installed** in the author's env → a test skill must scaffold/install GUT, not assume it.
  Source: env-probe.md
  Status: verified (2026-06-28)
  | Affects: godot-test

- Assumption: Most methodology value is **declarative** → belongs in a project `CLAUDE.md`/`AGENTS.md`; the Godot work currently has none.
  Source: stress-test.md + env-probe.md
  Status: holding (drives C1 as highest cheap leverage)
  | Affects: Phase 4 (C1 `godot-context`)

- Assumption: A scaffolder must end in a **project-load check gate** or it risks emitting broken GDScript (net-negative).
  Source: stress-test.md → **VERIFIED FEASIBLE (Phase 3, 2026-06-28)** — `godot_gate.py`/`gate.gd` work. **Key finding:** bare `load()` gives false negatives (returns non-null for a broken script); the gate MUST use `GDScript.reload() == OK` + output-marker scan after an `--import` pass. Per-file `--check-only` is insufficient.
  Status: verified feasible (design constraint on C2 + S1)
  | Affects: C2 `godot-scaffold`, S1 `godot-test` (Phase 7 spec)

## Phasing

*(Vertical slices, risk-ordered. Phase 1 (investigation) is done; Phase 2 (this roadmap)
closes at the roadmap gate. Build phases 3–7 follow — the scariest build assumption
(scaffolder must emit GDScript that actually parse-checks via the discovered headless binary)
is retired FIRST. Scope this effort: build CORE 3 now, spec the runtime tier for later.)*

**Cross-phase build constraints (apply to every built skill):**
- Author under `godot-ai-methodology/skills/<name>/SKILL.md` (canonical source). **Local activation per build phase** for its demo (copy into a discovery path — a project `.claude/skills/` or `~/.claude/skills/`); **permanent promotion in Phase 8**. Use **copy, not symlink** (Windows symlinks need admin/Dev-Mode); note source→promoted drift.
- Follow house SKILL.md conventions (see `research/existing-skills.md`): frontmatter `name` + long trigger-laden `description` (+ `disable-model-invocation`, `argument-hint`); router body; progressive disclosure (`templates/`, `reference.md`, zero-dep `*.py` helpers by absolute path); name ONE source-of-truth; state "the failure this skill prevents"; drift-fuse footer.
- Compose with — never duplicate — the existing generic workflow (spec authoring, adversarial spec review, planning, red-first TDD, code review, image generation, screen capture).
- Binary discovery everywhere: `$GODOT_BIN` → PATH → Steam path; never assume bare `godot`. Stay Godot-4.x-version-agnostic. GDScript target, but language-aware.
- Scaffolder/generators default to **no-overwrite / dry-run** (never clobber existing project files).

### Phase 1 — Investigate & catalog  [status: done]
6-agent Deep fan-out → 6 findings files + `SYNTHESIS.md`. **Done 2026-06-28.**
**Verified:** MCP feasibility (mature, gated on local install); headless `godot` (Steam path, not on PATH); GUT not installed. Hypothesis REFINED.

### Phase 2 — Roadmap & prioritize (adversarial)  [status: in progress]
Risk-ordered build roadmap + adversarial review (Deep triage) → gate.
**Produces:** this `## Phasing` + a passed adversarial review (SC 4).

### Phase 3 — Parse-gate spike + fixtures  [status: DONE 2026-06-28 — see `research/phase-3.md`]  ← load-bearing mechanism RETIRED
✓ Produces: `workflow/spike/{godot_gate.py,gate.gd,sample_clean,sample_broken,fixtures}` — gate distinguishes clean (exit 0) vs broken (exit 1). ✓ Verifies: headless-`godot`-discoverable (4.7) + project-load gate works (via `GDScript.reload()`, not bare `load()`).
Cheap throwaway: a zero-dep `*.py` helper does **binary discovery** (`$GODOT_BIN`→PATH→Steam path) and records the binary `--version`; then runs a **project-load gate** (open/import a tiny project / `load()` each emitted class — NOT just per-file `--check-only`) against (a) a deliberately-clean and (b) a deliberately-broken GDScript project, asserting exit codes/stderr differ. Also create the **throwaway GDScript 4.x sample project** + **seeded-bad GDScript fixtures** reused by Phases 4–6.
**Produces:** a proven `godot_gate.py` helper + sample project + fixtures; recorded binary version.
**Verifies:** headless-`godot`-discoverable + **project-load gate works** — the single load-bearing build mechanism. If this fails → `pivot-check.md`.

### Phase 4 — Build `godot-context` (C1)  [status: DONE 2026-06-28]
✓ Produces: `skills/godot-context/{SKILL.md,reference.md,generate_context.py}`. Demo'd on `sample_clean`: emits CLAUDE.md with all required sections, records real engine (`4.7.stable.steam`) + discovered binary, no-overwrite guard fires, recorded binary runs. ✓ Verifies: "most value is declarative → CLAUDE.md" (operationalized). Note: permanent promotion to `~/.claude/skills/` deferred to Phase 8 (avoid changing the live skill set mid-build).

### Phase 5 — Build `godot-scaffold` (C2)  [status: DONE 2026-06-28]
✓ Produces: `skills/godot-scaffold/{SKILL.md,reference.md,scaffold.py,gate.gd,templates/*.gd}` — 9-file substrate (RngStreams, Model/Entity, Modifier+ModifierResolver, GameAction+ActionExecutor, SaveMigration, SaveStore). Demo: scaffolded into a throwaway project → **GATE PASS (checked=9 failures=0)**; no-overwrite/idempotency verified. ✓ Verifies: scaffolder project-load gate + GDScript-validity (SC 5–6). All original GDScript 4.x.

### Phase 6 — Build `godot-guard` (C3)  [status: DONE 2026-06-28]
✓ Produces: `skills/godot-guard/{SKILL.md,reference.md,guard_check.py}`. Demo: bad fixtures → 5 findings (3 Godot-3 errors + 2 determinism warns); `good_sample` → 0; the 9 `godot-scaffold` templates → 0 false positives. Composition contract = `reference.md` lens that code review / adversarial spec review consult (`disable-model-invocation: false`). ✓ Verifies: composes-with-existing-skills (no duplication).

### Phase 7 — Spec the gated runtime tier (no build)  [status: DONE 2026-06-28 — `research/RUNTIME-TIER-SPEC.md`]
✓ `godot-test` specced deeply (name/trigger/IO/steps/acceptance/failure); S2 `godot-smoke`, S3 `godot-inspect`+`godot-verify`, S4 `godot-observe` as stubs; explicit gate condition (headless ✅ / GUT ❌ scaffold / runtime-MCP ❌ enable) + one-time enablement. SC 7 met.
**`godot-test`** specced deeply (scaffold+run GUT headless via the Phase-3 gate); **S2 `godot-smoke` / S3 `godot-inspect`+`godot-verify` / S4 `godot-observe` as thin stubs** (avoid spec-rot before the bridge exists). Include the one-time runtime-enablement (install a Godot MCP — Erodenn zero-footprint pattern — + binary discovery + probe) and an explicit testable **gate condition** (MCP installed AND `--headless` probe green).
**Produces:** `workflow/research/RUNTIME-TIER-SPEC.md` meeting the SC-7 spec-completeness checklist.

### Phase 8 — Integrate & document  [status: DONE 2026-06-28, except promotion]
✓ Added `../06-skills.md` (suite overview, each skill → methodology doc + StS2 trait) + README TOC cross-link. ✓ Suite self-validates (`godot-guard` → 0 findings on `godot-scaffold` output). ⏳ **Permanent promotion** (`cp -r skills/godot-* ~/.claude/skills/`) deferred — awaiting user confirm (outward-facing change to the live skill set).

## Close-out

**Success-criteria scorecard:**
1. Blueprint catalog — ✅ `research/friction-to-skill.md` + `SYNTHESIS.md` (19 → 3 core + 4 gated).
2. Traceability — ✅ every skill cites a `STS2_EVIDENCE.md` trait + methodology doc (`06-skills.md`, each `reference.md`).
3. Overlap resolved (22 skills) — ✅ core composes with, doesn't duplicate, existing skills; web UI-QA family ruled out (DOM-only).
4. Top set selected w/ rationale — ✅ core-vs-gated split (`stress-test.md`, roadmap).
5. Built skills valid + demonstrated + per-skill bars — ✅ all 3 (context: sections+real binary; scaffold: GATE PASS 9/9; guard: flags fixtures, 0 false positives).
6. Boundary — ✅ all original GDScript 4.x; no StS2 code/assets (none exist to copy).
7. Runtime tier specced + gate condition — ✅ `research/RUNTIME-TIER-SPEC.md`.

**Registry final state:** gold-standard hypothesis **REFINED→delivered** (curated core + gated tier);
headless `godot` **VERIFIED** (4.7, discovery); project-load gate **VERIFIED** (reload()-based);
Godot MCP **VERIFIED feasible, not wired** (gates runtime tier); GUT **absent** (godot-test scaffolds it);
skills+subagents+MCP vehicle **deferred** (core are plain skills).

**What the process got right/wrong:** the adversarial roadmap review earned its keep — it caught
the "gate can be green while broken" risk, which the Phase-3 spike then confirmed empirically
(bare `load()` false-negative) before any skill depended on it. Mild over-cut: 8 phases for a
3-skill build; the spike+CORE could have been 4 phases. The env-probe correcting "The Old God is
a built project" → "docs-only; the real project is C#" prevented a wrong GDScript
assumption from going unexamined.

**Remaining:** (a) user-confirm promotion to `~/.claude/skills/`; (b) optional next effort — build
`godot-test` (S1, unblocked) then enable a Godot MCP for S2–S4.

## Phase log

- 2026-06-28 — Framing approved (Deep triage). Effort home set to `godot-ai-methodology/workflow/`. Entered investigation.
- 2026-06-28 — Phase 1 investigation complete: 6-agent fan-out → 6 findings files + `SYNTHESIS.md`. Hypothesis **REFINED** (curated core + gated runtime tier). Riskiest assumptions retired: Godot MCP = mature-but-gated-on-local-install; headless `godot` = available via discovery (Steam path, not on PATH); GUT not installed.
- 2026-06-28 — Synthesis gate APPROVED. Scope: build CORE 3 now, spec runtime tier. Entered roadmapping.
- 2026-06-28 — Adversarial roadmap review run + folded in: added Phase 3 **parse-gate spike** (retire the load-bearing mechanism before building C2); corrected gate to a **project-load** check (not per-file syntax); **restored synthesis build order** C1→C2→C3; per-phase **local activation** (copy, not symlink) so SC-5 is verifiable before Phase 8; sharpened SC-5/6/7 into per-skill bars + spec checklist; fixed stale registry wiring; noted the skills+subagents+MCP vehicle is **deferred, not retired**. 8 phases total (1–2 process, 3 spike, 4–6 build, 7 spec, 8 integrate).
- 2026-06-28 — Roadmap gate APPROVED ("build now"). Entered phase loop.
- 2026-06-28 — **Phase 3 DONE.** Built the parse-gate spike; binary = Godot 4.7.stable (Steam, not on PATH). Gate distinguishes clean (exit 0) / broken (exit 1). **Surprise/debt:** bare `load()` returns non-null for a broken script (false negative) — gate hardened to use `GDScript.reload()==OK` + output-marker scan after `--import`; this is now a binding design rule for C2 `godot-scaffold` and S1 `godot-test`.
- 2026-06-28 — **Phase 4 DONE.** Built `godot-context` (SKILL.md + reference.md + stdlib `generate_context.py`). Discovers binary/version, parses project.godot (name/version/language/autoloads), emits a CLAUDE.md with all required sections; no-overwrite guard. Fixed a Windows cp1252 stdout encoding bug (reconfigure to utf-8). Per-skill bar met.
- 2026-06-28 — **Phase 5 DONE.** Built `godot-scaffold` — emits a 9-file original-GDScript substrate (seeded RNG streams, Model/Entity, modifier-resolution pipeline, action-queue seam, atomic save + migration) and gates it. Scaffolded into a throwaway project → GATE PASS (9/9 load). Reuses the Phase-3 reload()-based gate.
- 2026-06-28 — **Phase 6 DONE.** Built `godot-guard` — static scanner (`guard_check.py`) + lens (`reference.md`) for Godot-3 drift, determinism leaks, const traps + architecture non-goals. Bad fixtures → 5 findings; clean substrate + good fixture → 0 false positives. Composes into the code-review / adversarial spec-review steps. **All 3 CORE skills (C1/C2/C3) built + verified.**
- 2026-06-28 — **Phases 7 & 8 DONE.** Wrote `RUNTIME-TIER-SPEC.md` (godot-test deep + S2–S4 stubs + gate). Added `06-skills.md` + README cross-link. Suite self-validates (guard → 0 on scaffold output).
- 2026-06-28 — **Promotion DONE + effort COMPLETE.** Copied godot-context / godot-scaffold / godot-guard into `~/.claude/skills/` (user-approved); installed copies smoke-tested (guard → 0 findings on scaffold templates). Canonical source remains in `skills/`; edit there and re-copy.

## Research

- `workflow/research/SYNTHESIS.md` — cross-angle synthesis + hypothesis verdict (2026-06-28)
- `workflow/research/existing-skills.md` — 22-skill inventory, SKILL.md house conventions, reuse/overlap *(environment-specific; not included in the public tree)*
- `workflow/research/godot-mcp.md` — Godot MCP / runtime-automation landscape (verdict: feasible, mature)
- `workflow/research/friction-to-skill.md` — 19-candidate seed catalog (frictions → skills)
- An environment probe (the author's Godot binary, GUT, ComfyUI, CI reality) also informed the plan; it is environment-specific and not included in the public tree.
- `workflow/research/prior-art.md` — agentic game-dev toolchains; transferable ideas
- `workflow/research/stress-test.md` — adversarial; core-vs-speculative split
- Reuse inputs: `..\STS2_EVIDENCE.md`, methodology docs `..\01/03/04`, `..\references.md`, the author's unpublished StS2 study notes (not in this repo).
