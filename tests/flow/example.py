#!/usr/bin/env python3
from pathlib import Path

import click

from grafanarmadillo.cmd import grafanarmadillo as gcmd
from grafanarmadillo.cmd import make_grafana
from grafanarmadillo.flow import Dashboard, FileStore, Flow, GrafanaStore
from grafanarmadillo.templator import make_mapping_templator
from grafanarmadillo.util import load_data


def export_templates(grafana, basedir: Path):
	"""Export templates from the dev instance."""
	filestore = FileStore(basedir)
	grafanastore = GrafanaStore(grafana)

	mapping = load_data("file://usage/mapping.json")
	templator = make_mapping_templator(mapping, "dev", "template")

	flow = Flow(
		store_obj=grafanastore,
		store_tmpl=filestore,
		flows=[
			Dashboard(
				name_obj="/dev0/MySystem TEST",
				name_tmpl="/dev0/MySystem",
				templator=templator
			)
		]
	)
	result = flow.obj_to_tmpl()
	if result.failures:
		result.raise_first()


def import_templates(grafana, basedir: Path):
	"""Import your templates to the prod instance."""
	filestore = FileStore(basedir)
	grafanastore = GrafanaStore(grafana)

	mapping = load_data("file://usage/mapping.json")
	deployments = {"east", "west", "north"}
	flow = Flow(
		store_obj=grafanastore,
		store_tmpl=filestore,
		flows=[
			Dashboard(
				name_tmpl="/dev0/MySystem",
				name_obj=f"/{deployment}0/my_system",
				templator=(make_mapping_templator(mapping, env_grafana=deployment, env_template="template"))
			) for deployment in deployments
		]
	)
	result = flow.tmpl_to_obj()
	if result.failures:
		result.raise_first()


@gcmd.group()
def my_system():
	"""Wire your commands into the main grafanarmadillo command."""


@my_system.command(name="export")
@click.option("--basedir")
@click.pass_context
def _export_templates(ctx, basedir):
	"""Export templates from the dev instance."""
	gfn = make_grafana(ctx.obj["cfg"])
	export_templates(gfn, Path(basedir))


@my_system.command(name="import")
@click.option("--basedir")
@click.pass_context
def _import_templates(ctx, basedir):
	"""Import your templates to the prod instance."""
	gfn = make_grafana(ctx.obj["cfg"])
	import_templates(gfn, Path(basedir))


if __name__ == "__main__":
	gcmd(auto_envvar_prefix="GRAFANARMADILLO")
