extends SceneTree
# Project-load gate (Godot 4.x). Injected as __gate__.gd and run headless:
#   <godot> --headless --path <proj> -s res://__gate__.gd
# Loads every res://*.gd through the resource loader and recompiles each GDScript via
# reload() — load() alone returns non-null for a broken script (false negative), so the
# reload() check is what makes the gate catch cross-file class_name/preload failures.

func _initialize() -> void:
	var failures := 0
	var checked := 0
	for p in _scan("res://"):
		if p.ends_with("__gate__.gd"):
			continue
		checked += 1
		var res: Resource = load(p)
		var ok := res != null
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
			if f == ".godot" or f == ".import" or f == "addons":
				f = d.get_next()
				continue
			out.append_array(_scan(full))
		elif f.ends_with(".gd"):
			out.append(full)
		f = d.get_next()
	d.list_dir_end()
	return out
