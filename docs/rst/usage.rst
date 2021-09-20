=====
Usage
=====

Finding Things
==============

``grafanarmadillo`` can be used to find your things in Grafana, such as dashboards and folders.

.. code:: python

	from grafana_api.grafana_face import GrafanaFace
	from grafanarmadillo import Finder

	# start by creating a GrafanaFace instance
	gfn = GrafanaFace(
			auth=(
				os.getenv("GF_SECURITY_ADMIN_USER"),
				os.getenv("GF_SECURITY_ADMIN_PASSWORD")
			),
			port=os.getenv("GF_SERVER_HTTP_PORT"),
		)
	
	# then just create a Finder
	finder = Finder(gfn)

	# get all dashboards named "important_dashboard"
	finder.find_dashboards("important_dashboard")

	# get a dashboard by its name and folder
	finder.get_dashboard("Folder", "Dashboard")

	# get a dashboard by its path
	finder.get_dashboard("/Folder/Dashboard")
