extends SceneTree
# Project-load gate (Godot 4.x). Injected into a project as __gate__.gd and run with:
#   <godot> --headless --path <proj> -s res://__gate__.gd
# Loads every res://*.gd through the resource loader (resolving class_name / preload /
# cross-file refs), so it catches project-level resolution failures that a per-file
# --check-only would miss. Exits 0 iff every script loads.

func _initialize() -> void:
	var failures := 0
	var checked := 0
	for p in _scan("res://"):
		if p.ends_with("__gate__.gd"):
			continue
		checked += 1
		var res: Resource = load(p)
		var ok := res != null
		# load() can return a non-null GDScript object even when it failed to compile,
		# so force a recompile and check the result code — this is what makes the gate
		# catch cross-file resolution failures, not just missing files.
		if res is GDScript:
			ok = (res as GDScript).reload() == OK
		if ok:
			print("GATE-OK ", p)
		else:
			push_error("GATE-FAIL load: " + p)
			failures += 1
	print("GATE-SUMMARY checked=%d failures=%d" % [checked, failures])
	quit(0 if failures == 0 else 1)

func _scan(root: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(root)
	if d == null:
		return out
	d.list_dir_begin()
	var f := d.get_next()
	while f != "":
		if f == "." or f == "..":
			f = d.get_next()
			continue
		var full := root.path_join(f)
		if d.current_is_dir():
			if f == ".godot" or f == ".import":
				f = d.get_next()
				continue
			out.append_array(_scan(full))
		elif f.ends_with(".gd"):
			out.append(full)
		f = d.get_next()
	d.list_dir_end()
	return out
