from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo.types import DashboardsearchResult, DashboardContent
from grafanarmadillo._util import project_dashboard_identity


class Dashboarder(object):
	"""Collection of methods for managing dashboards"""

	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboard_content(self, dashboard: DashboardsearchResult):
		return self.api.dashboard.get_dashboard(dashboard["uid"])["dashboard"]

	def set_dashboard_content(
		self, dashboard: DashboardsearchResult, content: DashboardContent
	):
		new_dashboard = dashboard.copy()
		new_content = content.copy()

		new_content.update(project_dashboard_identity(new_dashboard))

		print(new_dashboard)
		print(new_dashboard)

		new_dashboard.update({"dashboard": new_content, "overwrite": True})

		return self.api.dashboard.update_dashboard(new_dashboard)
