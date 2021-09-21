"""Performs integration tests for dashboarder"""

from typing import Dict, Union
from tests.conftest import read_json_file
import pytest

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo._util import project_dashboard_identity


def test_dashboarder_get__present(ro_dashboarder: Dashboarder, ro_finder: Finder):
	dashboard = ro_finder.get_dashboard("General", "0")

	content = ro_dashboarder.get_dashboard_content(dashboard)

	import pprint

	pprint.pprint(dashboard)

	assert project_dashboard_identity(content) == project_dashboard_identity(dashboard)


def test_dashboard_set__already_present(rw_demo_grafana):
	marker = "0000"

	finder, dashboarder = (Finder(rw_demo_grafana[1]), Dashboarder(rw_demo_grafana[1]))
	dashboard_search_result = finder.get_dashboard("General", "0")
	dashboard = finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)

	content = dashboard.copy()
	content.update({"tags": [marker]})

	dashboarder.set_dashboard_content(dashboard_search_result, content)

	assert finder.api.dashboard.get_dashboard(
		dashboard_uid=dashboard_search_result["uid"]
	)["dashboard"]["tags"] == [marker]


def test_dashboarder__roundtrip(rw_demo_grafana):
	"""Tests that it's convenient to pull down the content, apply a modification, and push it back up"""
	marker = "0001"

	finder, dashboarder = (Finder(rw_demo_grafana[1]), Dashboarder(rw_demo_grafana[1]))
	dashboard = finder.get_dashboard("General", "0")

	content = dashboarder.get_dashboard_content(dashboard)
	content.update({"tags": [marker]})

	dashboarder.set_dashboard_content(dashboard, content)

	assert finder.api.dashboard.get_dashboard(dashboard_uid=dashboard["uid"])["dashboard"][
		"tags"
	] == [marker]
