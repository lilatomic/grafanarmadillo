====
Flow
====

Grafanarmadillo includes tools to help with exporting and importing multiple templates. For example: You might have a dashboard for developers to test new alerts and visualisations titled "MySystem TEST". When the devs are happy, they want an instance of the dashboard created for each of 3 deployments with the correct names and deployment_ids. They also want to be able to check the template into git so they can revert to a previous version.

Grafanarmadillo's Flow makes this easy! The CLI is good for simple scenarios or for integration with shell scripts. Flow can be a better choice for more complicated deployments or for integrating with other systems.

#. Create a :code:`Flow` object. Specify the locations where templates and objects will be stored. Add flowables to the :code:`Flow` for the objects you want to capture templates. Then, run the flow. The following code defines a function :code:`export_templates` to capture the template and save it in the file "/dev/MySystem.json"; and a function :code:`import_templates` to expand that template for each of the deployments.

   .. literalinclude:: ../../tests/flow/example.py
	:language: python
