class_name ActionExecutor
extends RefCounted
## Drains a queue of GameActions in order — the seam between player input and game logic.

var _queue: Array[GameAction] = []

func enqueue(a: GameAction) -> void:
	_queue.append(a)

func run_all() -> int:
	var n := 0
	while not _queue.is_empty():
		var a: GameAction = _queue.pop_front()
		a.execute()
		n += 1
	return n
