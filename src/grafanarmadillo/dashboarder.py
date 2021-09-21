"""Push and pull Grafana dashboards."""
from typing import Optional, Tuple

from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo._util import project_dashboard_identity
from grafanarmadillo.types import (
	DashboardContent,
	DashboardSearchResult,
	FolderSearchResult,
)


class Dashboarder(object):
	"""Collection of methods for managing dashboards."""

	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboard_content(self, dashboard: DashboardSearchResult) -> DashboardContent:
		"""Get the contents of a Grafana dashboard."""
		return self.api.dashboard.get_dashboard(dashboard["uid"])["dashboard"]

	def set_dashboard_content(
		self, dashboard: DashboardSearchResult, content: DashboardContent
	):
		"""
		Set the content of a Grafana dashboard.
		
		This explicitly leaves out the identity information.
		That allows you to graft the contents of a dashboard into another
		"""
		new_dashboard = dashboard.copy()
		new_content = content.copy()

		new_content.update(project_dashboard_identity(new_dashboard))

		new_dashboard.update({"dashboard": new_content, "overwrite": True})

		return self.api.dashboard.update_dashboard(new_dashboard)

	def import_dashboard(
		self, content: DashboardContent, folder: Optional[FolderSearchResult] = None
	):
		"""Import a dashboard into Grafana, optionally into a folder."""
		new_dashboard = {"dashboard": content, "overwrite": True}
		if folder:
			new_dashboard.update({"folderUid": folder["uid"], "folderId": folder["id"]})

		return self.api.dashboard.update_dashboard(new_dashboard)

	def export_dashboard(
		self, dashboard: DashboardSearchResult
	) -> Tuple[DashboardContent, Optional[FolderSearchResult]]:
		"""Export a dashboard from grafana, with its folder information if applicable."""
		result = self.api.dashboard.get_dashboard(dashboard["uid"])
		meta, dashboard = result["meta"], result["dashboard"]
		if meta["folderUid"]:
			folder = self.api.folder.get_folder(meta["folderUid"])
		else:
			folder = None

		return dashboard, folder
