"""Ready-to-run commands for common Grafana templating scenarios."""
import json
from typing import IO

import click
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator, make_mapping_templator
from grafanarmadillo.util import load_data


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


if __name__ == "__main__":
	grafanarmadillo()
