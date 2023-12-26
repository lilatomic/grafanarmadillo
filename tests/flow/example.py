from pathlib import Path

from grafanarmadillo.flow import Dashboard, FileStore, Flow, GrafanaStore
from grafanarmadillo.templator import make_mapping_templator
from grafanarmadillo.util import load_data


def export_templates(grafana):
	filestore = FileStore(Path("."))
	grafanastore = GrafanaStore(grafana)

	mapping = load_data("file://tests/cli/mapping.json")
	templator = make_mapping_templator(mapping, "stg", "template")

	flow = Flow(
		store_obj=grafanastore,
		store_tmpl=filestore,
		flows=[
			Dashboard(
				name_obj="/dev/MySystem TEST",
				name_tmpl="/dev/MySystem",
				templator=templator
			)
		]
	)
	result = flow.obj_to_tmpl()
	if result.failures:
		exit(1)


def import_templates(grafana):
	filestore = FileStore(Path("."))
	grafanastore = GrafanaStore(grafana)

	mapping = load_data("file://tests/cli/mapping.json")
	deployments = {"east" "west" "north"}
	flow = Flow(
		store_obj=grafanastore,
		store_tmpl=filestore,
		flows=[
			Dashboard(
				name_tmpl="/dev/MySystem",
				name_obj=f"/{deployment}/my_system",
				templator=(make_mapping_templator(mapping, env_grafana=deployment, env_template="template"))
			) for deployment in deployments
		]
	)
	result = flow.obj_to_tmpl()
	if result.failures:
		exit(1)
