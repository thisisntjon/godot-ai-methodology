# FIXTURE (seeded-bad, for godot-guard / C3) — Godot 3.x idioms that must be flagged.
extends Node

export var speed = 100            # G3: should be @export var speed: float = 100.0

signal hit

func _ready():
	connect("hit", self, "_on_hit")   # G3 connect signature; G4: hit.connect(_on_hit)
	yield(get_tree().create_timer(1.0), "timeout")  # G3: yield; G4: await

func _on_hit():
	print("hit")
