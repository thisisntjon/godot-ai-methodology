class_name Model
extends RefCounted
## Definition (data), instantiated rarely. Subclass for cards/enemies/items. Keep models
## free of runtime state — mutable state lives on Entity. Add content as data, not branches.

var id: StringName

func _init(model_id: StringName = &"") -> void:
	id = model_id
