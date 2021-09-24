from typing import Callable, Dict, List, TypeVar, Union

from grafanarmadillo.types import DashboardContent, DashboardSearchResult


A = TypeVar("A")
JSON = TypeVar("JSON", bound=Union[dict, list, str, int, float, bool, None])


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


def project_dict(d: Dict, keys: set, inverse: bool = False) -> Dict:
	"""
	Select the given fields from a dictionary.
	
	>>> project_dict({'a': 1, 'b': 2}, set(['a']))
	{'a': 1}

	>>> project_dict({'a': 1, 'b': 2}, set(['a']), inverse=True)
	{'b': 2}
	"""
	return {k: v for k, v in d.items() if inverse ^ (k in keys)}


dashboard_meta_fields = set(["id", "uid", "title"])


def project_dashboard_identity(
	dashboardlike: Union[DashboardSearchResult, DashboardContent]
) -> Dict:
	"""Project only the fields of a dashboard which are used for determining identity."""
	return project_dict(dashboardlike, dashboard_meta_fields)


def erase_dashboard_identity(
	dashboardlike: Union[DashboardSearchResult, DashboardContent]
) -> Dict:
	"""Delete the fields of a dashboard which are used for determining identity."""
	return project_dict(dashboardlike, dashboard_meta_fields, inverse=True)


def map_json_strings(f: Callable[[str], str], obj: JSON) -> JSON:
	"""
	Transform all strings in an object made of JSON primitives.

	>>> f = lambda s: s.upper()
	>>> map_json_strings(f, 's')
	'S'
	>>> map_json_strings(f, 1)
	1
	>>> map_json_strings(f, ['s'])
	['S']
	>>> map_json_strings(f, ['s', 1])
	['S', 1]
	>>> map_json_strings(f, {'a': 's'})
	{'a': 'S'}
	>>> map_json_strings(f, {'a': ['s', 1]})
	{'a': ['S', 1]}
	"""
	if isinstance(obj, dict):
		return {k: map_json_strings(f, v) for k, v in obj.items()}
	elif isinstance(obj, list):
		return [map_json_strings(f, i) for i in obj]
	elif isinstance(obj, str):
		return f(obj)
	else:
		return obj
