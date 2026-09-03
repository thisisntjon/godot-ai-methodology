# Investigation Synthesis — Holy-Grail Godot AI Skills

_Date: 2026-06-28 · Triage: Deep · Angles: existing-skills, godot-mcp, friction-to-skill, env-probe, prior-art, stress-test_

## Hypothesis verdict: **REFINED** (not confirmed as stated, not killed)

A high-leverage skill set exists — but it is **far smaller and more sharply bounded** than
"gold-standard / broad suite" implies, and it splits cleanly into two tiers with different
readiness. Three angles (existing-skills, stress-test, prior-art) independently converged on
the same correction; env-probe and godot-mcp set the build constraints.

**Refined hypothesis:** The gold standard is **~3 Godot-specific *knowledge-injection +
scaffolding* skills layered on the author's existing generic workflow spine, plus a separately-gated
*runtime/verification* tier (GUT + self-play + live-inspect + visual-verify) that ships only
after a Godot MCP / headless bridge is installed and proven in-env.** It is a *curated core +
gated tier*, not a large catalog.

## Why smaller than expected — the convergent finding

1. **The generic workflow already exists.** the author owns 22 skills. The methodology's
   collaboration patterns map almost 1:1 onto shipped skills: EARS/spec/non-goals →
   spec authoring + an adversarial review step; plan/small-diffs → a phased-planning workflow;
   RED-TDD → a red-first TDD skill; seed-debugging → a root-cause debugging skill;
   cross-validation → a multi-model review step; **asset-gen → an image-generation helper** (already
   wraps the local server); op-hardening → an operational-hardening pass; final gate →
   `end-session-closeout`. **Re-skinning these for Godot would be silent duplication.**
   (The web UI-QA family is Playwright/Chrome/DOM-only and genuinely does *not* transfer to a
   Godot render target — only its orchestrator→specialists→evidence-gate *pattern* does.)
2. **Most methodology value is declarative**, so it belongs in a project `CLAUDE.md`/`AGENTS.md`,
   not in new skills. Cheapest, highest first-order leverage — and **not yet done** for the
   Godot work.
3. **Tool sprawl is a documented failure mode** (prior art: packs with 49 agents / 73 commands
   / 175 MCP tools blow context and rot). Right-sizing for a solo dev is the differentiator.

## What's genuinely net-new and worth building (the leverage)

From the 19-candidate seed catalog (`friction-to-skill.md`), filtered through overlap
(`existing-skills.md`) and the adversarial split (`stress-test.md`):

**CORE — env-independent, build now, clears every objection:**
- **C1 · `godot-context` (CLAUDE.md/AGENTS.md generator + curator).** Emits/maintains a Godot
  project context file encoding the AI-leverageable architecture, the update order, GDScript-4.x
  rules, and non-negotiables. Operationalizes `04` + `00`. Highest cheap leverage.
- **C2 · `godot-scaffold` (architecture initializer).** Generates original GDScript for the
  substrate: seeded/segregated RNG, modifier-resolution pipeline, Models↔Entities split,
  intent/logic (action-queue) seam, atomic save + versioned migration, test seams — ending in a
  **parse/`--headless --check`/import gate** so it can't emit broken code. Operationalizes `03`
  + the StS2 traits. (Front-runner build target.)
- **C3 · `godot-guard` (GDScript-4.x idiom + Godot non-goals lens).** Composes into existing
  spec authoring / adversarial spec review / code review to catch Godot-3 API drift (the #1 recurring AI failure per
  prior art), determinism leaks, `const`-vs-`static var` traps, node-path/signal fragility, and
  "don't special-case the modifier pipeline" non-goals. Operationalizes `00`/`03`/`04`.

**RUNTIME TIER — high value, GATED on a one-time in-env enablement (MCP/headless proven):**
- **S1 · `godot-test`** — install/scaffold GUT, run headless, parse results, gate on exit code.
- **S2 · `godot-smoke`** — self-play harness + watchdog (dump state on stall) + memory-delta
  leak check (AutoSlay-style).
- **S3 · `godot-inspect` / `godot-verify`** — live scene-tree read, run-the-game, screenshot +
  drive-input visual verification (pairs with an existing screen-capture helper).
- **S4 · `godot-observe`** — dev-console / structured-logging / build-identity scaffolder.

**REJECT:** Godot re-skins of the generic spec / plan / TDD / debug / image-generation / operational-hardening skills. Inject
"Godot-ness" via C1+C3 instead.

## Assumption movement (evidence in)

| Assumption | Was | Now |
| --- | --- | --- |
| Gold-standard set exists | unverified | **REFINED** — small core + gated tier, not a suite |
| Skills+subagents+MCP are right vehicles | holding | **holding/strengthened** — subagents for isolation (prior art), MCP confirmed |
| Usable Godot MCP / runtime-automation exists/feasible | unverified | **VERIFIED at ecosystem level** (mature 2026: Erodenn/godot-mcp-runtime, tugcantopaloglu/godot-mcp v2, Godot MCP Pro) — **but UNVERIFIED in the author's env**; gates the runtime tier |
| Headless `godot` invocable in-env | unverified | **HOLDS** — only the Steam binary `C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`, **not on PATH** → skills must discover (`$GODOT_BIN`→PATH→Steam path) |
| GDScript-focused, project-agnostic | holding | **holding (deliberate target)** — note: the only on-disk Godot project (a C# project) is **C# / 4.3**; the GDScript project is docs-only. GDScript remains the chosen target; skills should be language-aware |

**New assumptions surfaced (added to registry):**
- **GUT is NOT installed** anywhere → `godot-test` must *scaffold* GUT, never assume it.
- **Most value is declarative** → a `CLAUDE.md` generator (C1) is the highest cheap leverage; the Godot work currently has no context file.
- **Scaffolder must end in a parse gate** or C2 risks being a net-negative "error factory."
- **CI is green-field** (empty `.git`, no remotes) → GitHub Actions is deferred/optional.
- **Version drift** (project 4.3 vs editor ~4.7) → skills must be 4.x-version-agnostic / discover the version.
- **Curate MCP tool surface** (servers expose 149–175 tools) → expose a minimal subset.

## Conflicts found & resolved

- *godot-mcp ("mature, available") vs env-probe/stress-test ("not wired locally").* **Not a real
  conflict:** the capability exists in the ecosystem and is installable; it is simply not yet
  installed/verified on the author's machine. **Resolution:** runtime tier is *feasible* (assumption
  holds) but *gated* on a one-time local install + green probe before those skills are trusted.
- *friction-to-skill (19 skills) vs stress-test (mostly overlap/declarative).* **Resolution:**
  the 19 are a superset; after overlap-pruning and the core/gated split they collapse to **3
  core + 4 gated**. The catalog stays as the audit trail; the blueprint uses the pruned set.

## Recommended build order (preview for roadmap stage)

1. **C1 `godot-context`** (cheapest, unblocks everything, env-independent).
2. **C2 `godot-scaffold`** with a parse gate (the marquee "turn findings into substrate" skill).
3. **C3 `godot-guard`** (composes into existing review/spec skills).
4. *Gate:* one-time **runtime enablement** — install a Godot MCP (Erodenn zero-footprint pattern)
   + binary discovery + `--headless` probe; only then build **S1 `godot-test`** → **S2/S3/S4**.

This retires the two riskiest assumptions early (MCP feasibility = yes-but-gated; headless godot
= yes-via-discovery) and front-loads the env-independent, highest-confidence value.

## Findings files
- `existing-skills.md` · `godot-mcp.md` · `friction-to-skill.md` · `env-probe.md` · `prior-art.md` · `stress-test.md`
