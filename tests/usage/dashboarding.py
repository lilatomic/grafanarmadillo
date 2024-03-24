import json

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder


def export_dashboard(gfn, dashboard_path, destination_file):
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

	# start by getting the name of the dashboard
	dashboard_info = finder.get_from_path(dashboard_path)

	# export a dashboard. You could save this into a file and commit that to git
	exported_dashboard, _exported_folder = dashboarder.export_dashboard(dashboard_info)

	return destination_file.write(json.dumps(exported_dashboard))


def import_dashboard(gfn, folder, source_file):
	dashboarder = Dashboarder(gfn)

	dashboard = json.loads(source_file.read())

	# you could then load that dashboard from a file and import it into Grafana
	return dashboarder.import_dashboard(dashboard, folder)


def clone_dashboard_contents(gfn, source_path, dest_path):
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

	# you can also "clone" the contents of a Grafana dashboard
	# which is useful for propagating a template to other dashboards
	template_info = finder.get_from_path(source_path)
	content = dashboarder.get_dashboard_content(template_info)

	prod_dashboard_info = finder.get_from_path(dest_path)
	return dashboarder.set_dashboard_content(prod_dashboard_info, content)
