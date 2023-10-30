=========
CLI Usage
=========

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
