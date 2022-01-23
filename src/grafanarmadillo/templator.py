"""Make and fill templates for dashboards."""
from typing import Callable, Dict, List

from grafanarmadillo._util import (
	map_json_strings,
	project_dashboard_identity,
	project_dict,
)
from grafanarmadillo.types import (
	DashboardContent,
	DashboardPanel,
	DashboardSearchResult,
	DatasourceInfo,
)


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

	def _panel_transformer(d: DashboardContent):
		out = d.copy()

		new_panels = list(filter(lambda p: bool(p), (f(p) for p in d["panels"])))

		out["panels"] = new_panels
		return out

	return _panel_transformer


class DatasourceDashboardTransformer:
	"""DashboardTransformers for moving datasources between instances."""

	expr_token = "__expr__"

	def __init__(self, datasources: List[DatasourceInfo]):
		self.by_name = {d["name"]: d for d in datasources}
		self.by_uid = {d["uid"]: d for d in datasources}

	def _modify_panel_datasources(self, f: Callable, panel):
		targets = panel["targets"]
		out = []
		for t in targets:
			if "datasource" in t and t["datasource"] != self.expr_token:
				d = t["datasource"]
				t["datasource"] = f(d)
				out.append(t)

		panel["targets"] = out
		return panel

	def _use_name(self, panel):
		def _do_add_name(d):
			d["name"] = self.by_uid[d["uid"]]["name"]
			del d["uid"]
			return d

		return self._modify_panel_datasources(_do_add_name, panel)

	def _use_uid(self, panel):
		def _do_rebuild_uid(d):
			d["uid"] = self.by_name[d["name"]]["uid"]
			del d["name"]
			return d

		return self._modify_panel_datasources(_do_rebuild_uid, panel)

	def use_name(self, d: DashboardContent):
		"""Use the datasource name in the dashboard. Useful for making a template."""
		return panel_transformer(self._use_name)(d)

	def use_uid(self, d: DashboardContent):
		"""Use the datasource uid in the dashboard. Useful for making a dashboard."""
		return panel_transformer(self._use_uid)(d)


class Templator(object):
	"""Collection of methods for filling and making templates."""

	def __init__(
		self,
		make_template: DashboardTransformer = nop,
		fill_template: DashboardTransformer = nop,
	) -> None:
		super().__init__()
		self.make_template = make_template
		self.fill_template = fill_template

	def make_template_from_dashboard(self, dashboard: DashboardContent) -> DashboardContent:
		"""Convert a dashboard into a one ready for templating."""
		new = dashboard.copy()
		new = project_dict(new, set(["id", "uid"]), inverse=True)  # we don't erase the title so we can template it later

		return self.make_template(new)

	def make_dashboard_from_template(self, dashboard_info: DashboardSearchResult, template: DashboardContent) -> DashboardContent:
		"""Inflate a template."""
		new = template.copy()
		new.update(project_dashboard_identity(dashboard_info))

		return self.fill_template(new)
