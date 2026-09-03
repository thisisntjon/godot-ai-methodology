#!/usr/bin/env python3
"""godot-guard — static lens for GDScript 4.x idiom drift, determinism leaks, and known traps.

The automated half of the godot-guard lens (the judgment half lives in reference.md, which
code-review / adversarial spec review consult). Scans .gd files line-by-line and reports findings as
file:line. Designed for ZERO false positives on idiomatic Godot-4.x code.

Usage:  python guard_check.py <path> [<path> ...]      # files or dirs (recurses)
Exit:   0 = clean · 1 = findings · 2 = nothing scanned
"""
import os
import re
import sys

# (id, severity, compiled-regex, message)  — regexes run against code with comments stripped.
CHECKS = [
    ("G3-export-var", "error", re.compile(r"(?<!@)\bexport\s+var\b"),
     "Godot-3 'export var' -> use '@export var name: Type'"),
    ("G3-export-paren", "error", re.compile(r"(?<!@)\bexport\s*\("),
     "Godot-3 'export(Type)' -> use '@export'"),
    ("G3-onready", "error", re.compile(r"(?<!@)\bonready\s+var\b"),
     "Godot-3 'onready var' -> use '@onready var'"),
    ("G3-yield", "error", re.compile(r"\byield\s*\("),
     "Godot-3 'yield(...)' -> use 'await'"),
    ("G3-setget", "error", re.compile(r"\bsetget\b"),
     "Godot-3 'setget' -> use property setter/getter functions or @export with set/get"),
    ("G3-connect-str", "error", re.compile(r"\bconnect\s*\(\s*[\"']"),
     "Godot-3 connect(\"sig\", obj, \"method\") -> use 'sig.connect(callable)'"),
    ("DET-global-rng", "warn", re.compile(r"(?<![\w.])(randi|randf|randi_range|randf_range|randomize)\s*\("),
     "Determinism leak: global RNG. Use a seeded RandomNumberGenerator stream per concern."),
    ("DET-walltime", "warn", re.compile(r"\b(Time\.get_ticks_msec|Time\.get_ticks_usec|OS\.get_ticks_msec)\s*\("),
     "Determinism leak: wall-clock in logic. Drive gameplay from ticks/seed, not real time."),
    ("TRAP-const-container", "warn",
     re.compile(r"\bconst\s+\w+\s*:?=?\s*.*\b(PackedStringArray|PackedByteArray|PackedInt32Array|PackedFloat32Array)\s*\("),
     "const typed-container trap -> use 'static var' (parse-time const can't build these)."),
    ("TRAP-const-typed-coll", "warn",
     re.compile(r"\bconst\s+\w+\s*:\s*(Array|Dictionary)\b"),
     "const typed Array/Dictionary that needs methods -> prefer 'static var'."),
]


def strip_comment(line):
    # Heuristic: drop from the first '#' not inside a quote. Good enough for a linter; at
    # worst it under-scans a line, never invents a finding.
    in_s = False
    q = ""
    for i, ch in enumerate(line):
        if in_s:
            if ch == q:
                in_s = False
        elif ch in "\"'":
            in_s = True
            q = ch
        elif ch == "#":
            return line[:i]
    return line


def scan_file(path):
    findings = []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return findings
    for n, raw in enumerate(text.splitlines(), 1):
        code = strip_comment(raw)
        if not code.strip():
            continue
        for cid, sev, rx, msg in CHECKS:
            if rx.search(code):
                findings.append((path, n, sev, cid, msg, raw.strip()))
    return findings


def gather(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                if any(seg in root for seg in (os.sep + ".godot", os.sep + ".import")):
                    continue
                for nm in names:
                    if nm.endswith(".gd"):
                        files.append(os.path.join(root, nm))
        elif p.endswith(".gd") and os.path.isfile(p):
            files.append(p)
    return files


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if len(argv) < 2:
        print("usage: guard_check.py <path> [<path> ...]")
        return 2
    files = gather(argv[1:])
    if not files:
        print("godot-guard: no .gd files found")
        return 2
    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f))
    if not all_findings:
        print("godot-guard: %d file(s) scanned, 0 findings — clean." % len(files))
        return 0
    for path, n, sev, cid, msg, src in all_findings:
        print("%s:%d [%s/%s] %s\n    %s" % (path, n, sev, cid, msg, src))
    errs = sum(1 for x in all_findings if x[2] == "error")
    warns = len(all_findings) - errs
    print("godot-guard: %d finding(s) across %d file(s) — %d error, %d warn."
          % (len(all_findings), len(files), errs, warns))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
