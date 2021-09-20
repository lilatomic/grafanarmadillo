from typing import List


def flat_map(f, xs):
	"""Flatmap: Map on a list and then merge the results."""
	ys = []
	for x in xs:
		ys.extend(f(x))
	return ys


def exactly_one(items: List, msg="more than one result found"):
	"""Throws if list does not contain exactly 1 item."""
	if len(items) != 1:
		raise ValueError(msg)
	return items[0]
