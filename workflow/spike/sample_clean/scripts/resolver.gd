class_name GateResolver
extends RefCounted

# References GateModifier from another file — only resolves if the project-wide
# class cache is built (i.e. a project-load gate, not a per-file syntax check).
static func resolve(base: float, mods: Array) -> float:
	var add := 0.0
	var mul := 1.0
	for m in mods:
		match m.kind:
			GateModifier.Kind.ADDITIVE:
				add += m.value
			GateModifier.Kind.MULTIPLICATIVE:
				mul *= m.value
			GateModifier.Kind.CAP:
				pass
	return (base + add) * mul
