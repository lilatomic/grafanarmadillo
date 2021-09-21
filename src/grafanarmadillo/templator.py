"""Make and fill templates for dashboards."""
from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.types import DashboardContent, DashboardSearchResult


class Templator(object):
	"""Collection of methods for filling and making templates."""

	def __init__(self) -> None:
		super().__init__()

	def make_template_from_dashboard(
		self, dashboard: DashboardContent
	) -> DashboardContent:
		"""Convert a dashboard into a one ready for templating."""
		new = dashboard.copy()
		del new["uid"]
		del new["id"]
		del new["title"]

		return new

	def make_dashboard_from_template(
		self, dashboard_info: DashboardSearchResult, template: DashboardContent
	) -> DashboardContent:
		"""Inflate a template."""
		new = template.copy()
		new.update(project_dashboard_identity(dashboard_info))

		return new
