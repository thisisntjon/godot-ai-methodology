class_name ModifierResolver
extends RefCounted
## Folds Modifier records into one value in a FIXED order: additive, then multiplicative,
## then cap, then clamp to [floor, +inf). Compose effects here — never write pairwise
## "if A and B" special cases.

static func resolve(base: float, mods: Array, floor_value: float = 0.0) -> int:
	var additive := 0.0
	var multiplier := 1.0
	var cap := INF
	var ordered := mods.duplicate()
	ordered.sort_custom(func(a, b):
		if a.kind != b.kind:
			return a.kind < b.kind
		return String(a.source) < String(b.source))
	for m in ordered:
		match m.kind:
			Modifier.Kind.ADDITIVE:
				additive += m.value
			Modifier.Kind.MULTIPLICATIVE:
				multiplier *= m.value
			Modifier.Kind.CAP:
				cap = minf(cap, m.value)
	var result := (base + additive) * multiplier
	result = minf(result, cap)
	result = maxf(result, floor_value)
	return int(result)
