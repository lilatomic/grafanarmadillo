
Changelog
=========

v0.0.8 (2021-09-26)
------------------------------------------------------------

* feature : add Finder.create_or_get_dashboard to help importing dashboards
* feature : add helper DashboardTransformer to combine several DashboardTransformers
* feature : add helper DashboardTransformer to process all panels in a dashboard

v0.0.7 (2021-09-24)
------------------------------------------------------------

* feature : Templator, which makes templates from dashboards (and vice-versa) by applying arbitrary transforms

  * includes a helper to easily convert a dictionary into a list of terms to globally find/replace


v0.0.6 (2021-09-21)
------------------------------------------------------------

* feature : Dashboarder

  * can get or set the content of a dashboard

  * can export and import dashboards (like with the "json model" and "import" buttons in Grafana)

* patch : get_dashboard returns exactly 1 (not a list)
* patch : get_folder returns exactly 1 (not list)
* patch : fix returns of methods in Finder

v0.0.5 (2021-09-20)
------------------------------------------------------------

* fix build

v0.0.4 (2021-09-20)
------------------------------------------------------------

* docsdocsdocs

v0.0.3 (2021-09-20)
------------------------------------------------------------

* adds methods for finding Grafana dashboards and folders by name

v0.0.2 (2021-09-18)
------------------------------------------------------------

* fixes CICD pipelines

v0.0.1 (2021-09-16)
-------------------

* templates from https://github.com/joaomcteixeira/python-project-skeleton
