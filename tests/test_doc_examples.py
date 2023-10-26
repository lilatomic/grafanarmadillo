import io
import json
import os

import pytest
from grafana_client import GrafanaApi

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator
from tests.conftest import read_json_file
from tests.usage.alerting import export_alert, import_alert
from tests.usage.dashboarding import (
	clone_dashboard_contents,
	export_dashboard,
	import_dashboard,
)
from tests.usage.templating import dashboard_maker, template_for_clients, template_maker


def test_usage_dashboard_export(rw_shared_grafana):
	gfn: GrafanaApi = rw_shared_grafana[1]
	out = io.StringIO()

	export_dashboard(gfn, "/f0/f0-0", out)

	out.seek(0)
	exported = json.loads(out.read())
	assert exported["title"] == "f0-0"


def test_usage_dashboard_import(rw_shared_grafana, unique):
	gfn: GrafanaApi = rw_shared_grafana[1]
	finder = Finder(gfn)
	gfn.folder.create_folder(unique)

	folder = finder.get_folder(unique)
	with open(os.path.join("tests", "dashboard.json"), "r") as template:
		import_dashboard(gfn, folder, template)

	assert finder.get_from_path(f"/{unique}/New dashboard Copy")


def test_usage_dashboard_clone(rw_shared_grafana, unique):
	gfn: GrafanaApi = rw_shared_grafana[1]
	dashboarder = Dashboarder(gfn)
	folder = gfn.folder.create_folder(f"f {unique}")
	dashboard = gfn.dashboard.update_dashboard(
		{"dashboard": {"title": unique, "panels": []}, "folderUid": folder["uid"]}
	)
	assert len(dashboarder.get_dashboard_content(dashboard)["panels"]) == 0

	clone_dashboard_contents(gfn, "/General/0", f"/f {unique}/{unique}")

	result = dashboarder.get_dashboard_content(dashboard)
	assert len(result["panels"]) == 1


@pytest.mark.integration
def test_usage_templating(rw_demo_grafana):
	gfn: GrafanaApi = rw_demo_grafana[1]
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


@pytest.mark.integration
def test_usage_templating__findreplace():
	content = read_json_file("usage/dashboard_content_with_templatables.json")

	template = template_maker.make_template_from_dashboard(content)

	assert template["title"] == "$deployment_id - $env"

	dashboard = dashboard_maker.make_dashboard_from_template({}, template)

	assert dashboard["title"] == "1337 - prod"


def test_usage_alerting__import(rw_shared_grafana, unique):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	gfn: GrafanaApi = rw_shared_grafana[1]
	finder = Finder(gfn)
	gfn.folder.create_folder(unique)

	folder = finder.get_folder(unique)
	with open(os.path.join("tests", "alert_rule.json"), "r") as template:
		template = json.loads(template.read())
		template["uid"] = unique
		del template["id"]

	import_alert(gfn, folder, template)

	assert finder.get_alert(folder_name=unique, alert_name=template["title"])


def test_usage_alerting__export(rw_shared_grafana, unique):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	gfn: GrafanaApi = rw_shared_grafana[1]
	out = io.StringIO()

	export_alert(gfn, "f0", "a0", out)

	out.seek(0)
	exported = json.loads(out.read())
	assert exported["title"] == "a0"
