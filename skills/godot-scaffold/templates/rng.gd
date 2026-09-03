class_name RngStreams
extends RefCounted
## Seeded, per-concern RNG. Gameplay randomness is reproducible from a seed; cosmetic
## randomness uses `chaotic` and is never saved (so it can't desync a reload).

var rewards := RandomNumberGenerator.new()
var shops := RandomNumberGenerator.new()
var transforms := RandomNumberGenerator.new()
var chaotic := RandomNumberGenerator.new() # cosmetic only — not persisted

# static var (not const) — typed containers with methods can't be parse-time const in GDScript.
static var _GAMEPLAY: Array[String] = ["rewards", "shops", "transforms"]

func _init(seed_value: int = 0) -> void:
	reseed(seed_value)

func reseed(seed_value: int) -> void:
	var i := 0
	for name in _GAMEPLAY:
		var s: RandomNumberGenerator = get(name)
		s.seed = seed_value + i
		i += 1
	chaotic.randomize()

func save_state() -> Dictionary:
	var out := {}
	for name in _GAMEPLAY:
		var s: RandomNumberGenerator = get(name)
		out[name] = {"seed": s.seed, "state": s.state}
	return out

func load_state(data: Dictionary) -> void:
	for name in _GAMEPLAY:
		if data.has(name):
			var s: RandomNumberGenerator = get(name)
			s.seed = int(data[name]["seed"])
			s.state = int(data[name]["state"])
