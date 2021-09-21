from grafana_api.grafana_face import GrafanaFace

import pytest
from conftest import read_json_file

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator
from usage.templating import template_for_clients


@pytest.mark.integration
def test_usage_templating(rw_demo_grafana):
	gfn: GrafanaFace = rw_demo_grafana[1]
	finder, dashboarder, templator = Finder(gfn), Dashboarder(gfn), Templator()
	service_name = "Service A"
	clients = ["Client A", "Client B"]

	# setup
	folder = gfn.folder.create_folder("Templates")
	content = templator.make_dashboard_from_template(
		{"title": service_name, "folderTitle": folder["title"]},
		read_json_file("dashboard.json"),
	)
	dashboarder.import_dashboard(content, folder)

	# do
	template_for_clients(gfn, service_name, clients)

	for c in clients:
		assert finder.get_dashboard(c, service_name)