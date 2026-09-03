# 06 — The Skill Suite (methodology, operationalized)

> The methodology docs are knowledge; these skills are that knowledge made executable.
> A small **curated core** an AI assistant invokes directly, plus a **gated runtime tier**
> specced for later. Built and verified 2026-06-28 against Godot **4.7.x**.

## Why a small set (not a big pack)

The investigation behind this (see `workflow/research/`) found that a general assistant
already owns the generic workflow (spec → plan → TDD → review). Re-skinning those for Godot
would be duplication, and large skill packs rot (documented "tool sprawl" failure). The genuine
Godot-specific leverage is **three knowledge-injection + scaffolding skills** layered on the
existing workflow, plus a runtime tier that's only worth building once the game can be driven
headlessly. So: 3 CORE skills now; 4 runtime skills specced and gated.

## CORE skills (built · `skills/`)

| Skill | What it does | Run | Grounding |
| --- | --- | --- | --- |
| **`godot-context`** | Generates/curates a project `CLAUDE.md` (engine version, discovered binary, autoloads, deterministic order, GDScript-4.x rules, non-negotiables) so the assistant stops re-deriving the architecture. | `python skills/godot-context/generate_context.py <proj>` | [00](00-principles.md) · [04](04-ai-collaboration-patterns.md) |
| **`godot-scaffold`** | Emits the AI-leverageable GDScript substrate (seeded RNG streams, Model/Entity, modifier-resolution pipeline, action-queue seam, atomic save + migration) and **gates** it with a project-load check. | `python skills/godot-scaffold/scaffold.py <proj>` | [00](00-principles.md) · [03](03-techniques.md) |
| **`godot-guard`** | The Godot-4.x correctness lens for review/spec: flags Godot-3 drift, determinism leaks, `const`-container traps, and architecture non-goals. Composes into your code-review / spec-critique step. | `python skills/godot-guard/guard_check.py <path…>` | [00](00-principles.md) · [03](03-techniques.md) · [04](04-ai-collaboration-patterns.md) |

**Verification (acceptance bars met):**
- `godot-context` → emits a CLAUDE.md with all required sections; records the *real* engine
  (4.7.x) + discovered binary; no-overwrite guard.
- `godot-scaffold` → scaffolds a 9-file substrate that passes the project-load gate
  (`checked=9 failures=0`); idempotent/no-overwrite.
- `godot-guard` → flags the seeded-bad fixtures (5 findings); **zero false positives** on the
  clean substrate + `good_sample`.

### The load-bearing lesson: the project-load gate
`godot-scaffold` and the future `godot-test` end in a **gate** that runs the discovered headless
binary, `--import`s the project, and calls `GDScript.reload()` on every script. This matters
because a per-file `--check-only` — and even a bare `load()` — can report success on a script
that fails to compile (a verified false negative). **`GATE PASS` is the definition of done for
any GDScript change.** (Helper: `skills/godot-scaffold/gate.gd` + `godot_gate.py`.)

## Gated runtime tier (specced · not built)

Full spec in `workflow/research/RUNTIME-TIER-SPEC.md`:
- **`godot-test`** (deep spec) — install/scaffold GUT, run headless, parse results. Needs only
  the headless binary (✅) + GUT (scaffolded). Buildable next.
- **`godot-smoke`** — self-play + watchdog + memory-delta leak check (StS2 `AutoSlayer`).
- **`godot-inspect` / `godot-verify`** — live scene-tree read + screenshot/input verify (pairs
  with a screen-capture tool).
- **`godot-observe`** — dev console + structured logging + build identity.

**Gate to build S2–S4:** a Godot runtime MCP installed and probed green in-env (the ecosystem
is mature — e.g. the Erodenn zero-footprint autoload pattern — just not yet wired locally).

## How these compose (not replace)

These are the Godot-specific layer on top of your own spec, plan, TDD, code-review, and
image-generation workflow: fold `godot-guard`'s non-goals into spec review, let your planning
workflow drive the work, let `godot-test` become the Godot executor for your TDD loop, have code
review consult the `godot-guard` lens, and pair asset generation and visual verification with the
tools you already use. Nothing here re-implements them.

## Activation

The skills live under `skills/` as the canonical source. To make them invocable in Claude
Code, **copy** (not symlink — Windows) each into `~/.claude/skills/`:
```bash
cp -r skills/godot-context skills/godot-scaffold skills/godot-guard ~/.claude/skills/
```
Note the source→installed drift: edit under `skills/` and re-copy. (`godot-guard` is
auto-invocable; `godot-context`/`godot-scaffold` are user-invoked.)
