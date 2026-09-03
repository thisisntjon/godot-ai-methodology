class_name GameAction
extends RefCounted
## Player INTENT (play a card, end the turn). Wraps game logic; does not contain it.
## Subclass and override execute(). Keep the actual rules in systems/commands, not here —
## this seam is what makes undo / replay / multiplayer possible later.

func execute() -> void:
	pass
