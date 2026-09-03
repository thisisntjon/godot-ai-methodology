---
name: godot-guard
description: >-
  The Godot-4.x correctness lens for AI-written GDScript: catches Godot-3 API drift (export var,
  yield, old connect(), setget), determinism leaks (global randi()/wall-clock in gameplay), the
  const-typed-container trap, and "don't special-case the modifier pipeline" non-goals. Use it
  as a Godot add-on to code review and spec authoring — invoke when reviewing or generating
  GDScript, when code-review / adversarial spec review run on a Godot project, or when the user says
  "check this Godot code", "review the GDScript", "is this Godot 4 correct", or "/godot-guard".
  Composes with code-review and adversarial spec review (they consult its lens); it does not replace them.
disable-model-invocation: false
argument-hint: <path> [<path> ...]
---

# godot-guard

**The failure this prevents:** an assistant writing plausible-but-wrong GDScript — Godot-3 APIs
the model defaults to, randomness that can't be reproduced, the `const` container trap, or
helpful special-casing that erodes the modifier pipeline — slipping through a generic review
that doesn't know Godot. This skill is the **Godot lens** that generic review/spec skills lack.

## How it composes (it does not duplicate code-review / spec review)

- **At review time:** when `code-review` runs on a Godot project, also apply this lens — read
  `reference.md` and run the automated scan over the changed `.gd` files.
- **At spec time:** when `spec` / an adversarial spec-review step author criteria for a Godot feature, fold in the
  **non-goals** from `reference.md` (e.g. "do NOT special-case effect combinations").
- **Standalone:** run the scan directly on files/dirs.

## Steps

1. **Run the automated scan** (zero-dep, stdlib):
   ```bash
   python <skill-dir>/guard_check.py <path...>
   ```
   (`<skill-dir>` = this skill's folder: `skills/godot-guard/` in the repo, or `~/.claude/skills/godot-guard/` once installed.)
   `error` = Godot-3 drift (must fix); `warn` = determinism leak / trap (justify or fix). Exit 1
   if any findings. Designed for **zero false positives** on idiomatic Godot-4.x code.
2. **Apply the judgment lens** — read `reference.md` and check the things a regex can't: is
   randomness seeded per concern? are effects composed via the modifier pipeline rather than
   special-cased? is intent (actions) kept separate from logic? do saves use atomic writes +
   migrations?
3. **Report** findings the way the host skill (`code-review`) reports, with file:line + fix.

## Rules

- **Errors block; warns need a reason.** Godot-3 idioms are never acceptable in a 4.x project;
  determinism warns may be intentional (cosmetic randomness) but must be justified.
- **Compose, don't replace.** This adds Godot-specific signal to existing review/spec — it is
  not a second reviewer. Don't re-implement what `code-review` / the TDD workflow already do.
- **Stay version-agnostic** across Godot 4.x; the rules target the 4.x line, not one point release.

## Files

- `guard_check.py` — the automated scanner (Godot-3 drift, determinism leaks, const traps).
- `reference.md` — the full lens: rules + non-goals that `code-review` / adversarial spec review consult.

<!-- Drift fuse (re-verify by 2026-12 or on misfire): the CHECKS regexes in guard_check.py are
     tuned for zero false positives against the godot-scaffold substrate + good fixtures
     (verified 2026-06-28, engine 4.7). If Godot syntax shifts, update CHECKS and re-verify. -->
