"""Helpers and generic functions."""

import json
from pathlib import Path
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


def exactly_one(items: List[A], message: str = None) -> A:
	"""
	Throws if list does not contain exactly 1 item.
	
	>>> exactly_one([1])
	1

	>>> exactly_one([1,2])
	Traceback (most recent call last):
	ValueError: expected exactly 1 item, found=2 message=None

	>>> exactly_one([])
	Traceback (most recent call last):
	ValueError: expected exactly 1 item, found=0 message=None

	"""
	if len(items) == 1:
		return items[0]
	else:
		raise ValueError(f"expected exactly 1 item, found={len(items)} {message=}")


def project_dict(d: Dict, keys: set, inverse: bool = False) -> Dict:
	"""
	Select the given fields from a dictionary.
	
	>>> project_dict({'a': 1, 'b': 2}, {'a'})
	{'a': 1}

	>>> project_dict({'a': 1, 'b': 2}, {'a'}, inverse=True)
	{'b': 2}
	"""
	return {k: v for k, v in d.items() if inverse ^ (k in keys)}


dashboard_meta_fields = {"id", "uid", "title"}
alert_rule_meta_fields = {"id", "uid", "title", "orgID", "folderUID"}


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


def erase_alert_rule_identity(
	alertlike
) -> Dict:
	"""Delete the fields of an alert_rule which are used for determining identity."""
	return project_dict(alertlike, alert_rule_meta_fields, inverse=True)


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


def resolve_object_to_filepath(base_path: Path, name: str):
	"""Transform the "/folder/object" format to the path on disk that contains the template."""
	path = Path(name)
	if path.is_absolute():
		path = path.relative_to("/")
	template_path = (base_path / path).with_suffix(".json")
	return template_path


def load_data(data_str: str):
	"""Attempt to load data."""
	_file_uri_prefix = "file://"
	if data_str.startswith(_file_uri_prefix):
		filename = Path(data_str.split(_file_uri_prefix)[1])
		with filename.open(mode="r", encoding="utf-8") as data_file:
			return json.load(data_file)
	else:
		return json.loads(data_str)


def write_to_file(out_path: Path, obj: dict):
	"""Write an object to file as JSON."""
	out_path.parent.mkdir(parents=True, exist_ok=True)
	with out_path.open(mode="w+", encoding="utf-8") as f:
		json.dump(obj, f, ensure_ascii=False, indent="\t")


def read_from_file(file_path: Path) -> dict:
	"""Read JSON from a file."""
	with file_path.open(mode="r", encoding="utf-8") as f:
		return json.load(f)
