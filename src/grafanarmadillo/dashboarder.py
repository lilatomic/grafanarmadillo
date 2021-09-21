from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo.types import Dashboard, DashboardSearchResult, DashboardContent
from grafanarmadillo._util import project_dashboard_identity


class Dashboarder(object):
	"""Collection of methods for managing dashboards"""

	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboard_content(self, dashboard: DashboardSearchResult):
		return self.api.dashboard.get_dashboard(dashboard["uid"])["dashboard"]

	def set_dashboard_content(
		self, dashboard: DashboardSearchResult, content: DashboardContent
	):
		new_dashboard = dashboard.copy()
		new_content = content.copy()

		new_content.update(project_dashboard_identity(new_dashboard))

		new_dashboard.update({"dashboard": new_content, "overwrite": True})

		return self.api.dashboard.update_dashboard(new_dashboard)

	def import_dashboard(self, content: DashboardContent):
		new_dashboard = {"dashboard": content, "overwrite": True}

		return self.api.dashboard.update_dashboard(new_dashboard)

	def export_dashboard(self, dashboard: DashboardSearchResult) -> Dashboard:
		return self.api.dashboard.get_dashboard(dashboard["uid"])["dashboard"]
