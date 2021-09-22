"""Make and fill templates for dashboards."""
from typing import Callable

from grafanarmadillo._util import (
	erase_dashboard_identity,
	project_dashboard_identity,
)
from grafanarmadillo.types import DashboardContent, DashboardSearchResult


def nop(d: DashboardContent) -> DashboardContent:
	"""Pass template through."""
	return d


class Templator(object):
	"""Collection of methods for filling and making templates."""

	def __init__(
		self,
		make_template: Callable[[DashboardContent], DashboardContent] = nop,
		fill_template: Callable[[DashboardContent], DashboardContent] = nop,
	) -> None:
		super().__init__()
		self.make_template = make_template
		self.fill_template = fill_template

	def make_template_from_dashboard(
		self, dashboard: DashboardContent
	) -> DashboardContent:
		"""Convert a dashboard into a one ready for templating."""
		new = dashboard.copy()
		new = erase_dashboard_identity(new)

		return self.make_template(new)

	def make_dashboard_from_template(
		self, dashboard_info: DashboardSearchResult, template: DashboardContent
	) -> DashboardContent:
		"""Inflate a template."""
		new = template.copy()
		new.update(project_dashboard_identity(dashboard_info))

		return self.fill_template(new)
