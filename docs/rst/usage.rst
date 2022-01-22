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

Datasources
===========

Grafana recently added the datasource uid to the dashboard. This solves many problems, but does make migrating between instances a bit harder. ``grafanarmadillo`` provides 2 ways to make this easier. The first is to create your datasources with the ``Datasourcer``. This will give them a stable UID based on the name of the datasource, so the UID will match across instances.

.. code:: python

	from grafanarmadillo.datasourcer import Datasourcer
	from grafanarmadillo.types import DatasourceInfo

	dsinfo: DatasourceInfo = read_json_file("datasource.json")
	datasourcer = Datasourcer(gfn)
	datasourcer.put(dsinfo)

The other way it to use a transformer built for migrating between instances. The ``DatasourceDashboardTransformer`` is built for switching between names and UIDs. This works like a standard dashboard transformer, which you can combine with other dashboard transformers

.. code:: python

	datasources_make_template = DatasourceDashboardTransformer([{'uid': original_uid, 'name': 'name'}]).use_name
	datasources_make_dashboard = DatasourceDashboardTransformer([{'uid': new_uid, 'name': 'name'}]).use_uid

	# with other DashboardTransformers
	template_maker = combine_transformers(findreplace_make_template, datasources_make_template)
	dashboard_maker = combine_transformers(findreplace_make_dashboard, datasources_make_dashboard)
