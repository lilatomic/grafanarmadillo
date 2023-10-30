"""Find Grafana dashboards and folders."""

from pathlib import PurePath
from typing import List, Optional, Tuple

from grafana_client import GrafanaApi

from grafanarmadillo._util import exactly_one
from grafanarmadillo.types import (
	AlertSearchResult,
	DashboardSearchResult,
	FolderSearchResult,
)


def _query_message(query_type: str, query: str) -> str:
	"""Format a message detailing the query."""
	return f"type={query_type}, query={query}"


class Finder:
	"""Collection of methods for finding Grafana dashboards and folders."""

	def __init__(self, api: GrafanaApi) -> None:
		super().__init__()
		self.api = api

	def find_dashboards(self, name) -> List[DashboardSearchResult]:
		"""Find all dashboards with a name. Returns exact matches only."""
		return list(
			filter(
				lambda x: x["title"] == name,
				self.api.search.search_dashboards(query=name, type_="dash-db"),
			)
		)

	def _enumerate_dashboards_in_folders(self, folder_ids: List[str]):
		folder_param = ",".join(folder_ids)
		return self.api.search.search_dashboards(
			query=None, type_="dash-db", folder_ids=folder_param
		)

	def get_dashboards_in_folders(
		self, folder_names: List[str]
	) -> List[DashboardSearchResult]:
		"""Get all dashboards in folders."""
		folder_objects = list(
			map(lambda folder_name: self.get_folder(name=folder_name), folder_names)
		)
		return self._enumerate_dashboards_in_folders(
			list(map(lambda f: str(f["id"]), folder_objects))
		)

	def get_folder(self, name) -> FolderSearchResult:
		"""Get a folder by name. Folders don't nest, so this will return at most 1 folder."""
		if name == "General":
			return self.api.folder.get_folder_by_id(0)
		else:
			search_result = self.api.search.search_dashboards(query=name, type_="dash-folder")
			return exactly_one(
				list(filter(
					lambda x: x["title"] == name,
					map(lambda sr: self.api.folder.get_folder(sr["uid"]), search_result),
				)),
				_query_message("folder", name),
			)

	def get_dashboard(self, folder_name, dashboard_name) -> DashboardSearchResult:
		"""
		Get a dashboard by its parent folder and dashboard name.

		Dashboards without a parent are children of the "General" folder.
		"""
		folder_object = self.get_folder(folder_name)
		dashboards = self._enumerate_dashboards_in_folders([str(folder_object["id"])])
		return exactly_one(
			list(filter(lambda d: d["title"] == dashboard_name, dashboards)),
			_query_message("dashboard", f"/{folder_name}/{dashboard_name}"),
		)

	def get_alert(self, folder_name, alert_name) -> AlertSearchResult:
		"""Get an alert by its parent folder and alert name."""
		folder_uid = self.get_folder(folder_name)["uid"]

		return exactly_one(
			list(filter(
				lambda a: a["title"] == alert_name and a["folderUID"] == folder_uid,
				self.api.alertingprovisioning.get_alertrules_all()
			)),
			_query_message("alert", f"/{folder_name}/{alert_name}")
		)

	@staticmethod
	def _resolve_path(path) -> Tuple[str, str]:
		parts = PurePath(path).parts

		# validate path
		if len(parts) > 3:
			# can support maximally ("/", "folder", "dashboard")
			raise ValueError("Dashboard path has too many parts")
		if PurePath(path).is_absolute() or parts[0] == "/" or parts[0] == "\\":
			# removes optional "absolute" signifier
			parts = parts[1:]

		if len(parts) == 2:
			folder, dashboard = parts
		else:
			folder, dashboard = "General", parts[0]

		return folder, dashboard

	def get_from_path(self, path) -> DashboardSearchResult:
		"""Get a dashboard from a string path like `/folder0/dashboard0`."""
		folder, dashboard = self._resolve_path(path)
		return self.get_dashboard(folder, dashboard)

	def get_alert_from_path(self, path) -> AlertSearchResult:
		"""Get an alert from a string path like `/folder0/alert0`."""
		folder, alert = self._resolve_path(path)
		return self.get_alert(folder, alert)

	def create_or_get_dashboard(
		self, path: str
	) -> Tuple[DashboardSearchResult, Optional[FolderSearchResult]]:
		"""
		Create a new empty dashboard if it does not exist.
		
		Returns the search information if it does
		"""
		folder_name, dashboard_name = self._resolve_path(path)

		try:
			folder = self.get_folder(folder_name)
		except ValueError:
			folder = self.api.folder.create_folder(folder_name)

		try:
			dashboard = self.get_dashboard(folder_name, dashboard_name)
		except ValueError:
			self.api.dashboard.update_dashboard(
				{
					"dashboard": {"title": dashboard_name},
					"folderId": folder["id"],
					"folderUid": folder["uid"],
				}
			)
			dashboard = self.get_dashboard(folder_name, dashboard_name)

		return dashboard, folder

	def create_or_get_alert(self, path: str) -> Tuple[AlertSearchResult, FolderSearchResult]:
		"""
		Get the information about an alert, or fake the metadata if it does not.

		Creating an "empty" alert in Grafana requires filling in much more data than an empty dashboard,
		including at least 1 rule.
		We can fake that with a `math` rule that always returns 0,
		but that's a lot of garbage data to inject.
		"""
		folder_name, alert_name = self._resolve_path(path)

		try:
			folder = self.get_folder(folder_name)
		except ValueError:
			folder = self.api.folder.create_folder(folder_name)

		try:
			alert = self.get_alert(folder_name, alert_name)
		except ValueError:
			alert = {
				"folderUID": folder["uid"],
				"title": alert_name
			}

		return alert, folder
