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
	assert (len(f.get_folders("f0"))) == 1


def test_find_folder__general_folder(ro_demo_grafana):
	"""The 'General' folder is a special folder, so we synthesis it."""
	f = Finder(ro_demo_grafana[1])
	assert (len(f.get_folders("General"))) == 1


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

	assert len(r) == 1
	assert r[0]["title"] == "0"


def test_get_dashboard__other_folder(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	r = f.get_dashboard("f0", "f0-0")

	assert len(r) == 1
	assert r[0]["title"] == "f0-0"


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

	assert len(r) == 1
	assert r[0]["title"] == "f0-0"
