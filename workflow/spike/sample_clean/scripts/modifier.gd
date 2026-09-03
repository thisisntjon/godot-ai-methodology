class_name GateModifier
extends RefCounted

enum Kind { ADDITIVE, MULTIPLICATIVE, CAP }

var kind: Kind
var value: float

static func make(k: Kind, v: float) -> GateModifier:
	var m := GateModifier.new()
	m.kind = k
	m.value = v
	return m
