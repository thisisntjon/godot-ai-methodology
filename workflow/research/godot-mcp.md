# Godot MCP & Runtime Automation

_Date: 2026-06-28_

Angle: map the Godot MCP (Model Context Protocol) + runtime/editor automation
landscape, because the highest-value AI-assistant skills for Godot (live
scene-tree inspection, run-the-game verify, self-play smoke testing, visual
verify) depend on the engine being drivable and observable by an external
agent. This document retires the load-bearing assumption that "no usable Godot
MCP / runtime-automation path exists."

All claims date-stamped to releases/activity visible 2026-06-28 unless noted.

---

## 1. Existing Godot MCP servers

The ecosystem is crowded as of mid-2026 — 10+ servers exist. They split into
two generations: **editor-authoring** servers (drive the editor to build
scenes/scripts) and **runtime** servers (inspect and drive the *running game*).
The runtime generation is what unlocks the high-value verify/self-play skills.

### Editor-authoring / general (first generation)

- **Coding-Solo/godot-mcp** — https://github.com/Coding-Solo/godot-mcp
  - The de-facto reference, ~4.5k stars (largest by far), MIT.
  - Exposes: launch editor, run project in debug mode, stop, **capture debug
    output/console+errors**, create scenes, add nodes, load sprites, export
    MeshLibrary, project info, Godot version, UID management (4.4+).
  - Implementation: **external Node.js MCP server** + one comprehensive
    `godot_operations.gd` driven via `--headless --script` with JSON params
    (avoids temp-file-per-op). ~60% JS / ~40% GDScript. No EditorPlugin.
  - Gaps: **no live scene-tree read, no input driving, no screenshots.** Good
    for "build the project" but not "watch it run."
  - Maturity: high adoption, 8 contributors, ~60 commits; the template most
    forks descend from.

- **IvanMurzak/Godot-MCP** — https://github.com/IvanMurzak/Godot-MCP
  - ~138 stars, Apache-2.0, latest v0.14.0 (June 2026). Godot 4.3+ / .NET 8.
  - Implementation: **C# `[Tool]` EditorPlugin** — installs a main-thread
    dispatcher, a ReflectorNet reflector with Godot type converters, and a
    SignalR connection to an MCP server. Backend is either hosted
    **ai-game.dev** (Cloud, default) or self-hosted GameDev-MCP-Server (engine-
    agnostic; shared with a Unity-MCP). Notable for cross-engine architecture.
  - 39 tools / 11 families: node/scene/resource/filesystem/script CRUD (.cs and
    .gd), **screenshots (viewport/camera/isolated-node → PNG)**, editor state,
    console logs, **reflection-based method calling**, runtime-error capture.
  - Runtime: opt-in `GodotMcpRuntime.Initialize(...)` exposes live state;
    runtime-error capture (GDScript/C# exceptions, shader errors, multi-frame
    backtraces) on Godot 4.5+. C#-centric.

- **mkdevkit/godot-mcp**, **bradypp/godot-mcp**, **LeeSinLiang/godot-mcp**,
  **Raunaksplanet/godot-mcp-server** — additional open-source editor-control
  servers (Godot 4.x, Claude Code / Cursor / VS Code clients). Smaller, similar
  authoring feature sets; differ mainly in client packaging and tool breadth.
  Treat as alternates to Coding-Solo, not capability leaders.

### Runtime / self-play generation (the load-bearing ones)

- **tugcantopaloglu/godot-mcp** — https://github.com/tugcantopaloglu/godot-mcp
  - ~298 stars, 48 forks, MIT, **v2.0.0 (2026-03-02)**, 390 Vitest tests.
  - **149 tools.** This is the most complete runtime story found:
    - Run project + capture output, stop, get debug output.
    - **Read/modify scene trees; full node introspection; property/method
      access; signal management; instantiate scenes at runtime.**
    - **Input simulation: mouse, keyboard, gamepad, touch.** ← self-play.
    - **Screenshots (base64 PNG); performance metrics; error logs.**
    - **Execute arbitrary GDScript in the running game with return values.**
  - Implementation: **two-channel.** (1) headless CLI via `--headless --script`
    for non-running ops; (2) an **autoload `mcp_interaction_server.gd` listening
    on a TCP socket (port 9090)** that takes JSON commands *during gameplay* —
    this is the bridge that makes live inspection + input driving work.
    TypeScript MCP server + GDScript.

- **Erodenn/godot-mcp-runtime** — https://github.com/Erodenn/godot-mcp-runtime
  - ~40 stars, Apache-style, **19 releases, v3.1.2 (May 2026)**, 0 open issues.
  - Explicitly the "watch it run" server. Capabilities:
    - Headless editing (create scenes/nodes, set props, attach scripts, connect
      signals, **validate GDScript**) — no editor needed.
    - **Runtime control via an auto-injected autoload bridge**: screenshots
      (viewport, multiple formats), **input simulation (keyboard/mouse/UI
      clicks/Godot actions)**, **live scene-tree inspection incl. Control-node
      data (UI discovery)**, live GDScript execution against the running scene.
    - **Background mode**: run off-screen with "physical input blocked" for
      automated/CI self-play testing. **Manual-attach** mode: launch Godot
      yourself, let MCP manage the bridge.
  - Implementation: **TypeScript (~86%) + GDScript (~10%)**; bridge
    **auto-injects as an autoload, "zero footprint"** (no addon install / no
    project edits). Built with Claude Code, atop prior Godot-MCP work.

- **youichi-uda/godot-mcp-pro** — https://github.com/youichi-uda/godot-mcp-pro
  - Commercial ($15 one-time), 160+ tools: scene/animation/3D/physics/particles/
    audio/shader, **input simulation, runtime analysis, testing**. Closed but
    confirms the runtime feature direction is productized.

- **Commercial / itch.io**: **GDAI MCP** (gdaimcp.com), **Beckett MCP**
  (beckettlabs.itch.io), **PurpleJelly godot-mcp** (purplejelly.itch.io),
  **hi-godot/godot-ai** (120+ ops / 41 tools, Snap install, free). All
  editor-integration focused; several advertise screenshots + run + state query.

### Takeaway

The capabilities the gold-standard skills need — **run + read logs, live
scene-tree, input driving, screenshots** — already exist together in
**tugcantopaloglu/godot-mcp** and **Erodenn/godot-mcp-runtime** today (both
shipped releases in 2026), and partially in IvanMurzak. The pattern they
converge on is identical and reproducible: **headless CLI for static ops + an
autoload TCP/socket bridge for live runtime control.**

---

## 2. Godot's own automation primitives (build-on-able, no MCP required)

Everything the MCP servers do is built on first-class engine features. A skill
can use these directly even with no MCP installed:

- **`--headless`** — run without a window/GPU (CI, servers). Combine with
  `--script` for batch jobs. Source: Godot command-line tutorial.
- **`-s, --script <file.gd>`** — run a standalone `.gd` that inherits
  `SceneTree`/`MainLoop`, no editor. The basis of "do X to the project" ops
  (asset conversion, scene edits, validation). Official-supported.
- **Run a project / scene directly** — `godot` or `godot scene.tscn`.
- **`--quit`, `--quit-after <frames>`** — deterministic exit for CI / one-shot
  smoke runs (e.g. boot, render N frames, screenshot, quit).
- **`-d`** — command-line debugger for game or single scene.
- **`--remote-debug <uri>`** (e.g. `tcp://127.0.0.1:6007`) — the running game
  connects out to a remote-debug endpoint. This is the same channel the editor's
  remote debugger / **EditorDebugger** uses; it carries the live remote
  **scene tree**, remote inspector, profiler, and `print`/error streams. An
  external listener can speak this protocol to observe a running game.
- **`EngineDebugger`** (singleton) + **`EditorDebuggerPlugin`** /
  capture-message API — register custom debugger messages so the running game
  and an external/editor-side listener exchange arbitrary data. This is the
  *sanctioned* path for a custom live-inspection bridge.
- **Editor side**: `EditorPlugin` + `EditorInterface` (open scenes, inspect
  edited scene tree, trigger play, read editor state) for an in-editor addon.
- **Log capture**: `print`/`push_error`/`push_warning` go to stdout/stderr (so
  a parent process running the CLI can read them directly) and over the
  remote-debug channel; `--log-file` (4.x) can persist them.
- **Screenshots without any MCP**: in-game,
  `get_viewport().get_texture().get_image().save_png(path)` captures the frame;
  pair with `--quit-after` for headed runs. (Headless has no rendered viewport,
  so visual verify needs a headed/offscreen GPU context.)
- **Input injection without MCP**: `Input.parse_input_event(...)` and
  `Input.action_press/release(...)` drive actions/keys/mouse from script —
  the engine primitive every "input simulation" tool wraps.
- **Testing frameworks**: **GUT** and **GdUnit4** already run headless from CLI
  for unit/integration tests (`gut.readthedocs.io`), a complement to self-play.

**Net:** an AI assistant can do a surprising amount with *zero* custom MCP —
just spawn the Godot binary with `--headless`/`--script`/`--quit-after`, read
stdout/stderr, and have a tiny injected autoload save PNGs and inject input.
The MCP servers mainly package this into a clean tool surface + a persistent
live socket so inspection/input work *continuously* during a play session
rather than one-shot.

---

## 3. Feasibility verdict (per capability)

| Capability | Rating | Why |
|---|---|---|
| (a) Run project + read output/logs | **Available now** | Spawn `godot --headless` / run project from Bash; stdout/stderr is captured directly. Multiple MCPs (Coding-Solo, tugcantopaloglu, Erodenn) already expose run+capture. Trivial even without MCP. |
| (b) Inspect a running scene tree | **Available now (via MCP) / feasible-to-build** | tugcantopaloglu + Erodenn expose live scene-tree + node introspection today via autoload TCP bridge. Engine basis: remote-debug protocol / `EngineDebugger` / a custom autoload. Buildable in a day as a small GDScript autoload + socket. |
| (c) Drive inputs for self-play | **Available now (via MCP) / feasible-to-build** | tugcantopaloglu (mouse/kbd/gamepad/touch) and Erodenn (kbd/mouse/UI/actions, incl. background off-screen mode) ship it. Engine basis: `Input.parse_input_event` / `Input.action_press`. The main work is *determinism* (fixed timestep, seeded RNG), not access. |
| (d) Screenshot for visual verify | **Available now (headed) / mild caveat headless** | `get_viewport().get_texture().get_image().save_png()` works in a headed/offscreen-GPU run; IvanMurzak/tugcantopaloglu/Erodenn return PNG/base64. Caveat: pure `--headless` has no rendered frame, so visual verify needs a real or virtual GPU (Xvfb/offscreen). On this Windows dev box, headed runs are fine. |

No capability is **hard**. The only genuine frictions are operational, not
existential: (i) headless-vs-visual GPU requirement for screenshots; (ii)
making self-play *deterministic* for reliable smoke tests; (iii) the live
bridge must be injected/enabled (autoload), though Erodenn shows "zero-footprint"
auto-injection is achievable; (iv) version churn — these MCPs target Godot
4.3/4.4/4.5 and move fast.

---

## Verdict on the load-bearing assumption

**"A usable Godot MCP / runtime-automation path exists or is feasible" — HOLDS.**

- It HOLDS strongly for run+logs and (with an autoload bridge) live scene-tree,
  input self-play, and screenshots. Two actively-released 2026 open-source MCPs
  (tugcantopaloglu v2.0.0 Mar-2026; Erodenn v3.1.2 May-2026) already deliver the
  full set; the underlying engine primitives are all first-class and documented.
- The realistic build target for the skill set is **not** "invent automation"
  but "adopt or fork a runtime MCP (Erodenn's zero-footprint autoload pattern is
  the cleanest), pin a Godot version, and add determinism + visual-diff glue."
- Only soft caveat: **visual verify wants a GPU context** (headless alone won't
  render), and **self-play reliability depends on determinism**, not tooling.

So the highest-value skills (live inspection, run-the-game verify, self-play
smoke testing, visual verify) are **all on the table.**

### Assumption candidates surfaced (to test next)

1. **Determinism is achievable enough** for self-play smoke tests to be stable
   (fixed timestep + seeded RNG + input scripting) — *unproven, test it.*
2. **A single Godot version can be pinned** across the skill set without
   constant breakage given fast 4.x churn — *risk.*
3. **Screenshot/visual verify has a working GPU path** on target environments
   (dev box headed = yes; CI/headless needs offscreen/Xvfb) — *env-dependent.*
4. **An external-process + autoload-bridge architecture** (vs. C# EditorPlugin)
   is the right default for a GDScript-first project — *design choice to lock.*
5. **Forking/adopting an existing MCP beats writing one** — likely true; the
   convergent architecture is well-trodden.
6. **The remote-debug/EngineDebugger protocol is stable enough** to target
   directly if a custom bridge is preferred over an existing MCP — *verify.*

---

## Sources

- Godot MCP servers (GitHub): Coding-Solo/godot-mcp; tugcantopaloglu/godot-mcp;
  Erodenn/godot-mcp-runtime; IvanMurzak/Godot-MCP; mkdevkit, bradypp,
  LeeSinLiang, Raunaksplanet variants; youichi-uda/godot-mcp-pro;
  hi-godot/godot-ai.
- https://github.com/Coding-Solo/godot-mcp
- https://github.com/tugcantopaloglu/godot-mcp
- https://github.com/Erodenn/godot-mcp-runtime
- https://github.com/IvanMurzak/Godot-MCP
- https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- https://docs.godotengine.org/en/stable/tutorials/scripting/debug/overview_of_debugging_tools.html
- https://gut.readthedocs.io/en/latest/Command-Line.html
- https://aceade.net/2025/07/17/godot-how-to-use-remote-debugger/
- Commercial/itch listings: gdaimcp.com; beckettlabs.itch.io; purplejelly.itch.io
