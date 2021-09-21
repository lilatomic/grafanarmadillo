"""Performs integration tests for dashboarder."""
import pytest

from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from tests.conftest import read_json_file


@pytest.mark.parametrize(
	"folder_name,dashboard_name", [("General", "0"), ("f0", "f0-0")]
)
def test_dashboarder_get__present(
	ro_dashboarder: Dashboarder, ro_finder: Finder, folder_name, dashboard_name
):
	dashboard = ro_finder.get_dashboard(folder_name, dashboard_name)

	content = ro_dashboarder.get_dashboard_content(dashboard)

	assert project_dashboard_identity(content) == project_dashboard_identity(dashboard)


@pytest.mark.parametrize(
	"folder_name,dashboard_name", [("General", "0"), ("f0", "f0-0")]
)
def test_dashboard_set__already_present(
	rw_shared_grafana, unique, folder_name, dashboard_name
):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))
	dashboard_search_result = finder.get_dashboard(folder_name, dashboard_name)
	dashboard = finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)

	content = dashboard.copy()
	content.update({"tags": [unique]})

	dashboarder.set_dashboard_content(dashboard_search_result, content)

	result = finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)
	assert result["dashboard"]["tags"] == [unique]
	if folder_name != "General":
		assert result["meta"]["folderUid"] == dashboard_search_result["folderUid"]


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


def test_import__no_folder(rw_shared_grafana, unique):
	_, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard)

	assert (
		dashboarder.api.dashboard.get_dashboard(unique)["dashboard"]["panels"]
		== new_dashboard["panels"]
	)


def test_import__subfolder(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	folder = finder.get_folders("f0")[0]

	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard, folder)

	result = dashboarder.api.dashboard.get_dashboard(unique)

	assert result["dashboard"]["panels"] == new_dashboard["panels"]
	assert result["meta"]["folderUid"] == folder["uid"]


def test_importexport__roundtrip_no_folder(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard)

	dashboard_search_result = finder.get_dashboard("General", unique)
	exported, folder = dashboarder.export_dashboard(dashboard_search_result)

	del exported["id"]
	del new_dashboard["id"]
	assert exported == new_dashboard
	assert folder is None


def test_importexport__roundtrip_subfolder(rw_shared_grafana, unique):
	finder, dashboarder = (Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1]))

	folder_name = "f0"
	target_folder = finder.get_folders(folder_name)[0]
	new_dashboard = read_json_file("dashboard.json")
	new_dashboard["uid"] = unique
	new_dashboard["title"] = unique

	dashboarder.import_dashboard(new_dashboard, target_folder)

	dashboard_search_result = finder.get_dashboard(folder_name, unique)
	exported_dashboard, exported_folder = dashboarder.export_dashboard(
		dashboard_search_result
	)

	del exported_dashboard["id"]
	del new_dashboard["id"]
	assert exported_dashboard == new_dashboard

	assert target_folder["uid"] == exported_folder["uid"]
