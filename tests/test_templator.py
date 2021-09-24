from string import printable

import pytest

from conftest import read_json_file
from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.templator import Templator, findreplace
from grafanarmadillo.types import DashboardContent


def test_make_template_from_dashboard__has_no_identity():
	templator = Templator()
	d = read_json_file("dashboard_get_result.json")["dashboard"]

	r = templator.make_template_from_dashboard(d)

	assert project_dashboard_identity(r) == {}


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
