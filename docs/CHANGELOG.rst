
Changelog
=========

v0.9.0 (2025-02-23)
------------------------------------------------------------

* task : (breaking) drop python 3.9
* fix : fix for templating options without a name

v0.8.0 (2024-09-23)
------------------------------------------------------------

* task : upgrade pinned deps
* task : (breaking) drop support for Python 3.8
* fix : also remove folderUID when creating templates
* feature : caching in finder
* feature : `FlowResult.ensure_success` for inline raising flow exceptions
* feature : `FileStore.resolve_object_to_filepath` has the type of object being referenced, allowing separate folders for alerts and dashboards
* feature : `Finder.get_alerts_in_folders`
* refactor : (breaking) set compatibility for API in Finder
* refactor : use `folderUIDs` for newer search API
* feature : FileStore accepts json encoders and decoders
* feature : Flow.extend for adding multiple flows in 1 call
* fix : searching for multiple folders doesn't fail and return all of them
* feature : add DashboardTransformer to help fill Grafana templates
* feature : flow: add URLStore to import dashboards and alerts from remote sources
* feature : flow: allow all PathLike instead of just str
* feature : flow: easier to change filename convention
* fix : fix typo in grafanarmadillo.flow.Store : write_dasbaord -> write_dashboard

v0.7.1 (2024-06-03)
------------------------------------------------------------

* task : commit requests and pytest as test dependencies
* task : bump transitive dependencies
* task : upgrade Pants
* fix : pin migrator to use latest Grafana 10 image (Grafana 11 drops legacy alerting)

v0.7.0 (2024-03-24)
------------------------------------------------------------

* feature : add templator for resolving dashboard uids on alerts
* fix : idempotency of bulk ops importing alerts
* fix : do not double-decode path (mostly affects bulk ops)
* feature : cli supports extra option to remove edit metadata from dashboards
* fix : fix bulk export using wrong key for folders
* task : increase tested Grafana versions
* task : fix docs
* task : migrate to use pyproject.toml

v0.6.0 (2024-03-23)
------------------------------------------------------------

* feature : expose functions to resolve path-like objects into their Grafana references
* fix : handle folders and dashboards with non-path-safe elements
* task : migrate from tox to Pants for build system

v0.5.0 (2024-02-25)
------------------------------------------------------------

* feature : bulk migrator supports templating

v0.4.0 (2024-02-13)
------------------------------------------------------------

* feature : migrator to upgrade alerts from Legacy to Unified
* feature : bulk migrator to move all alerts and dashboards

v0.3.0 (2023-12-26)
------------------------------------------------------------

* feature : Finder.create_or_get_alert will create a placeholder alert instead of faking one
* feature : helpful Flow for performing multiple templating operations
* feature : can set provenance of provisioned alerts (defaults to disabled)
* deprecated : Windows and MacOS platforms are no longer supported

v0.2.1 (2023-10-31)
------------------------------------------------------------

* feature : option to automatically generate template replacers in cli
* feature : expose cli functions as library functions

v0.2.0 (2023-10-30)
------------------------------------------------------------

* feature : find, template, import, and export alerts
* feature : helpful CLI to do the most common task
* feature : add Python 3.12 support
* deprecated : drop Python 3.7 support

v0.1.0 (2023-08-09)
------------------------------------------------------------

* feature : add Python 3.11 support
* feature : add Grafana 9 and 10 support
* task : switch backend to panodata/grafana-client

v0.0.9 (2022-07-26)
------------------------------------------------------------

* feature : add Python 3.9 and Python 3.10 support

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
