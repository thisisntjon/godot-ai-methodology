# AI-Leverageable Game Architecture — A Methodology for Solo Godot Devs

> The front door to a doc set on building shippable Godot 4.x games with an AI
> coding assistant — grounded in a read-only study of Slay the Spire 2.

## Thesis

The traits that make a game **shippable** are the same traits that make it
**AI-leverageable**. Determinism, data-driven content, clean seams, composition
over special-casing, self-play smoke testing, and disciplined documentation are
not luxuries — they are the substrate that turns an LLM from a plausible-code
generator into a contributor whose changes you can actually verify. We learned
this by studying **Slay the Spire 2 (StS2)** read-only: a large, shipped Godot
game whose architecture, seen through its own published docs, reads like a
checklist for "how to make a codebase an agent can safely extend."

## How this was made — sourcing & ethics

StS2 was studied **only** through the artifacts it plainly ships: its C# XML
documentation (`sts2.xml`, ~99k lines, about 2,700 documented types) and loose JSON
manifests in `data_sts2_windows_x86_64/`. Every StS2 claim in this set quotes the
developers' own `<summary>` doc comments and is cited from the evidence pack at
`STS2_EVIDENCE.md`.

- **No decompilation.** The encrypted `.pck` (GDPC v3) was never extracted.
- **No asset extraction.** No sprites, audio, or scene data were pulled.
- **No copied code.** StS2 is C#/.NET 9 on Godot 4.5.1; there is no source to
  copy, only documentation summaries. We translate the *patterns* into idiomatic
  Godot 4.x GDScript. **Every code example in this set is original GDScript.**

This set is deliberately **project-agnostic and reusable** — adapt it to any
Godot 4.x game.

## Table of contents

| Doc | What it gives you |
| --- | --- |
| [00 — Principles](00-principles.md) | The conceptual backbone: the eight principles that make a codebase both shippable and AI-leverageable, each grounded in StS2 and translated to GDScript. |
| [01 — Phased Workflow](01-phased-workflow.md) | The per-feature loop with Claude Code: SPEC → PLAN → TESTS (RED) → IMPLEMENT (GREEN) → VERIFY → REVIEW → COMMIT, with copy-paste prompt templates. |
| [02 — Project Roadmap](02-project-roadmap.md) | A zero-to-ship phase template for a Godot game, where each phase's acceptance criteria double as the agent's definition of done. |
| [03 — Techniques](03-techniques.md) | The ten load-bearing patterns (seeded RNG, modifier resolver, intent/logic seam, self-play, save migrations…) with runnable GDScript. |
| [04 — AI Collaboration Patterns](04-ai-collaboration-patterns.md) | How to drive coding agents — context files, plan mode, subagents, small diffs, enforcing the RED phase, keeping the codebase AI-legible. |
| [05 — Checklists](05-checklists.md) | Copy-paste gates: per-feature, pre-commit, pre-release, an "is my codebase AI-friendly?" audit, and CI setup. Stop-signs you run when the agent says "done." |
| [06 — The Skill Suite](06-skills.md) | The methodology made executable: three built Claude Code skills (`godot-context`, `godot-scaffold`, `godot-guard`) + a specced gated runtime tier, with how to run and activate them. |
| [references.md](references.md) | Sourced tool facts: GUT vs gdUnit4, headless/CI commands, Godot MCP, SDD/TDD methodology, ComfyUI asset generation. |

## How to use this set

**Newcomer (read in order).** Start with the *why*, then the *loop*, then the
*mechanics*:

1. [00 — Principles](00-principles.md) — orient on the core idea.
2. [01 — Phased Workflow](01-phased-workflow.md) — the loop you'll run daily.
3. [03 — Techniques](03-techniques.md) — the patterns the loop produces.
4. [04 — AI Collaboration Patterns](04-ai-collaboration-patterns.md) — how to
   drive the agent so the patterns survive contact.
5. [02 — Project Roadmap](02-project-roadmap.md) — sequence it into a real
   project, empty repo to release.
6. [05 — Checklists](05-checklists.md) + [references.md](references.md) — keep
   open as you work.

**Quick-reference user (jump straight in).** Keep
[05 — Checklists](05-checklists.md) open while the agent works and run the
matching block when it reports done. When you need a concrete pattern, go to
[03 — Techniques](03-techniques.md). When you need a tool name, command, or URL,
go to [references.md](references.md). Each doc cross-links its siblings, so you
can follow the thread from any entry point.

**Your assumed stack:** an advanced solo dev driving **Claude Code** (plan mode,
subagents, skills, hierarchical `CLAUDE.md` context), **GUT** for GDScript tests,
and **ComfyUI** for asset generation.

## The StS2 through-line

These are the StS2-validated patterns the set is built around — each is a
documented StS2 trait that doubles as an AI-assisted-dev lever. (Full quotes and
citations live in `STS2_EVIDENCE.md`.)

| StS2-validated pattern | Why it's an AI lever | Covered in |
| --- | --- | --- |
| **Seeded, segregated RNG** (`Rng`, `PlayerRngSet`, `Rng.Chaotic`, `MegaRandom`/Xoshiro256\*\*) | A run reproduces from a seed, so the agent can reproduce your bug; segregated streams keep behavioral diffs local; cosmetic chaos is quarantined. | [00](00-principles.md) §1, [03](03-techniques.md) §1, [02](02-project-roadmap.md) Phase 0 |
| **Data-driven Models vs Entities** (`CardModel`/`Cards` vs runtime `Creatures`/`Players`) | New content is a reviewable data row, not new control flow — low blast radius. | [00](00-principles.md), [03](03-techniques.md), [02](02-project-roadmap.md) |
| **Modifier-resolution pipeline** (`ModifyDamageHookType`: Additive → Multiplicative → Cap) | Effects compose automatically; no combinatorial special-casing for the agent to get wrong. | [03](03-techniques.md), [04](04-ai-collaboration-patterns.md) §2 non-goals |
| **Intent wraps logic** (`GameAction` wraps `Command`) | Clean seam for undo/replay/multiplayer; the agent edits logic without touching input plumbing. | [00](00-principles.md), [03](03-techniques.md), [04](04-ai-collaboration-patterns.md) |
| **Testability seams** (DI in `SaveManager`, `TestRngInjector`, headless `UiHelper.Click()`) | The agent writes deterministic tests against real systems without production coupling. | [03](03-techniques.md), [05](05-checklists.md), [references.md](references.md) |
| **Self-play smoke testing** (`AutoSlayer` + `Watchdog` + `MemoryProfiler`) | A machine-checkable "does a full run still work / leak?" gate the agent can run and read. | [03](03-techniques.md), [02](02-project-roadmap.md), [05](05-checklists.md) |
| **Disciplined saves** (atomic writes, `IMigration<T>`, best-effort cloud) | Schema evolves safely via a learnable migration pattern; optional infra never blocks. | [00](00-principles.md), [03](03-techniques.md), [02](02-project-roadmap.md) |
| **Observability** (DevConsole, structured logs, `ReleaseInfo`/Sentry) | You and the agent inspect live state and reproduce from build identity. | [03](03-techniques.md), [04](04-ai-collaboration-patterns.md) |
| **Exhaustive docs** (~36 lines of XML doc per type, consistent conventions) | The agent reads intent from comments and replicates mechanical patterns instead of guessing. | [00](00-principles.md), [04](04-ai-collaboration-patterns.md) §context files |

---

*Full StS2 provenance for every claim lives in `STS2_EVIDENCE.md` (read-only observations; no decompilation).
StS2 © Mega Crit; studied here under fair, read-only inspection of shipped
documentation for the purpose of learning architecture, not reproducing it.*
