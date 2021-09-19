"""Performs integration tests for searches"""

import requests

from grafanarmadillo.find import Finder


def test_with_testcontainer(ro_demo_grafana):
	requests.get(ro_demo_grafana[0].url)

def test_find_dashboards__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert len(f.get_dashboards("0")) == 1
	
def test_find_folders__smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert(len(f.get_folders("f0"))) == 1

def test_find_folder__general_folder(ro_demo_grafana):
	"""The 'General' folder is a special folder, so we synthesis it"""
	f = Finder(ro_demo_grafana[1])
	assert(len(f.get_folders("General"))) == 1
