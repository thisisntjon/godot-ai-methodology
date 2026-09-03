class_name SaveMigration
extends RefCounted
## Versioned save migration. Bump current_version() and add a step each time the save
## schema changes, so old saves load forward instead of breaking.

static func current_version() -> int:
	return 1

static func migrate(data: Dictionary) -> Dictionary:
	var v := int(data.get("version", 0))
	# while v < current_version():
	#     data = _step(v, data)
	#     v += 1
	data["version"] = current_version()
	return data
