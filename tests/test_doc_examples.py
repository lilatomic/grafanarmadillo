import io
import json
import os

import pytest
from grafana_api.grafana_face import GrafanaFace

from conftest import read_json_file
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator
from usage.dashboarding import (
	clone_dashboard_contents,
	export_dashboard,
	import_dashboard,
)
from usage.templating import template_for_clients


def test_usage_dashboard_export(rw_shared_grafana):
	gfn: GrafanaFace = rw_shared_grafana[1]
	out = io.StringIO()

	export_dashboard(gfn, "/f0/f0-0", out)

	out.seek(0)
	exported = json.loads(out.read())
	assert exported["title"] == "f0-0"


def test_usage_dashboard_import(rw_shared_grafana, unique):
	gfn: GrafanaFace = rw_shared_grafana[1]
	finder = Finder(gfn)
	gfn.folder.create_folder(unique)

	folder = finder.get_folder(unique)
	with open(os.path.join("tests", "dashboard.json"), "r") as template:
		import_dashboard(gfn, folder, template)

	assert finder.get_from_path(f"/{unique}/New dashboard Copy")


def test_usage_dashboard_clone(rw_shared_grafana, unique):
	gfn: GrafanaFace = rw_shared_grafana[1]
	dashboarder = Dashboarder(gfn)
	folder = gfn.folder.create_folder(f"f{unique}")
	dashboard = gfn.dashboard.update_dashboard(
		{"dashboard": {"title": unique, "panels": []}, "folderUid": folder["uid"]}
	)
	assert len(dashboarder.get_dashboard_content(dashboard)["panels"]) == 0

	clone_dashboard_contents(gfn, "/General/0", f"/f{unique}/{unique}")

	result = dashboarder.get_dashboard_content(dashboard)
	assert len(result["panels"]) == 1


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
