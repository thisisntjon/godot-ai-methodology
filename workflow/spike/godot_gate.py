#!/usr/bin/env python3
"""Project-load gate for Godot GDScript projects (parse-gate spike for godot-scaffold / godot-test).

Discovers a Godot binary, imports the project (builds the global class cache), then loads
every res://*.gd through the resource loader and exits non-zero if any script fails to
compile/resolve. This is a *project-load* gate (catches cross-file class_name/preload
failures), not just per-file syntax.

Usage:  python godot_gate.py <project_dir>
Env:    GODOT_BIN  (overrides discovery)
Exit:   0 = all scripts load · 1 = >=1 load failure · 2 = usage · 3 = no binary
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE_SRC = os.path.join(HERE, "gate.gd")
STEAM = r"C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"


def discover_binary():
    b = os.environ.get("GODOT_BIN")
    if b and os.path.exists(b):
        return b
    for name in ("godot", "godot4", "Godot", "godot.exe"):
        p = shutil.which(name)
        if p:
            return p
    if os.path.exists(STEAM):
        return STEAM
    return None


def run(binary, proj, *args, timeout=180):
    cmd = [binary, "--headless", "--path", proj, *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def main(argv):
    if len(argv) < 2:
        print("usage: godot_gate.py <project_dir>")
        return 2
    proj = os.path.abspath(argv[1])
    if not os.path.isfile(os.path.join(proj, "project.godot")):
        print("GATE: no project.godot in %s" % proj)
        return 2
    binary = discover_binary()
    if not binary:
        print("GATE: no Godot binary found (set GODOT_BIN)")
        return 3
    print("GATE: using %s" % binary)

    # Inject the gate script (no-overwrite: refuse if a stray copy exists).
    dst = os.path.join(proj, "__gate__.gd")
    if os.path.exists(dst):
        print("GATE: refusing to overwrite existing __gate__.gd")
        return 2
    shutil.copyfile(GATE_SRC, dst)
    # Markers that mean a script failed to compile/resolve, regardless of exit code.
    err_markers = ("SCRIPT ERROR", "Parse Error", "Failed to load script", "GATE-FAIL")
    try:
        # 1) Import to build the global class cache. Capture its output too: script
        #    compile errors surface here even when the exit code is 0.
        import_out = ""
        try:
            imp = run(binary, proj, "--import", timeout=240)
            import_out = (imp.stdout or "") + (imp.stderr or "")
        except subprocess.TimeoutExpired:
            print("GATE: --import timed out (continuing to load gate)")
        # 2) Load-gate.
        res = run(binary, proj, "-s", "res://__gate__.gd", timeout=180)
        sys.stdout.write(res.stdout)
        if res.stderr:
            sys.stderr.write(res.stderr)
        combined = import_out + (res.stdout or "") + (res.stderr or "")
        marker_hit = next((m for m in err_markers if m in combined), None)
        failed = res.returncode != 0 or marker_hit is not None
        print("GATE: exit=%d marker=%s -> %s"
              % (res.returncode, marker_hit, "FAIL" if failed else "PASS"))
        return 1 if failed else 0
    finally:
        try:
            os.remove(dst)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
