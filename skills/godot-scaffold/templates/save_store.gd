class_name SaveStore
extends RefCounted
## Atomic JSON save: write a temp file, then rename it over the real file (rename is atomic
## on the same filesystem), so a crash mid-write never corrupts the save. Reads run
## migrations. Any cloud sync layered on top must be best-effort and never block local saves.

var path: String

func _init(save_path: String = "user://save.json") -> void:
	path = save_path

func save(data: Dictionary) -> Error:
	data["version"] = SaveMigration.current_version()
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return FileAccess.get_open_error()
	f.store_string(JSON.stringify(data))
	f.close()
	var d := DirAccess.open(path.get_base_dir())
	if d == null:
		return ERR_CANT_OPEN
	return d.rename(tmp.get_file(), path.get_file())

func load_data() -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var text := f.get_as_text()
	f.close()
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return SaveMigration.migrate(parsed)
