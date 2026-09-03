class_name GateResolver
extends RefCounted

# BROKEN ON PURPOSE: GateModifier is referenced but modifier.gd does not exist in this
# project, so this script fails to resolve at project load.
static func resolve(base: float, mods: Array) -> float:
	var add := 0.0
	for m in mods:
		if m.kind == GateModifier.Kind.ADDITIVE:
			add += m.value
	return base + add
