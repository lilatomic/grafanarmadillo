"""Make and fill templates for dashboards."""
from typing import Callable, Dict

from grafanarmadillo._util import (
	map_json_strings,
	project_dashboard_identity,
	project_dict,
)
from grafanarmadillo.types import DashboardContent, DashboardSearchResult


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
