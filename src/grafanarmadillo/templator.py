"""Make and fill templates for dashboards."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, NewType, Optional

from grafana_client.client import GrafanaClientError

from grafanarmadillo.find import Finder
from grafanarmadillo.paths import PathCodec
from grafanarmadillo.types import (
	DashboardContent,
	DashboardPanel,
	DashboardSearchResult,
)
from grafanarmadillo.util import (
	map_json_strings,
	project_dashboard_identity,
	project_dict,
)


l = logging.getLogger(__name__)


DashboardTransformer = Callable[[DashboardContent], DashboardContent]


def nop(d: DashboardContent) -> DashboardContent:
	"""Pass template through."""
	return d


def findreplace(context: Dict[str, str]) -> DashboardTransformer:
	"""Make DashboardTransformer to make replacements in strings in dashboards."""

	def replace_strings(s: str):
		out = s
		for k, v in context.items():
			out = out.replace(k, v)
		return out

	def _findreplace(d: DashboardContent) -> DashboardContent:
		return map_json_strings(replace_strings, d)

	return _findreplace


def combine_transformers(*transformers: DashboardTransformer) -> DashboardTransformer:
	"""Chain transformers together into one big transformer."""

	def _chained(d: DashboardContent):
		out = d
		for t in transformers:
			out = t(out)
		return out

	return _chained


def panel_transformer(f: Callable[[DashboardPanel], DashboardPanel]) -> DashboardTransformer:
	"""
	Make DashboardTransformer which processes all panels in a dashboard.
	
	Will omit a dashboard if function returns None
	"""

	def _panel_transformer(d: DashboardContent) -> DashboardContent:
		out = d.copy()

		new_panels = list(filter(lambda p: bool(p), (f(p) for p in d["panels"])))

		out["panels"] = new_panels
		return DashboardContent(out)

	return _panel_transformer


def remove_edit_metadata_transformer(d: DashboardContent) -> DashboardContent:
	"""Remove frequently-changing edit metadata, such as "updated", "version", and "provenance"."""
	d.pop("updated", None)
	d.pop("version", None)
	d.pop("provenance", None)
	return d


class Templator:
	"""Collection of methods for filling and making templates."""

	def __init__(
		self,
		make_template: DashboardTransformer = nop,
		fill_template: DashboardTransformer = nop,
	) -> None:
		super().__init__()
		self.make_template = make_template
		self.fill_template = fill_template

	def make_template_from_dashboard(
		self, dashboard: DashboardContent
	) -> DashboardContent:
		"""Convert a dashboard into a one ready for templating."""
		new = dashboard.copy()
		new = project_dict(
			new, {"id", "uid"}, inverse=True
		)  # we don't erase the title so that we can template it later

		return self.make_template(DashboardContent(new))

	def make_dashboard_from_template(
		self, dashboard_info: DashboardSearchResult, template: DashboardContent
	) -> DashboardContent:
		"""Inflate a template."""
		new = template.copy()
		new.update(project_dashboard_identity(dashboard_info))

		return self.fill_template(DashboardContent(new))

	def chain(self, other) -> Templator:
		"""Chain two templators."""
		return Templator(
			make_template=combine_transformers(self.make_template, other.make_template),
			fill_template=combine_transformers(self.fill_template, other.fill_template)
		)


EnvMapping = NewType("EnvMapping", Dict[str, Dict[str, str]])
TOK_AUTO_MAPPING = "$auto"


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


def alert_dashboarduid_templator(finder: Finder) -> Templator:
	"""Resolve the dashboard uid associated with an alert."""

	def uid2ref(d: DashboardContent) -> DashboardContent:
		dashboard_uid = d.get("annotations", {}).get("__dashboardUid__", None)
		if dashboard_uid is None:
			return d

		try:
			address = finder.get_dashboard_by_uid(dashboard_uid)
		except GrafanaClientError as e:
			if e.status_code == 404:
				l.error(f"Could not find dashboard with uid uid={dashboard_uid}")
				return d
			else:
				raise

		d["annotations"]["__dashboardUid__"] = "$$%s" % PathCodec.encode_grafana(address)
		return d

	def ref2uid(d: DashboardContent) -> DashboardContent:
		dashboard_ref_raw: Optional[str] = d.get("annotations", {}).get("__dashboardUid__", None)
		if dashboard_ref_raw is None or not dashboard_ref_raw.startswith("$$"):
			return d

		dashboard_ref = PathCodec.try_parse(PathCodec.decode(Path(dashboard_ref_raw[2:])))

		dashboard, folder = finder.create_or_get_dashboard(dashboard_ref)
		d["annotations"]["__dashboardUid__"] = dashboard["uid"]
		return d

	return Templator(
		make_template=uid2ref,
		fill_template=ref2uid,
	)
