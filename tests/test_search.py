"""Performs integration tests for searches"""

import requests

from grafanarmadillo.find import Finder


def test_with_testcontainer(ro_demo_grafana):
	requests.get(ro_demo_grafana[0].url)

def test_find_dashboards_smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert len(f.get_dashboards("0")) == 1
	
def test_find_folders_smoke(ro_demo_grafana):
	f = Finder(ro_demo_grafana[1])
	assert(len(f.get_folders("f0"))) == 1
