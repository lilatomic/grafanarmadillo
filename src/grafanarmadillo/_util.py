from typing import Dict, List, TypeVar, Union

from grafanarmadillo.types import DashboardContent, DashboardSearchResult


A = TypeVar("A")


def flat_map(f, xs):
	"""
	Flatmap: Map on a list and then merge the results.
	
	>>> and_reversed = lambda s: [s,s[::-1]]

	>>> flat_map(and_reversed, [])
	[]

	>>> flat_map(and_reversed, ['hi'])
	['hi', 'ih']

	>>> flat_map(and_reversed, ['hi', 'hello'])
	['hi', 'ih', 'hello', 'olleh']

	"""
	ys = []
	for x in xs:
		ys.extend(f(x))
	return ys


def exactly_one(items: List[A], msg="did not find exactly one item") -> A:
	"""
	Throws if list does not contain exactly 1 item.
	
	>>> exactly_one([1])
	1

	>>> exactly_one([1,2])
	Traceback (most recent call last):
	ValueError: did not find exactly one item

	>>> exactly_one([])
	Traceback (most recent call last):
	ValueError: did not find exactly one item

	"""
	if len(items) != 1:
		raise ValueError(msg)
	return items[0]


def project_dict(d: Dict, keys: set) -> Dict:
	"""
	Select the given fields from a dictionary.
	
	>>> project_dict({'a': 1, 'b': 2}, set(['a']))
	{'a': 1}
	"""
	return {k: v for k, v in d.items() if k in keys}


def project_dashboard_identity(
	dashboardlike: Union[DashboardSearchResult, DashboardContent]
) -> Dict:
	"""Project only the fields of a dashboard which are used for determining identity."""
	meta_fields = set(["id", "uid", "title"])
	return project_dict(dashboardlike, meta_fields)
