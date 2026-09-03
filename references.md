# References & Further Reading

A sourced reference for AI-assisted Godot 4.x development. Every claim below
links to a credible primary source (official docs, project repositories, or
named author write-ups). Claims that could not be tied to a verifiable source
have been omitted. Organized by the six research areas, with a final
cross-reference to the Slay the Spire 2 study material.

---

## 1. Testing (GUT vs gdUnit4)

- **GUT (Godot Unit Test)** is a GDScript-only unit-test framework for Godot 4.x
  (current line: 9.x). Install by copying `addons/gut/` into the project, then
  enabling the plugin and restarting the editor.
  ([GUT GitHub](https://github.com/bitwes/Gut),
  [GUT docs](https://gut.readthedocs.io/))
- GUT tests extend the `GutTest` class; any method whose name starts with
  `test_` runs automatically. Lifecycle hooks are `before_all()`,
  `before_each()`, `after_each()`, and `after_all()`.
  ([GUT docs](https://gut.readthedocs.io/))
- GUT's assertion set includes `assert_eq`/`assert_ne`, `assert_gt`/`assert_lt`
  (and the `*_gte`/`*_lte` variants), `assert_true`/`assert_false`,
  `assert_null`/`assert_not_null`, `assert_between`, `assert_almost_eq` (floats),
  `assert_has`, `assert_string_contains`, and `assert_typeof`. Test doubles use
  `double()`, `stub()`, and `assert_called()`.
  ([GUT Asserts & Methods](https://gut.readthedocs.io/en/9.3.1/Asserts-and-Methods.html))
- GUT runs headlessly through `res://addons/gut/gut_cmdln.gd`; the runner's exit
  code reflects pass/fail and it can emit JUnit XML via `-goutput`. Typical
  invocation:
  ```bash
  godot --headless -s res://addons/gut/gut_cmdln.gd \
    -gdir=res://tests -ginclude_subdirs -gexit
  ```
  ([GUT GitHub](https://github.com/bitwes/Gut))
- **gdUnit4** supports both GDScript and C# (the C# path ships separately as
  **gdUnit4Net** with VSTest/Rider integration). Install by extracting
  `addons/gdUnit4/` and enabling the plugin.
  ([gdUnit4 GitHub](https://github.com/godot-gdunit-labs/gdUnit4),
  [gdUnit4Net](https://github.com/godot-gdunit-labs/gdUnit4Net))
- gdUnit4 uses fluent, type-specific assertions such as `assert_int()`,
  `assert_float()`, `assert_str()`, `assert_array()`, `assert_dict()`,
  `assert_vector()`, plus async `assert_signal()` — e.g.
  `assert_str("Hello").is_equal("Hello").has_length(5)`. It also offers a Scene
  Runner for simulating input.
  ([gdUnit4 assertions](https://godot-gdunit-labs.github.io/gdUnit4/latest/testing/assert/))
- gdUnit4 ships a CLI runner (`runtest.sh`) that generates HTML + JUnit XML
  reports automatically; documented exit codes are `0` (pass), `100`
  (failures), `101` (warnings). Flags include `-a`/`--add`, `-i`/`--ignore`,
  `-c`/`--continue`, and `-rd`/`--report-directory`.
  ([gdUnit4 CLI docs](https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/cmd/))
- Quick chooser: GUT for GDScript-only projects on Godot 4.0+; gdUnit4 when you
  need C# coverage, scene-input simulation, or built-in report generation
  (newer gdUnit4 releases target Godot 4.5+).
  ([gdUnit4 docs](https://godot-gdunit-labs.github.io/gdUnit4/latest/))

---

## 2. Headless / CI

- Godot's `--headless` flag disables GPU and audio drivers and is the baseline
  for any CI server. It composes with export and import commands.
  ([Godot command-line tutorial](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html))
- Export from the CLI with `--export-release <preset> <path>` or
  `--export-debug <preset> <path>` (debug implies `--import`). Preset names are
  case-sensitive and must match `export_presets.cfg`, and the target directory
  must already exist.
  ([Godot command-line tutorial](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html))
- Useful CI flags: `--import` (import resources then continue), `--quit`,
  `--quit-after <n>`, `-s`/`--script <path>` (script must inherit `SceneTree` or
  `MainLoop`), and `--check-only` (parse/error-check, used with `-s`).
  ([Godot 4.4 command-line tutorial](https://docs.godotengine.org/en/4.4/tutorials/editor/command_line_tutorial.html))
- **firebelley/godot-export** is a GitHub Action for automated exports. Required
  inputs include `godot_executable_download_url`,
  `godot_export_templates_download_url`, and `relative_project_path`; optional
  inputs include `cache`, `archive_output`, and `presets_to_export`.
  ([firebelley/godot-export](https://github.com/firebelley/godot-export))
- **gdUnit4-action** runs gdUnit4 tests in GitHub Actions. Key inputs:
  `godot-version`, `paths` (e.g. `res://tests`), `godot-net` (C#),
  `publish-report`, and `timeout`.
  ([gdUnit4-action](https://github.com/godot-gdunit-labs/gdUnit4-action))
- **abarichello/godot-ci** provides Docker images for Godot CI on GitHub Actions
  and GitLab CI; the `mono-*` tag variants include .NET/C# support
  (e.g. `barichello/godot-ci:mono-<ver>-stable`).
  ([abarichello/godot-ci](https://github.com/abarichello/godot-ci),
  [Docker Hub: barichello/godot-ci](https://hub.docker.com/r/barichello/godot-ci))
- Pre-heat the import cache before headless runs (e.g.
  `godot --headless --import`) and cache `.godot/` keyed on a hash of
  `project.godot` and source/scene files to avoid headless import failures.
  Commit `export_presets.cfg` to version control (do not `.gitignore` it).
  ([abarichello/godot-ci](https://github.com/abarichello/godot-ci),
  [helpmetest CI/CD guide](https://helpmetest.com/blog/godot-ci-cd-testing/))
- Browse the broader action ecosystem (setup, Android, Web/HTML5 exports) on the
  GitHub Marketplace.
  ([Godot CI actions on Marketplace](https://github.com/marketplace?category=ci&type=actions&query=godot))

---

## 3. Godot MCP & AI tooling

> The raw MCP briefing did not return verifiable facts, so this section is
> limited to sources whose existence can be confirmed directly.

- The **Model Context Protocol (MCP)** is an open protocol for connecting AI
  assistants to external tools and data sources; the specification and SDKs are
  published at the official site.
  ([Model Context Protocol](https://modelcontextprotocol.io/))
- **Coding-Solo/godot-mcp** is a community MCP server that lets MCP-capable AI
  clients drive the Godot editor and engine (e.g. launching the editor, running
  projects, and reading output). Verify capabilities against the repository
  before relying on any specific tool.
  ([Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp))
- Any MCP server's headless control surface ultimately bottoms out on Godot's
  documented CLI (`--headless`, `-s`, `--export-*`), so the command-line
  tutorial is the authoritative reference for what such a server can actually do.
  ([Godot command-line tutorial](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html))

---

## 4. AI-assisted dev methodology

- **Spec-driven development (SDD)** treats specifications as the primary
  artifact and code as regenerable output, pairing well with explicit
  acceptance criteria.
  ([Pluralsight: SDD with AI](https://www.pluralsight.com/resources/blog/software-development/spec-driven-development-with-AI-SDD),
  [Microsoft: Spec-driven development](https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering))
- **EARS notation** (Easy Approach to Requirements Syntax) gives a small set of
  sentence patterns for unambiguous, testable requirements and is commonly used
  to phrase SDD acceptance criteria.
  ([Pluralsight: SDD with AI](https://www.pluralsight.com/resources/blog/software-development/spec-driven-development-with-AI-SDD))
- A practical agent lifecycle moves spec -> clarify -> plan -> tasks ->
  implement -> validate, keeping the agent aimed at a defined target rather than
  drifting.
  ([Microsoft: Spec-driven development](https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering),
  [Augment Code: SDD for AI agents](https://www.augmentcode.com/guides/spec-driven-development-ai-agents-explained))
- **TDD with agents** must enforce the red phase explicitly: agents otherwise
  tend to delete failing tests or write tests that already pass. Confirm a test
  fails before letting the agent implement against it.
  ([Simon Willison: red/green TDD for agents](https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/),
  [Augment Code: spec + TDD](https://www.augmentcode.com/guides/spec-tdd-shippable-ai-generated-code))
- Specs and tests are complementary: specs define *what* and serve as the shared
  contract for multi-file generation; tests provide runtime proof it works.
  ([Augment Code: spec + TDD](https://www.augmentcode.com/guides/spec-tdd-shippable-ai-generated-code))
- **Persistent context**: Claude Code reads hierarchical `CLAUDE.md` memory
  files that cascade up the directory tree; keep each file concise to preserve
  token budget.
  ([Claude Code memory docs](https://code.claude.com/docs/en/memory))
- **Multi-model / worker-auditor review**: have one model generate and a second,
  independent model critique it, with a human gate on disagreement — the value
  comes from models challenging each other rather than agreeing.
  ([Bizzmark: multi-model auditor](https://bizzmarkblog.com/the-mechanics-of-shared-context-why-your-llm-thread-needs-a-multi-model-auditor/))
- Decompose work into small, reviewable diffs and back the workflow with
  evaluation pipelines and observability rather than ad-hoc prompting.
  ([DEV: AI-assisted development in 2026](https://dev.to/austinwdigital/ai-assisted-development-in-2026-best-practices-real-risks-and-the-new-bar-for-engineers-3fom),
  [arXiv: Spec-Driven Development](https://arxiv.org/html/2602.00180v1))

---

## 5. Godot AI friction & mitigations

> The raw friction briefing did not return verifiable facts, so this section is
> limited to claims grounded in official Godot documentation.

- Godot scenes (`.tscn`) and resources (`.tres`) use a human-readable text
  format. This makes them diffable and AI-editable, but the format has strict
  structural rules (sections, `ext_resource`/`sub_resource`, `load_steps`) that
  hand-edits can break — consult the format spec before generating them.
  ([TSCN file format](https://docs.godotengine.org/en/stable/engine_details/file_formats/tscn.html))
- Resource references in 4.x use stable **UIDs** (`uid://...`) alongside
  `res://` paths; UID bookkeeping lives in `.godot/` and `.uid` files, and the
  editor can regenerate/resave these. AI-generated resource links should prefer
  resaving through the editor (or `--import`) over hand-authored UIDs.
  ([Godot command-line tutorial](https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html))
- Prefer signals and clear interfaces over brittle absolute `NodePath`s: Godot's
  best-practices guidance favors accessing other nodes through exported
  references, groups, and signals rather than hard-coded tree paths, which also
  makes AI-generated wiring more robust to scene refactors.
  ([Godot interfaces best practices](https://docs.godotengine.org/en/stable/tutorials/best_practices/godot_interfaces.html))
- Mitigation pattern: keep logic in plain GDScript/C# that an agent can edit and
  unit-test (see Testing/CI above), and treat `.tscn`/`.import` artifacts as
  editor-owned outputs to be regenerated, not free-hand authored.
  ([TSCN file format](https://docs.godotengine.org/en/stable/engine_details/file_formats/tscn.html))

---

## 6. AI asset generation

- **ComfyUI** drives sprite/spritesheet pipelines via its HTTP API: submit
  JSON workflows to `POST /prompt`, poll `/history/{prompt_id}` for results, and
  free VRAM with `/free`.
  ([ComfyUI](https://comfy.org/),
  [ComfyUI workflows](https://comfy.org/workflows/))
- **Character consistency** is typically achieved by training a character
  **LoRA** on ~15-20 reference images (multiple angles/poses) and applying it
  across generations, separating identity (LoRA) from variation (prompt). Pose
  control via **OpenPose ControlNet** enforces skeletal accuracy.
  ([Thinkpeak: consistent-character LoRAs](https://thinkpeak.ai/best-loras-consistent-characters-2026/),
  [ComfyUI pose ControlNet tutorial](https://docs.comfy.org/tutorials/controlnet/pose-controlnet-2-pass))
- **Hugging Face Diffusers** is the core Python library for batched generation
  (`DiffusionPipeline.from_pretrained(...)`); **Replicate** offers managed
  Stable Diffusion hosting with async polling.
  ([Hugging Face Diffusers](https://github.com/huggingface/diffusers),
  [Replicate: Stable Diffusion](https://replicate.com/stability-ai/stable-diffusion))
- **GameAssetLab** is an MIT-licensed set of Jupyter notebooks demonstrating
  Dreambooth + Keras-CV fine-tuning for character datasets (auto-captioning via
  BLIP).
  ([GameAssetLab](https://github.com/soheil-mp/GameAssetLab))
- Academic technique for many character variations while preserving style:
  few-shot multi-token DreamBooth + LoRA.
  ([arXiv 2510.09475](https://arxiv.org/abs/2510.09475))
- Pixel-art-specific generators include **PixelLab** (directional sprite
  variants) and **Sprite AI** (game-exact sizes, sheet export).
  ([PixelLab](https://www.pixellab.ai/),
  [Sprite AI](https://sprite-ai.art/),
  [Best pixel-art generators 2026](https://www.sprite-ai.art/blog/best-pixel-art-generators-2026))
- Audio options span music (**Mubert**, **Stable Audio**, **Udio**) and SFX
  (**ElevenLabs Sound Effects**); a common setup pairs a music generator with a
  dedicated SFX generator.
  ([Mubert](https://mubert.com),
  [Stable Audio](https://stability.ai/stable-audio),
  [Udio API](https://udioapi.pro/),
  [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects))
- **Reality check**: studios generally use AI for drafts, bulk variation, and
  background/prop content while reserving hero assets for human artists, because
  AI output struggles with clean symmetry, mesh topology, strict style
  continuity, and engine/performance constraints — and carries training-data IP
  risk. Keep humans in the decision-making role.
  ([GIANTY: generative AI in asset production 2026](https://www.gianty.com/generative-ai-in-game-asset-production-in-2026/),
  [Starloop: how studios use AI 2026](https://starloopstudios.com/how-game-studios-use-ai-in-2026/))

---

## Slay the Spire 2 cross-reference

- The methodology doc set is grounded in an internal evidence pack:
  `STS2_EVIDENCE.md`, which collects verified, read-only observations
  used to teach techniques (not to copy code).
- **Slay the Spire 2 is studied strictly read-only from its plainly shipped C#
  XML documentation** (`sts2.xml`) and loose JSON manifests located under
  `data_sts2_windows_x86_64/`. **No decompilation and no `.pck` extraction** are
  performed; the `.pck` is encrypted (GDPC v3) and out of scope.
- Confirmed StS2 facts relevant to this reference: it runs on **Godot 4.5.1**
  using **C# / .NET 9** (not GDScript), so testing/CI guidance here favors the
  C#-capable paths (gdUnit4 / gdUnit4Net, `mono-*` CI images). See
  `STS2_EVIDENCE.md` for the full type taxonomy and packaging details.
- Treat StS2 as a *reference implementation for technique*, not a code source:
  all example code in the deliverable docs must be original GDScript/C#.
