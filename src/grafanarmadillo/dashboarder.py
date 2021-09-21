from typing import Optional, Tuple
from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo.types import (
	DashboardSearchResult,
	DashboardContent,
	FolderSearchResult,
)
from grafanarmadillo._util import project_dashboard_identity


class Dashboarder(object):
	"""Collection of methods for managing dashboards"""

	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboard_content(self, dashboard: DashboardSearchResult) -> DashboardContent:
		return self.api.dashboard.get_dashboard(dashboard["uid"])["dashboard"]

	def set_dashboard_content(
		self, dashboard: DashboardSearchResult, content: DashboardContent
	):
		new_dashboard = dashboard.copy()
		new_content = content.copy()

		new_content.update(project_dashboard_identity(new_dashboard))

		new_dashboard.update({"dashboard": new_content, "overwrite": True})

		return self.api.dashboard.update_dashboard(new_dashboard)

	def import_dashboard(
		self, content: DashboardContent, folder: Optional[FolderSearchResult] = None
	):
		new_dashboard = {"dashboard": content, "overwrite": True}
		if folder:
			new_dashboard.update({"folderUid": folder["uid"], "folderId": folder["id"]})

		return self.api.dashboard.update_dashboard(new_dashboard)

	def export_dashboard(
		self, dashboard: DashboardSearchResult
	) -> Tuple[DashboardContent, Optional[FolderSearchResult]]:
		result = self.api.dashboard.get_dashboard(dashboard["uid"])
		meta, dashboard = result["meta"], result["dashboard"]
		if "folderUid" in meta:
			folder = self.api.folder.get_folder(meta["folderUid"])
		else:
			folder = None

		return dashboard, folder