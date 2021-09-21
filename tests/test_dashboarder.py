"""Performs integration tests for dashboarder."""

from tests.conftest import read_json_file
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo._util import project_dashboard_identity


def test_dashboarder_get__present(ro_dashboarder: Dashboarder, ro_finder: Finder):
	dashboard = ro_finder.get_dashboard("General", "0")

	content = ro_dashboarder.get_dashboard_content(dashboard)

	import pprint

	pprint.pprint(dashboard)

	assert project_dashboard_identity(content) == project_dashboard_identity(dashboard)


def test_dashboard_set__already_present(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))
	dashboard_search_result = finder.get_dashboard("General", "0")
	dashboard = finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)

	content = dashboard.copy()
	content.update({"tags": [unique]})

	dashboarder.set_dashboard_content(dashboard_search_result, content)

	assert finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)["dashboard"]["tags"] == [unique]


def test_dashboarder__roundtrip(rw_shared_grafana, unique):
	"""Tests that it's convenient to pull down the content, apply a modification, and push it back up."""
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))
	dashboard = finder.get_dashboard("General", "0")

	content = dashboarder.get_dashboard_content(dashboard)
	content.update({"tags": [unique]})

	dashboarder.set_dashboard_content(dashboard, content)

	assert finder.api.dashboard.get_dashboard(dashboard_uid=dashboard["uid"])["dashboard"][
		"tags"
	] == [unique]


def test_import(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard)

	assert (
		dashboarder.api.dashboard.get_dashboard(unique)["dashboard"]["panels"]
		== new_dashboard["panels"]
	)


def test_importexport__roundtrip(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard)

	dashboard_search_result = finder.get_dashboard("General", unique)
	exported = dashboarder.export_dashboard(dashboard_search_result)

	del exported["id"]
	del new_dashboard["id"]
	assert exported == new_dashboard
