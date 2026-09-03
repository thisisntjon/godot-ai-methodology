# FIXTURE (seeded-bad, for godot-guard / C3) — determinism leaks in gameplay logic.
extends Node

func roll_reward() -> int:
	# LEAK: global RNG, not a seeded per-concern stream — unreproducible.
	return randi() % 6

func spawn_decision() -> bool:
	# LEAK: wall-clock drives gameplay -> not reproducible from a seed/save.
	return Time.get_ticks_msec() % 2 == 0
