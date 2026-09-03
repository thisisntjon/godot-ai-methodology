# FIXTURE (clean, for godot-guard / C3) — idiomatic Godot 4.x; must produce ZERO findings.
class_name RewardRoller
extends RefCounted

signal rolled(value: int)

var _rng := RandomNumberGenerator.new()

func _init(seed_value: int) -> void:
	_rng.seed = seed_value

func roll() -> int:
	var v := _rng.randi_range(1, 6)
	rolled.emit(v)
	return v
