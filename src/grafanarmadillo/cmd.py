"""Ready-to-run commands for common Grafana templating scenarios."""
import datetime
import json
import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import IO

import click
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.bulk import BulkExporter, BulkImporter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import (
	Templator,
	alert_dashboarduid_templator,
	make_mapping_templator,
	remove_edit_metadata_transformer,
)
from grafanarmadillo.util import load_data


load_file_help = """Should be encoded as json. You can pass this in as a string; or as file using 'file://path/to/file'"""
auto_template_env_help = "The special value '$auto' will automatically provide a value by prepending a '$' to the keys of the grafana mapping"

mapping_help = (
	"Mapping of values to findreplace in the template. "
	+ "The type should be a mapping of environment names (like 'template' or 'production') "
	+ 'to dicts of replacements (for example, `{"region": "SouthWest"}`). '
	+ load_file_help
)
env_grafana_help = "Name of the environment in the mapping file for Grafana, found in the `--mapping` argument"
env_template_help = (
	"Name of the environment in the mapping file for the template, found in the `--mapping` argument. "
	+ auto_template_env_help
)
templator_extra_opts_help = (
	textwrap.dedent(
		"""\
		Extra options for the templator
		
		- remove_edit_metadata : remove metadata related to edits on the dashboard, such as the version and last modified times
		
		- resolve_alert_dashboarduid : resolve the dashboard referenced by an alert to a reference.
		
		"""
	) + load_file_help
)


def make_grafana(config) -> GrafanaApi:
	"""Make a GrafanaApi from the passed config."""
	if isinstance(config.get("auth"), list):
		config["auth"] = tuple(config["auth"])
	return GrafanaApi(**config)


@dataclass(frozen=True)
class TemplatorOpts:
	"""Extra options for the templator."""

	remove_edit_metadata: bool = False
	resolve_alert_dashboarduid: bool = False


def apply_template_opts(gfn: GrafanaApi, opts: TemplatorOpts, templator: Templator) -> Templator:
	"""Apply the extra templator options."""
	if opts.remove_edit_metadata:
		templator = templator.chain(Templator(make_template=remove_edit_metadata_transformer))
	if opts.resolve_alert_dashboarduid:
		templator = templator.chain(alert_dashboarduid_templator(Finder(gfn)))
	return templator


def make_templator(gfn: GrafanaApi, mapping, env_grafana, env_template, templator_extra_opts) -> Templator:
	"""Assemble the templator."""
	mapping = load_data(mapping)
	templator = make_mapping_templator(mapping, env_grafana, env_template)
	extra_opts = TemplatorOpts(**load_data(templator_extra_opts))
	templator = apply_template_opts(gfn, extra_opts, templator)
	return templator


def with_template_options(f):
	"""Add template options to a command."""
	return click.option("--templator-extra-opts", default="{}", help=templator_extra_opts_help)(
		click.option("--mapping", help=mapping_help)(
			click.option("--env-grafana", help=env_grafana_help)(
				click.option("--env-template", help=env_template_help)(f)
			)
		)
	)


@click.group()
@click.option("--cfg", "-c", help=f"Config for connecting to Grafana. {load_file_help}")
@click.pass_context
def grafanarmadillo(ctx, cfg):
	"""Template Grafana things."""
	ctx.ensure_object(dict)
	if cfg:
		config = load_data(cfg)
		if isinstance(config.get("auth"), list):
			config["auth"] = tuple(config["auth"])
	else:
		config = {}
	ctx.obj["cfg"] = config


@grafanarmadillo.group()
def dashboard():
	"""Manage Grafana dashboards."""


@dashboard.command(name="export")
@click.option("--src", help="Path to the dashboard to capture")
@click.option("--dst", help="Path to write the dashboard to", type=click.File("w"))
@with_template_options
@click.pass_context
def _export_dashboard(ctx, src, dst, mapping, env_grafana, env_template, templator_extra_opts):
	"""Capture a dashboard from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
	return export_dashboard(gfn, src, dst, templator)


def export_dashboard(gfn: GrafanaApi, src: str, dst: IO, templator: Templator):
	"""Capture a dashboard from Grafana."""
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)

	dashboard_info = finder.get_from_path(src)
	dashboard_content, _ = dashboarder.export_dashboard(dashboard_info)
	template = templator.make_template_from_dashboard(dashboard_content)

	dst.write(json.dumps(template))


@dashboard.command(name="import")
@click.option("--src", help="Path of the template", type=click.File("r"))
@click.option("--dst", help="Path to write the dashboard to")
@with_template_options
@click.pass_context
def _import_dashboard(ctx, src, dst, mapping, env_grafana, env_template, templator_extra_opts):
	"""Deploy a template to Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
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
@click.option("--dst", help="Path to write the alert to", type=click.File("w"))
@with_template_options
@click.pass_context
def _export_alert(ctx, src, dst, mapping, env_grafana, env_template, templator_extra_opts):
	"""Capture an alert from Grafana."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
	return export_alert(gfn, src, dst, templator)


def export_alert(gfn: GrafanaApi, src: str, dst: IO, templator: Templator):
	"""Capture an alert from Grafana."""
	finder, alerter = Finder(gfn), Alerter(gfn)

	alert_info = finder.get_alert_from_path(src)
	alert, _ = alerter.export_alert(alert_info)
	template = templator.make_template_from_dashboard(alert)

	dst.write(json.dumps(template))


@alert.command(name="import")
@click.option("--src", help="Path of the template", type=click.File("r"))
@click.option("--dst", help="Path to write the dashboard to")
@with_template_options
@click.pass_context
def _import_alert(ctx, src, dst, mapping, env_grafana, env_template, templator_extra_opts):
	"""Deploy an alert from a template."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
	return import_alert(gfn, src, dst, templator)


def import_alert(gfn: GrafanaApi, src: IO, dst: str, templator: Templator):
	"""Deploy an alert from a template."""
	finder, alerter = Finder(gfn), Alerter(gfn)

	template = load_data(src.read())

	alert_info, folder_info = finder.create_or_get_alert(dst)
	alert = templator.make_dashboard_from_template(alert_info, template)
	alerter.import_alert(alert, folder_info)


@grafanarmadillo.group()
def migrate():
	"""Migrate between Grafana instances."""


@migrate.command()
@click.option(
	"--grafana-db-path",
	help="Path to the Grafana DB",
	type=click.Path(exists=True, path_type=Path),
)
@click.option(
	"--grafana-container-image",
	help="Grafana image to upgrade to",
	default="grafana/grafana:latest",
)
@click.option(
	"--output-directory",
	"-o",
	help="Path to write output files",
	type=click.Path(exists=True, path_type=Path),
	default=".",
)
@click.option(
	"--grafana-extra-envvars",
	help=f"Environment variables to pass to the Grafana container used to migrate the alerts. {load_file_help}",
	default=None,
)
@click.option(
	"--grafana-migration-timeout",
	help="Timeout in seconds to wait for the Grafana docker container to apply all migrations. A large Grafana instance may take a long time",
	default=300,
	type=int,
)
@click.option(
	"--clone-db",
	help="whether to perform migrations on a clone of the DB or the DB itself",
	type=click.BOOL,
	default=True,
)
@with_template_options
@click.pass_context
def upgrade_alerting(
	ctx,
	grafana_db_path,
	grafana_container_image,
	output_directory,
	grafana_extra_envvars,
	grafana_migration_timeout,
	clone_db,
	mapping,
	env_grafana,
	env_template,
	templator_extra_opts,
):
	"""
	Migrate from Classic to Unified alerting.

	Migrations from Classic to Unified alerting is done as DB migrations.
	We clone the database and use a docker container to perform the migration.
	Note that because we use a clone of the DB, we need to supply the config with the auth for the live instance.
	"""
	from grafanarmadillo.migrate import migrate

	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)

	cfg = ctx.obj["cfg"]
	if grafana_extra_envvars:
		grafana_extra_envvars = load_data(grafana_extra_envvars)
	else:
		grafana_extra_envvars = {}
	migrate(
		cfg,
		grafana_container_image,
		grafana_db_path,
		output_directory,
		templator,
		extra_env_vars=grafana_extra_envvars,
		timeout=datetime.timedelta(seconds=grafana_migration_timeout),
		clone_db=clone_db,
	)


@grafanarmadillo.group()
def resources():
	"""Move many resources to a Grafana."""


@resources.command("import")
@click.option(
	"--root-directory",
	help="Root directory for all resources",
	type=click.Path(exists=True, path_type=Path),
)
@with_template_options
@click.pass_context
def _import_resources(
	ctx,
	root_directory: Path,
	mapping,
	env_grafana,
	env_template,
	templator_extra_opts,
):
	"""Load exported dashboards and alerts."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
	operator = BulkImporter(ctx.obj["cfg"], root_directory, templator=templator)
	operator.run()


@resources.command("export")
@click.option(
	"--root-directory",
	help="Root directory for all resources",
	type=click.Path(exists=True, path_type=Path),
)
@with_template_options
@click.pass_context
def _export_resources(
	ctx,
	root_directory: Path,
	mapping,
	env_grafana,
	env_template,
	templator_extra_opts,
):
	"""Export dashboards and alerts from a Grafana instance."""
	gfn = make_grafana(ctx.obj["cfg"])
	templator = make_templator(gfn, mapping, env_grafana, env_template, templator_extra_opts)
	operator = BulkExporter(ctx.obj["cfg"], root_directory, templator=templator)
	operator.run()


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	grafanarmadillo()
