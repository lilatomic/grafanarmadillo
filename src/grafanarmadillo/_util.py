from typing import Dict, List, TypeVar, Union

from grafanarmadillo.types import DashboardContent, DashboardSearchResult


A = TypeVar("A")


def flat_map(f, xs):
	"""Flatmap: Map on a list and then merge the results."""
	ys = []
	for x in xs:
		ys.extend(f(x))
	return ys


def exactly_one(items: List[A], msg="more than one result found") -> A:
	"""Throws if list does not contain exactly 1 item."""
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
