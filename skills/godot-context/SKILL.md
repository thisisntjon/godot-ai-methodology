---
name: godot-context
description: >-
  Generate or refresh a Godot project's CLAUDE.md / AGENTS.md so AI coding assistants stop
  re-deriving the architecture every session. Use when starting AI-assisted work on a Godot
  project that has no context file, when the engine version / autoloads / commands have drifted,
  or when the user says "make a CLAUDE.md for this Godot project", "set up the context file",
  "the assistant keeps forgetting the architecture", or "/godot-context". Discovers the Godot
  binary + version, reads project.godot, and emits a context file seeded with the
  AI-leverageable architecture rules (determinism, data-driven content, modifier composition,
  intent/logic seam, test seams) for you to curate.
disable-model-invocation: true
argument-hint: <project_dir> [--force]
---

# godot-context

**The failure this prevents:** an AI assistant opening a Godot project cold — re-deriving the
architecture, guessing the engine version, assuming `godot` is on PATH, reaching for Godot-3
APIs, and quietly breaking determinism — because the project has no single context file. The
generated **`CLAUDE.md` is the project's source of truth**; a fresh session reads it first.

## Steps

1. **Locate the project** — the directory containing `project.godot` (ask if ambiguous).
2. **Generate the scaffold** — run the helper (zero-dep, stdlib only):
   ```bash
   python <skill-dir>/generate_context.py <project_dir>
   ```
   (`<skill-dir>` = this skill's folder: `skills/godot-context/` in the repo, or `~/.claude/skills/godot-context/` once installed.)
   It discovers the binary (`$GODOT_BIN` → PATH → Steam path), records the real engine
   version, parses name / config version / language (GDScript vs C#) / autoloads, and writes
   `CLAUDE.md`. It **refuses to overwrite** an existing file (use `--force`, or `--stdout` to
   preview and merge by hand).
3. **Curate the TODO sections** — the script cannot infer game design. Fill in: each autoload's
   responsibility, the deterministic update order, naming/dir conventions, and save/migration
   rules. Pull architecture language from the methodology docs (`../../00-principles.md`,
   `../../04-ai-collaboration-patterns.md`).
4. **Verify it's true** — the recorded binary + commands must actually run. Confirm with
   `"$GODOT_BIN" --headless --version` (or the discovered path) and a headless `--import`.

## Rules

- **Discover, never assume `godot`.** Always resolve `$GODOT_BIN` → PATH → the Steam path; the
  binary is frequently not on PATH (and the version is whatever is installed — stay 4.x-agnostic).
- **No-overwrite by default.** Never clobber a curated context file; regenerate facts and merge.
- **Compose, don't duplicate.** This is the Godot *context* layer; it feeds — not replaces —
  `spec`, `plan`, TDD, `code-review`. It pairs with `godot-guard` (idiom/non-goals lens) and
  `godot-scaffold` (which writes the substrate this file documents).
- **Language-aware.** If the project is C# (GodotSharp), the rules section adapts; the default
  and recommended target is GDScript.

## Files

- `generate_context.py` — the generator (discovery + parse + emit). Source of truth for the
  CLAUDE.md skeleton lives inside it.
- `reference.md` — what each context-file section is for, and why it earns its place.

<!-- Drift fuse (re-verify by 2026-12 or on misfire): the Steam fallback path + the
     GDScript-4.x rule list in generate_context.py track the installed engine (4.7 as of
     2026-06-28). Update both if the engine moves. Helper is stdlib-only, no deps. -->
