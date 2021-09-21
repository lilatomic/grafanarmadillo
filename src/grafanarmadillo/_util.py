from typing import Dict, List, TypeVar, Union

from grafanarmadillo.types import DashboardContent, DashboardsearchResult

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
	return {k: v for k, v in d.items() if k in keys}


def project_dashboard_identity(
	dashboardlike: Union[DashboardsearchResult, DashboardContent]
) -> Dict:
	meta_fields = set(["id", "uid", "title"])
	return project_dict(dashboardlike, meta_fields)