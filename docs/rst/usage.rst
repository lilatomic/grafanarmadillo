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

.. literalinclude:: ../../tests/usage/dashboarding.py
	:language: python



Templating
==========

``grafanarmadillo`` makes it easier to transform dashboards into templates and templates into dashboards.

.. literalinclude:: ../../tests/usage/templating.py
	:language: python