"""Performs integration tests for searches"""

from tests.conftest import ro_demo_grafana
import requests

from grafanarmadillo.find import Finder


def test_with_testcontainer(ro_demo_grafana):
	requests.get(ro_demo_grafana[0].url)


def test_find_dashboards__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert len(f.get_dashboards("0")) == 1


def test_find_folders__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert (len(f.get_folders("f0"))) == 1


def test_find_folder__general_folder(ro_demo_grafana):
	"""The 'General' folder is a special folder, so we synthesis it"""
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
