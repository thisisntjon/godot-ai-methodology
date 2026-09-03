# Godot AI Methodology

A second-domain application of one thesis: deterministic, observable, testable, modular, data-driven, documented codebases are easier for AI coding systems to modify safely and to verify. Grounded in a read-only study of Slay the Spire 2 (StS2), a shipped Godot game.

**Status:** PUBLIC methodology; the skills run offline.

**Research question:** What software architecture makes AI-assisted development safer and more verifiable?

**Sourcing and ethics**

- No decompilation. The encrypted `.pck` was never opened.
- No extracted proprietary assets.
- No copied source.
- Observations are based on shipped documentation and manifests, quoted in `STS2_EVIDENCE.md`.
- Generated examples are original GDScript 4.x.

**Verify** (from the repo root; `<proj>` holds a `project.godot`; observed 2026-09-02):

| Command | Observed tail |
| --- | --- |
| `python skills/godot-context/generate_context.py <proj>` | `godot-context: wrote <proj>/CLAUDE.md (engine=4.7.2.stable.steam.ed1daf0bf, language=GDScript, autoloads=0)` |
| `python skills/godot-scaffold/scaffold.py <proj>` | `godot-scaffold: GATE PASS ... GATE-SUMMARY checked=9 failures=0 (marker=None, exit=0)` |
| `python skills/godot-guard/guard_check.py <proj>` | `godot-guard: 9 file(s) scanned, 0 findings ... clean.` |
| `python workflow/spike/godot_gate.py <proj>` | `GATE: exit=0 marker=None -> PASS` |

**Limitations:** one studied game; author-run, not independently reproduced; scaffold and gate need a Godot binary, and only Windows/Steam binary discovery is documented (`$GODOT_BIN`, PATH, Steam path).

**Deeper documentation**

- [00 Principles](00-principles.md): eight principles, StS2-grounded.
- [01 Phased Workflow](01-phased-workflow.md): the per-feature loop, with prompt templates.
- [02 Project Roadmap](02-project-roadmap.md): zero-to-ship phases.
- [03 Techniques](03-techniques.md): ten patterns with runnable GDScript.
- [04 AI Collaboration Patterns](04-ai-collaboration-patterns.md): driving the agent.
- [05 Checklists](05-checklists.md): gates to run when the agent says done.
- [06 Skill Suite](06-skills.md): three built skills, one specced tier.
- [STS2_EVIDENCE.md](STS2_EVIDENCE.md): the evidence pack.
- [references.md](references.md): sourced tool facts.

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

## Part of the Simone Systems Research program

SEED measures whether agent-driven work constitutes verified progress. BigBoss controls which autonomous actions can occur and preserves human decision authority. The Council tests independent verification through heterogeneous model families. The Bus shows adversarial review terminating a bad architecture before further implementation. Godot Methodology tests whether the same verification principles generalize into software architecture.

[seed-protocol](https://github.com/thisisntjon/seed-protocol) · [thecouncil](https://github.com/thisisntjon/thecouncil) · [bigboss-approval-plane](https://github.com/thisisntjon/bigboss-approval-plane) · [thebus](https://github.com/thisisntjon/thebus) · [simoneresearch.com](https://simoneresearch.com)

Simone Systems Research is founder-led and independent (Jonathan Simone, jon@simoneresearch.com). Principles: Evidence before promotion; Independent verification; Compute must earn its cost; Negative results are retained; Artifacts matter.
