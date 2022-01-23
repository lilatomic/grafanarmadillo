import pytest

from conftest import read_json_file
from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.templator import (
	DashboardTransformer,
	DatasourceDashboardTransformer,
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
		make_test_transformer("0", "0"),
		make_test_transformer("1", "1"),
	)

	r = t({})

	assert r["0"] == "0"
	assert r["1"] == "1"


def test_combine_transformers__ordering():
	"""Test that combined transformers are applied in order."""
	k = "0"
	t = combine_transformers(
		make_test_transformer(k, "0"),
		make_test_transformer(k, "1"),
	)

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


class TestDatasourceTransformer:
	"""Tests for the DatasourceDashboardTransformer."""

	def test_use_name(self, unique):
		original = read_json_file("dashboard_with_datasource.json")
		datasource = read_json_file("datasource.json")

		t = DatasourceDashboardTransformer([datasource])
		r = t.use_name(original)

		ds = r["panels"][0]["targets"][0]["datasource"]
		assert ds["name"] == datasource["name"]
		assert "uid" not in ds

	def test_use_uid(self, unique):
		original = read_json_file("dashboard_with_datasource.json")
		datasource = read_json_file("datasource.json")

		_d = original["panels"][0]["targets"][0]["datasource"]
		_d["name"] = datasource["name"]
		del _d["uid"]

		t = DatasourceDashboardTransformer([datasource])
		r = t.use_uid(original)

		ds = r["panels"][0]["targets"][0]["datasource"]
		assert ds["uid"] == datasource["uid"]
		assert "name" not in ds

	def test_name_intermediate(self, unique):
		"""Test using the DatasourceDashboardTransformer to make a template and then to inflate that template."""
		original = read_json_file("dashboard_with_datasource.json")
		original_uid = original["panels"][0]["targets"][0]["datasource"]["uid"]

		t0 = DatasourceDashboardTransformer([{'uid': original_uid, 'name': 'name'}]).use_name
		t1 = DatasourceDashboardTransformer([{'uid': unique, 'name': 'name'}]).use_uid

		t = combine_transformers(t0, t1)

		r = t(original)

		ds = r["panels"][0]["targets"][0]["datasource"]
		assert ds['uid'] == unique

	def test_modify_panel_datasource_multiple_targets(self):
		p = read_json_file("panel.json")

		t = DatasourceDashboardTransformer([])

		def modify(d):
			d['modified'] = True
			return d

		r = t._modify_panel_datasources(modify, p)

		targets = r["targets"]
		assert targets[0]["datasource"]["modified"]
		assert targets[1]["datasource"]["modified"]
		assert "modified" not in targets[2]["datasource"]

	def test_datasource_absent(self):
		d = read_json_file("dashboard_with_datasource.json")

		t = DatasourceDashboardTransformer([])

		r = t.use_name(d)

		assert r["panels"][0]["targets"][0]["datasource"]["uid"] == "f8c0b7a3-7d64-5ed8-a2fe-e6f517330dc2"

	def test_multiple_datasources(self):
		d = read_json_file("dashboard_with_datasource.json")
		p = read_json_file("panel.json")
		d["panels"] = [p]

		sources = [{'uid': "f8c0b7a3-7d64-5ed8-a2fe-e6f517330dc2", "name": "s0"}, {"uid": "d91fe7c1-075a-4e0e-93ff-8d4d163b95a2", "name": "s1", "refId": "B"}]

		t = DatasourceDashboardTransformer(sources)
		r = t.use_name(d)

		targets = r["panels"][0]["targets"]
		assert targets[0]["datasource"]["name"] == "s0"
		assert targets[1]["datasource"]["name"] == "s1"
		assert "name" not in targets[2]["datasource"]
