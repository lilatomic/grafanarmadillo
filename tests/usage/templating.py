from typing import List
from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator


def template_for_clients(gfn: GrafanaFace, service_name: str, clients: List[str]):
	finder, dashboarder, templator = Finder(gfn), Dashboarder(gfn), Templator()

	dashboard_info = finder.get_dashboard("Templates", service_name)
	exported_dashboard = dashboarder.get_dashboard_content(dashboard_info)

	template = templator.make_template_from_dashboard(exported_dashboard)

	for client in clients:
		folder = dashboarder.api.folder.create_folder(client)
		info = {"title": f"{service_name}"}

		dashboard = templator.make_dashboard_from_template(info, template)

		dashboarder.import_dashboard(dashboard, folder)
