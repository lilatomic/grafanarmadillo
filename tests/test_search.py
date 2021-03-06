"""Performs integration tests for searches."""

import pytest
import requests

from grafanarmadillo.find import Finder


def test_with_testcontainer(ro_demo_grafana):
	requests.get(ro_demo_grafana[0].url)


def test_find_dashboards__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert len(f.find_dashboards("0")) == 1


def test_find_folders__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert f.get_folder("f0")


def test_find_folder__general_folder(ro_demo_grafana):
	"""The 'General' folder is a special folder, so we synthesis it."""
	f = Finder(ro_demo_grafana[1])
	assert f.get_folder("General")


def test_get_dashboards_in_folders__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboards_in_folders(["f0"])
	assert len(r) == 1
	assert r[0]["title"] == "f0-0"


def test_get_dashboards_in_folders__only_in_target_folder(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboards_in_folders(["f0"])
	assert len(r) == 1
	assert r[0]["title"] == "f0-0"


def test_get_dashboards_in_folders__general(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboards_in_folders(["General"])
	assert len(r) == 1
	assert r[0]["title"] == "0"


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


def test_resolve_path__general():
	assert Finder(None)._resolve_path("/folder/dashboard") == ("folder", "dashboard")


def test_resolve_path__no_absolute_slash():
	assert Finder(None)._resolve_path("folder/dashboard") == ("folder", "dashboard")


def test_resolve_path__implicit_general():
	assert Finder(None)._resolve_path("/dashboard") == ("General", "dashboard")


def test_resolve_path__bare_dashboard():
	assert Finder(None)._resolve_path("dashboard") == ("General", "dashboard")


def test_resolve_path__too_many_parts():
	with pytest.raises(ValueError):
		Finder(None)._resolve_path("/folder/dashboard/invalidpart")


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
