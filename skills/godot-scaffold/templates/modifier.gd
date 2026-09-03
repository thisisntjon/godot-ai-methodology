class_name Modifier
extends RefCounted
## One contribution to a resolved value. Effects emit Modifier records; the resolver folds
## them. This is how effects compose without pairwise special-casing.

enum Kind { ADDITIVE, MULTIPLICATIVE, CAP }

var kind: Kind
var value: float
var source: StringName

static func make(k: Kind, v: float, src: StringName = &"") -> Modifier:
	var m := Modifier.new()
	m.kind = k
	m.value = v
	m.source = src
	return m
