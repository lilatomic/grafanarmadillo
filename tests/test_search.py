"""Performs integration tests for searches."""

import pytest
import requests

from grafanarmadillo.find import Finder
from tests.conftest import requires_alerting


def test_with_testcontainer(ro_demo_grafana):
	requests.get(ro_demo_grafana[0].url)


def test_find_dashboards__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert len(f.find_dashboards("0")) == 1


def test_find_folders__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert f.get_folder("f0")


def test_find_folder__general_folder(ro_demo_grafana):
	"""The 'General' folder is a special folder, so we synthesise it."""
	f = Finder(ro_demo_grafana[1])
	assert f.get_folder("General")


class TestGetDashboardsInFolders:

	def test_smoke(self, ro_demo_grafana):
		f = Finder(ro_demo_grafana[1], ro_demo_grafana[0].major_version)
		r = f.get_dashboards_in_folders(["f0"])
		assert len(r) == 1
		assert r[0]["title"] == "f0-0"

	def test_multiple(self, ro_demo_grafana):
		f = Finder(ro_demo_grafana[1], ro_demo_grafana[0].major_version)
		r = f.get_dashboards_in_folders(["f0", "f0_similar"])
		assert len(r) == 1

	def test_only_in_target_folder(self, ro_demo_grafana):
		f = Finder(ro_demo_grafana[1], ro_demo_grafana[0].major_version)
		r = f.get_dashboards_in_folders(["f0"])
		assert len(r) == 1
		assert r[0]["title"] == "f0-0"

	def test_general(self, ro_demo_grafana):
		f = Finder(ro_demo_grafana[1], ro_demo_grafana[0].major_version)
		r = f.get_dashboards_in_folders(["General"])
		assert len(r) == 1
		assert r[0]["title"] == "0"


class TestGetAlertsInFolders:

	def test_smoke(self, ro_demo_grafana):
		requires_alerting(ro_demo_grafana)

		f = Finder(ro_demo_grafana[1], ro_demo_grafana[0].major_version)
		r = f.get_alerts_in_folders(["f0"])
		assert len(r) == 1
		assert r[0]["title"] == "a0"


def test_get_dashboard__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	f.get_dashboard("General", "0")


def test_get_dashboard__general_folder(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboard("General", "0")

	assert r["title"] == "0"


def test_get_dashboard__other_folder(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboard("f0", "f0-0")

	assert r["title"] == "f0-0"


def test_get_from_path__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_from_path("/f0/f0-0")

	assert r["title"] == "f0-0"


def test_create_or_get__new_folder_and_dashboard(rw_shared_grafana, unique):
	f = Finder(rw_shared_grafana[1])
	path = f"/f{unique}/{unique}"

	r_dashboard, r_folder = f.create_or_get_dashboard(path)

	assert r_dashboard is not None and r_folder is not None

	r = f.get_from_path(path)
	assert r["title"] == unique
	assert r["folderTitle"] == "f" + unique


def test_create_or_get__existing_folder_new_dashboard(rw_shared_grafana, unique):
	f = Finder(rw_shared_grafana[1])
	path = f"/f0/{unique}"

	r_dashboard, r_folder = f.create_or_get_dashboard(path)

	assert r_dashboard is not None and r_folder is not None

	r = f.get_from_path(path)
	assert r["title"] == unique
	assert r["folderTitle"] == "f0"


def test_create_or_get__existing_folder_and_dashboard(rw_shared_grafana):
	f = Finder(rw_shared_grafana[1])
	path = "/f0/f0-0"

	r_dashboard, r_folder = f.create_or_get_dashboard(path)

	assert r_dashboard is not None and r_folder is not None

	r = f.get_from_path(path)
	assert r["title"] == "f0-0"
	assert r["folderTitle"] == "f0"

	dashboard = f.api.dashboard.get_dashboard(r["uid"])
	assert len(dashboard["dashboard"]["panels"]) == 1


def test_create_or_get__new_folder_and_alert(rw_shared_grafana, unique):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	f = Finder(rw_shared_grafana[1])
	path = f"/f{unique}/{unique}"

	r_alert, r_folder = f.create_or_get_alert(path)

	assert r_alert is not None and r_folder is not None
	assert r_alert["folderUID"] == r_folder["uid"], "alert did not have parent folder's UID"

	r = f.get_folder(f"f{unique}")
	assert r["uid"] == r_folder["uid"]


def test_create_or_get__existing_folder_new_alert(rw_shared_grafana, unique):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	f = Finder(rw_shared_grafana[1])
	path = f"/f0/{unique}"

	r_alert, r_folder = f.create_or_get_alert(path)

	assert r_alert is not None and r_folder is not None
	assert r_alert["folderUID"] == r_folder["uid"], "alert did not have parent folder's UID"

	r = f.get_folder("f0")
	assert r["uid"] == r_folder["uid"]


def test_create_or_get__existing_folder_and_alert(rw_shared_grafana, unique):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	f = Finder(rw_shared_grafana[1])
	path = "/f0/a0"

	r_alert, r_folder = f.create_or_get_alert(path)

	r = f.get_alert_from_path(path)
	assert r["title"] == "a0"
	assert r["folderUID"] == r_folder["uid"]

	alert = f.api.alertingprovisioning.get_alertrule(r_alert["uid"])
	assert alert
