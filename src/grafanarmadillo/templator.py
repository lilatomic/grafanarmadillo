"""Make and fill templates for dashboards."""
from typing import Callable, Dict

from grafanarmadillo._util import (
	map_json_strings,
	project_dashboard_identity,
	project_dict,
)
from grafanarmadillo.types import (
	DashboardContent,
	DashboardPanel,
	DashboardSearchResult,
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


def panel_transformer(
	f: Callable[[DashboardPanel], DashboardPanel]
) -> DashboardTransformer:
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

	def make_template_from_dashboard(
		self, dashboard: DashboardContent
	) -> DashboardContent:
		"""Convert a dashboard into a one ready for templating."""
		new = dashboard.copy()
		new = project_dict(
			new, set(["id", "uid"]), inverse=True
		)  # we don't erase the title so we can template it later

		return self.make_template(new)

	def make_dashboard_from_template(
		self, dashboard_info: DashboardSearchResult, template: DashboardContent
	) -> DashboardContent:
		"""Inflate a template."""
		new = template.copy()
		new.update(project_dashboard_identity(dashboard_info))

		return self.fill_template(new)
