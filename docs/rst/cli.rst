=========
CLI Usage
=========

Common templating
=================

Grafanarmadillo includes a CLI to do the most common operation of importing and exporting templates with a find-replace templator. For example: You might have a dashboard for developers to test new alerts and visualisations titled "MySystem TEST". When the devs are happy, they want an instance of the dashboard created for each of 3 deployments with the correct names and deployment_ids. They also want to be able to check the template into git so they can revert to a previous version.

Grafanarmadillo's CLI makes this easy!

#. Create a config for connecting to Grafana. These parameters will be passed in directly to the `grafana_client.GrafanaApi <https://github.com/panodata/grafana-client/blob/main/grafana_client/api.py>`_ . You can set it directly in a variable or save it to a file and use a URI of "file://path/to/file.json"

   .. literalinclude:: ../../tests/usage/grafana_cfg.json
	:language: json


#. Create a mapping file for strings to findreplace. The format consists of names of environments mapped to dictionaries of replacements. Each key in the replacement is the name in the template, and each value is what that key should be expanded to. For example, to represent the deployment name "TEST" we might use :code:`"$deployment_name": "TEST"`. The "$" is not necessary, but might help prevent spurious replacements.

   .. literalinclude:: ../../tests/usage/mapping.json
	:language: json


#. Capture the template (you can commit this into git).

   .. literalinclude:: ../../tests/usage/cli_export.bash
	:language: bash


#. Deploy the template to Grafana

   .. literalinclude:: ../../tests/usage/cli_import.bash
	:language: bash


Migrations
==========

Bulk operations
---------------

Grafanarmadillo also includes some tools from performing some migrations. :code:`grafanarmadillo resources export` and :code:`grafanarmadillo resources import` allow for a bulk export and import of all alerts. These tools map between the Grafana instance and a filesystem::

	dashboards
		org0
			folder0
				dashboard.json
	alerts
		org0
			folder0
				alert.json


Migrating from Classic to Unified alerting
------------------------------------------

Another migrator included in Grafanarmadillo upgrades from Classic to Unified alerting. This needs to happen as a database migration. Grafanarmadillo clones the DB and uses a docker container to run the migrations. It then uses bulk operations to copy the upgraded dashboards and alerts and save them to disk. You can then inspect and filter the exported alerts, for example to only migrate a single org. The bulk importer can then be used to move these into a new Grafana instance.
