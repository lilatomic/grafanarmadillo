"""Ready-to-run commands for common Grafana templating scenarios."""
import json
from pathlib import Path
from typing import IO, Dict, NewType

import click
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator, findreplace


EnvMapping = NewType("EnvMapping", Dict[str, Dict[str, str]])

TOK_AUTO_MAPPING = "$auto"

load_file_help = """Should be encoded as json. You can pass this in as a string; or as file using 'file://path/to/file'"""
auto_template_env_help = "The special value '$auto' will automatically provide a value by prepending a '$' to the keys of the grafana mapping"

mapping_help = \
	"Mapping of values to findreplace in the template. " + \
	"The type should be a mapping of environment names (like 'template' or 'production') " + \
	"to dicts of replacements (for example, `{\"region\": \"SouthWest\"}`). " + \
	load_file_help
env_grafana_help = "Name of the environment in the mapping file for Grafana, found in the `--mapping` argument"
env_template_help = "Name of the environment in the mapping file for the template, found in the `--mapping` argument. " + \
	auto_template_env_help


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
	if env_template == TOK_AUTO_MAPPING:
		mapping_template = {k: "${%s}" % k for k in mapping_grafana.keys()}
	else:
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
def _export_dashboard(ctx, src, dst, mapping, env_grafana, env_template):
	"""Capture a dashboard from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	return export_dashboard(gfn, src, dst, templator)


def export_dashboard(gfn: GrafanaApi, src: str, dst: IO, templator: Templator):
	"""Capture a dashboard from Grafana."""
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

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
def _import_dashboard(ctx, src, dst, mapping, env_grafana, env_template):
	"""Deploy a template to Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	return import_dashboard(gfn, src, dst, templator)


def import_dashboard(gfn: GrafanaApi, src: IO, dst: str, templator: Templator):
	"""Deploy a template to Grafana."""
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

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
def _export_alert(ctx, src, dst, mapping, env_grafana, env_template):
	"""Capture an alert from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	return export_alert(gfn, src, dst, templator)


def export_alert(gfn: GrafanaApi, src: str, dst: IO, templator: Templator):
	"""Capture an alert from Grafana."""
	finder, alerter = Finder(gfn), Alerter(gfn)

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
def _import_alert(ctx, src, dst, mapping, env_grafana, env_template):
	"""Deploy an alert from a template."""
	gfn = make_grafana(ctx.obj["cfg"])

	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	return import_alert(gfn, src, dst, templator)


def import_alert(gfn: GrafanaApi, src: IO, dst: str, templator: Templator):
	"""Deploy an alert from a template."""
	finder, alerter = Finder(gfn), Alerter(gfn)

	template = load_data(src.read())

	alert_info, folder_info = finder.create_or_get_alert(dst)
	alert = templator.make_dashboard_from_template(alert_info, template)
	alerter.import_alert(alert, folder_info)


def resolve_object_to_filepath(base_path: Path, name: str):
	"""Transform the "/folder/object" format to the path on disk that contains the template."""
	path = Path(name)
	if path.is_absolute():
		path = path.relative_to("/")
	template_path = (base_path / path).with_suffix(".json")
	return template_path


if __name__ == "__main__":
	grafanarmadillo()
