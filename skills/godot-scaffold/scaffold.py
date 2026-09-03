#!/usr/bin/env python3
"""godot-scaffold — emit the AI-leverageable GDScript substrate into a Godot project, then
prove it with the project-load gate.

Substrate (original GDScript 4.x): seeded per-concern RNG, Model/Entity split,
modifier-resolution pipeline (additive/multiplicative/cap), intent-vs-logic action queue,
atomic save + versioned migration. After copying, runs a project-load gate that recompiles
every script (catches cross-file failures). No-overwrite by default.

Usage:
  python scaffold.py <project_dir> [--dir scripts/core] [--force] [--no-gate]
Env:
  GODOT_BIN  overrides binary discovery
Exit: 0 ok (and gate passed, unless --no-gate) · 1 gate failed · 2 usage/no project.godot · 3 no binary
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")
GATE_SRC = os.path.join(HERE, "gate.gd")
STEAM = r"C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"


def discover_binary():
    b = os.environ.get("GODOT_BIN")
    if b and os.path.exists(b):
        return b
    for n in ("godot", "godot4", "Godot", "godot.exe"):
        p = shutil.which(n)
        if p:
            return p
    if os.path.exists(STEAM):
        return STEAM
    return None


def run(binary, proj, *args, timeout=180):
    return subprocess.run([binary, "--headless", "--path", proj, *args],
                          capture_output=True, text=True, timeout=timeout)


def emit(proj, subdir, force):
    dst_dir = os.path.join(proj, *subdir.split("/"))
    os.makedirs(dst_dir, exist_ok=True)
    written, skipped = [], []
    for fn in sorted(os.listdir(TEMPLATES)):
        if not fn.endswith(".gd"):
            continue
        dst = os.path.join(dst_dir, fn)
        if os.path.exists(dst) and not force:
            skipped.append(fn)
            continue
        shutil.copyfile(os.path.join(TEMPLATES, fn), dst)
        written.append(fn)
    return written, skipped, dst_dir


def gate(binary, proj):
    dst = os.path.join(proj, "__gate__.gd")
    if os.path.exists(dst):
        return 2, "gate refused: __gate__.gd already exists"
    shutil.copyfile(GATE_SRC, dst)
    markers = ("SCRIPT ERROR", "Parse Error", "Failed to load script", "GATE-FAIL")
    try:
        import_out = ""
        try:
            imp = run(binary, proj, "--import", timeout=240)
            import_out = (imp.stdout or "") + (imp.stderr or "")
        except subprocess.TimeoutExpired:
            import_out = "(import timed out)"
        res = run(binary, proj, "-s", "res://__gate__.gd", timeout=180)
        combined = import_out + (res.stdout or "") + (res.stderr or "")
        hit = next((m for m in markers if m in combined), None)
        failed = res.returncode != 0 or hit is not None
        summary = next((ln for ln in combined.splitlines() if "GATE-SUMMARY" in ln), "")
        return (1 if failed else 0), "%s (marker=%s, exit=%d)" % (summary, hit, res.returncode)
    finally:
        try:
            os.remove(dst)
        except OSError:
            pass


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--dir", default="scripts/core")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-gate", action="store_true")
    args = ap.parse_args(argv[1:])

    proj = os.path.abspath(args.project_dir)
    if not os.path.isfile(os.path.join(proj, "project.godot")):
        print("godot-scaffold: no project.godot in %s" % proj)
        return 2

    written, skipped, dst_dir = emit(proj, args.dir, args.force)
    print("godot-scaffold: wrote %d file(s) to %s" % (len(written), dst_dir))
    for f in written:
        print("  + " + f)
    if skipped:
        print("  (skipped existing, use --force: %s)" % ", ".join(skipped))

    if args.no_gate:
        return 0
    binary = discover_binary()
    if not binary:
        print("godot-scaffold: no Godot binary found (set GODOT_BIN) — skipping gate")
        return 3
    print("godot-scaffold: gating with %s" % binary)
    code, info = gate(binary, proj)
    print("godot-scaffold: GATE %s — %s" % ("PASS" if code == 0 else "FAIL", info))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
