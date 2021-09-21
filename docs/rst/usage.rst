=====
Usage
=====


Most modules will depend on a GrafanaFace instance.

.. code:: python

	from grafana_api.grafana_face import GrafanaFace

	gfn = GrafanaFace(
			auth=(
				os.getenv("GF_SECURITY_ADMIN_USER"),
				os.getenv("GF_SECURITY_ADMIN_PASSWORD")
			),
			port=os.getenv("GF_SERVER_HTTP_PORT"),
		)

Finding Things
==============

``grafanarmadillo`` can be used to find your things in Grafana, such as dashboards and folders.

.. code:: python

	from grafanarmadillo.find import Finder

	# inject the GrafanaFace
	finder = Finder(gfn)

	# get all dashboards named "important_dashboard"
	finder.find_dashboards("important_dashboard")

	# get a dashboard by its name and folder
	finder.get_dashboard("Folder", "Dashboard")

	# get a dashboard by its path
	finder.get_dashboard("/Folder/Dashboard")


Importing and Exporting
=======================

``grafanarmadillo`` can be used to import and export Grafana dashboards. It works well with the Finder.

.. code:: python

	from grafanarmadillo.dashboarder import Dashboarder
	from grafanarmadillo.find import Finder

	finder = Finder(gfn)
	dashboarder = Dashboarder(gfn)

	# start by getting the name of the dashboard
	dashboard_info = finder.get_dashboard("Folder", "Dashboard")

	# export a dashboard. You could save this into a file and commit that to git
	exported_dashboard, exported_folder = dashboarder.export_dashboard(dashboard_info)

	# you could then load that dashboard from a file and import it into Grafana
	dashboarder.import_dashboard(exported_dashboard, exported_folder)

	# you can also "clone" the contents of a Grafana dashboard
	# which is useful for propagating a template to other dashboards
	template_info = finder.get_dashboard("Templates", "ServiceA")
	content = dashboarder.get_dashboard_content(template_info)

	prod_dashboard_info = finder.get_dashboard("Prod", "ServiceA")
	dashbaorder.set_dashboard_content(prod_deployment_info, content)
