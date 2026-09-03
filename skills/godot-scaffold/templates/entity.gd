class_name Entity
extends RefCounted
## Runtime instance bound to a Model. Holds mutable state; reads its definition from `model`.

var model: Model
var props: Dictionary = {}

func _init(m: Model = null) -> void:
	model = m

func get_id() -> StringName:
	return model.id if model != null else &""
