import pytest

from tests.conftest import read_json_file
from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.templator import (
	DashboardTransformer,
	Templator,
	combine_transformers,
	findreplace,
	panel_transformer,
)
from grafanarmadillo.types import DashboardContent


def test_make_template_from_dashboard__has_no_identity():
	templator = Templator()
	d = read_json_file("dashboard_get_result.json")["dashboard"]

	r = templator.make_template_from_dashboard(d)

	assert project_dashboard_identity(r) == {"title": "f0-0"}


def test_make_dashboard_from_template__has_correct_identity():
	templator = Templator()

	d_info = read_json_file("dashboard_search_result.json")
	d_content = read_json_file("dashboard.json")

	r = templator.make_dashboard_from_template(d_info, d_content)

	assert project_dashboard_identity(r) == project_dashboard_identity(d_info)


def test_make_template(unique):
	original = read_json_file("dashboard.json")

	def make_template(d: DashboardContent) -> DashboardContent:
		d["tags"] = [unique]
		return d

	templator = Templator(make_template=make_template)
	template = templator.make_template_from_dashboard(original)

	assert template["tags"] == [unique]


def test_fill_template(unique):
	original = read_json_file("dashboard.json")

	def fill_template(d: DashboardContent) -> DashboardContent:
		d["tags"] = [unique]
		return d

	templator = Templator(fill_template=fill_template)
	template = templator.make_dashboard_from_template({"title": "Not final"}, original)

	assert template["tags"] == [unique]


@pytest.mark.parametrize(
	"input,output",
	[
		("ac", "Ac"),
		("abc", "ABc"),
		(["a", 1], ["A", 1]),
		({"a": "a"}, {"a": "A"}),
		({"a": ["a", 1]}, {"a": ["A", 1]}),
		({"a": {"b": "a", "c": 1}}, {"a": {"b": "A", "c": 1}}),
	],
)
def test_findreplace(input, output):
	fr = findreplace({"a": "A", "b": "B"})

	r = fr(input)
	assert output == r


def make_test_transformer(k, v) -> DashboardTransformer:
	def _transformer(dashboard: DashboardContent) -> DashboardContent:
		d = dashboard.copy()
		d[k] = v
		return d

	return _transformer


def test_combine_transformers():
	t = combine_transformers(
		make_test_transformer("0", "0"), make_test_transformer("1", "1"),
	)

	r = t({})

	assert r["0"] == "0"
	assert r["1"] == "1"


def test_combine_transformers__ordering():
	"""Test that combined transformers are applied in order."""
	k = "0"
	t = combine_transformers(make_test_transformer(k, "0"), make_test_transformer(k, "1"),)

	r = t({})

	assert r[k] == "1"


def test_panel_transformer(unique):
	original = read_json_file("dashboard.json")

	def f(panel):
		out = panel.copy()
		out["title"] = unique
		return out

	t = panel_transformer(f)

	r = t(original)

	assert r["panels"][0]["title"] == unique
	assert all(map(lambda x: x["title"] == unique, r["panels"]))
