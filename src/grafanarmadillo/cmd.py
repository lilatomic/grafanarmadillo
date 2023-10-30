"""Ready-to-run commands for common Grafana templating scenarios."""
import json
from pathlib import Path
from typing import Dict, Literal, NewType, Union

import click
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator, findreplace


EnvMapping = NewType("EnvMapping", Dict[str, Dict[str, str]])
Direction = NewType("Direction", Union[Literal["import"], Literal["export"]])

load_file_help = """Should be encoded as json. You can pass this in as a string; or as file using 'file://path/to/file'"""
mapping_help = \
	"Mapping of values to findreplace in the template. " + \
	"The type should be a mapping of environment names (like 'template' or 'production') " + \
	"to dicts of replacements (for example, `{\"region\": \"SouthWest\"}`). " + \
	load_file_help
env_grafana_help = "Name of the environment in the mapping file for Grafana, found in the `--mapping` argument"
env_template_help = "Name of the environment in the mapping file for the template, found in the `--mapping` argument"


def load_data(data_str: str):
	"""Attempt to load data."""
	_file_uri_prefix = "file://"
	if data_str.startswith(_file_uri_prefix):
		filename = Path(data_str.split(_file_uri_prefix)[1])
		with filename.open(mode="r", encoding="utf-8") as data_file:
			return json.load(data_file)
	else:
		return json.loads(data_str)


def make_mapping_templator(mapping: EnvMapping, env_grafana: str, env_template: str) -> Templator:
	"""Assemble the templator from the environment mapping."""
	mapping_grafana = mapping[env_grafana]
	mapping_template = mapping[env_template]

	# if some keys in the src mapping are not in the dst mapping
	missing = mapping_grafana.keys() - mapping_template.keys()
	if missing:
		raise ValueError(f"Some keys in the source mapping are not present in the destination mapping. {missing=}")

	grafana_to_template = {v: mapping_template[k] for k, v in mapping_grafana.items()}
	template_to_grafana = {v: k for k, v in grafana_to_template.items()}

	return Templator(make_template=findreplace(grafana_to_template), fill_template=findreplace(template_to_grafana))


def make_grafana(config) -> GrafanaApi:
	"""Make a GrafanaApi from the passed config."""
	if isinstance(config.get("auth"), list):
		config["auth"] = tuple(config["auth"])
	return GrafanaApi(**config)


@click.group()
@click.option("--cfg", "-c", help=f"Config for connecting to Grafana. {load_file_help}")
@click.pass_context
def grafanarmadillo(ctx, cfg):
	"""Template Grafana things."""
	ctx.ensure_object(dict)
	config = load_data(cfg)
	ctx.obj["cfg"] = config
	ctx.obj["gfn"] = make_grafana(config)


@grafanarmadillo.group()
def dashboard():
	"""Manage Grafana dashboards."""


@dashboard.command(name="export")
@click.option("--src", help="Path to the dashboard to capture")
@click.option("--dst", help="Path to write the dashboard to", type=click.File('w'))
@click.option("--mapping", help=mapping_help)
@click.option("--env-grafana", help=env_grafana_help)
@click.option("--env-template", help=env_template_help)
@click.pass_context
def export_dashboard(ctx, src, dst, mapping, env_grafana, env_template):
	"""Capture a dashboard from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)

	dashboard_info = finder.get_from_path(src)
	dashboard_content, _ = dashboarder.export_dashboard(dashboard_info)
	template = templator.make_template_from_dashboard(dashboard_content)

	dst.write(json.dumps(template))


@dashboard.command(name="import")
@click.option("--src", help="Path of the template", type=click.File('r'))
@click.option("--dst", help="Path to write the dashboard to")
@click.option("--mapping", help=mapping_help)
@click.option("--env-grafana", help=env_grafana_help)
@click.option("--env-template", help=env_template_help)
@click.pass_context
def import_dashboard(ctx, src, dst, mapping, env_grafana, env_template):
	"""Deploy a template to Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	template = load_data(src.read())

	dashboard_info, folder = finder.create_or_get_dashboard(dst)
	dashboard = templator.make_dashboard_from_template(dashboard_info, template)
	dashboarder.import_dashboard(dashboard, folder)


@grafanarmadillo.group()
def alert():
	"""Manage Grafana alerts."""


@alert.command(name="export")
@click.option("--src", help="Path to the alert to capture")
@click.option("--dst", help="Path to write the alert to", type=click.File('w'))
@click.option("--mapping", help=mapping_help)
@click.option("--env-grafana", help=env_grafana_help)
@click.option("--env-template", help=env_template_help)
@click.pass_context
def export_alert(ctx, src, dst, mapping, env_grafana, env_template):
	"""Capture an alert from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	finder, alerter = Finder(gfn), Alerter(gfn)

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)

	alert_info = finder.get_alert_from_path(src)
	alert, _ = alerter.export_alert(alert_info)
	template = templator.make_template_from_dashboard(alert)

	dst.write(json.dumps(template))


@alert.command(name="import")
@click.option("--src", help="Path of the template", type=click.File('r'))
@click.option("--dst", help="Path to write the dashboard to")
@click.option("--mapping", help=mapping_help)
@click.option("--env-grafana", help=env_grafana_help)
@click.option("--env-template", help=env_template_help)
@click.pass_context
def import_alert(ctx, src, dst, mapping, env_grafana, env_template):
	"""Deploy an alert from a template."""
	gfn = make_grafana(ctx.obj["cfg"])
	finder, alerter = Finder(gfn), Alerter(gfn)

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	template = load_data(src.read())

	alert_info, folder_info = finder.create_or_get_alert(dst)
	alert = templator.make_dashboard_from_template(alert_info, template)

	alerter.import_alert(alert, folder_info)


if __name__ == "__main__":
	grafanarmadillo()
