def flat_map(f, xs):
	ys = []
	for x in xs:
		ys.extend(f(x))
	return ys


def exactly_one(l, msg="more than one result found"):
	if len(l) != 1:
		raise ValueError(msg)
	return l[0]
