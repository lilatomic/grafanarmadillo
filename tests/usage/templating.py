from typing import List

from grafana_client import GrafanaApi

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator, findreplace


def template_for_clients(gfn: GrafanaApi, service_name: str, clients: List[str]):
	"""Pull a template for a service from the Templates folder on Grafana and fills it out for a client."""
	finder, dashboarder, templator = Finder(gfn), Dashboarder(gfn), Templator()

	dashboard_info = finder.get_dashboard("Templates", service_name)
	exported_dashboard = dashboarder.get_dashboard_content(dashboard_info)

	template = templator.make_template_from_dashboard(exported_dashboard)

	for client in clients:
		folder = dashboarder.api.folder.create_folder(client)
		info = {"title": f"{service_name}"}

		dashboard = templator.make_dashboard_from_template(info, template)

		dashboarder.import_dashboard(dashboard, folder)


# It's easy to do a global findreplace throughout all strings in a dashboard with the `findreplace` helper
# This example templates the ID of the deployment, the environment, and the version

template_maker = Templator(
	make_template=findreplace(
		{
			"0000": "$deployment_id",
			"test": "$env",
			"1.0.0": "$version",
			"ThingDoer": "$service",
		}
	)
)

# We can then expand the template with values later

dashboard_maker = Templator(
	fill_template=findreplace(
		{"$deployment_id": "1337", "$env": "prod", "$version": "1.4.5", "$service": "ETL"}
	)
)
