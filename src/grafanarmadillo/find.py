"""Find Grafana dashboards and folders."""

from pathlib import PurePath
from typing import List, Optional, Tuple, Union

from grafana_client import GrafanaApi

from grafanarmadillo.types import (
	AlertSearchResult,
	DashboardSearchResult,
	FolderSearchResult,
)
from grafanarmadillo.util import exactly_one


def _query_message(query_type: str, query: str) -> str:
	"""Format a message detailing the query."""
	return f"type={query_type}, query={query}"


class Finder:
	"""Collection of methods for finding Grafana dashboards and folders."""

	def __init__(self, api: GrafanaApi) -> None:
		super().__init__()
		self.api = api

	def list_dashboards(self) -> List[DashboardSearchResult]:
		"""List all dashboards."""
		return self.api.search.search_dashboards(type_="dash-db")

	def list_alerts(self) -> List[AlertSearchResult]:
		"""List all alerts."""
		return self.api.alertingprovisioning.get_alertrules_all()

	def find_dashboards(self, name: str) -> List[DashboardSearchResult]:
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

	def get_dashboards_in_folders(self, folder_names: List[str]) -> List[DashboardSearchResult]:
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

	def create_or_get_folder(self, name: str) -> FolderSearchResult:
		"""
		Create a new folder if it does not exist.

		Returns the search information if it does.
		"""
		try:
			folder = self.get_folder(name)
		except ValueError:
			folder = self.api.folder.create_folder(name)
		return folder

	def get_dashboard(self, folder_name: str, dashboard_name: str) -> DashboardSearchResult:
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

	def get_from_path(self, path) -> Union[DashboardSearchResult, AlertSearchResult]:
		"""Get a dashboard from a string path like `/folder0/dashboard0`."""
		folder, dashboard = self._resolve_path(path)
		return self.get_dashboard(folder, dashboard)

	def get_alert_from_path(self, path) -> AlertSearchResult:
		"""Get an alert from a string path like `/folder0/alert0`."""
		folder, alert = self._resolve_path(path)
		return self.get_alert(folder, alert)

	def create_or_get_dashboard(self, path: str) -> Tuple[DashboardSearchResult, Optional[FolderSearchResult]]:
		"""
		Create a new empty dashboard if it does not exist.
		
		Returns the search information if it does
		"""
		folder_name, dashboard_name = self._resolve_path(path)

		folder = self.create_or_get_folder(folder_name)

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
		Get the information about an alert or create a new "empty" alert if it does not exist.

		Creating an "empty" alert in Grafana requires filling in a rule.
		We can fake that with a `math` rule that always returns 0.
		"""
		folder_name, alert_name = self._resolve_path(path)

		folder = self.create_or_get_folder(folder_name)

		try:
			alert = self.get_alert(folder_name, alert_name)
		except ValueError:
			self.api.alertingprovisioning.create_alertrule(self._mk_null_alert(folder["uid"], alert_name), disable_provenance=True)
			alert = self.get_alert(folder_name, alert_name)

		return alert, folder

	def _mk_null_alert(self, folder_uid: str, title: str) -> dict:
		"""Fill in the minimum boilerplate for Grafana to let us create an alert."""
		return {
			"title": title,
			"folderUID": folder_uid,
			"condition": "A",
			"ruleGroup": "grafanarmadillo_tmp",
			"data": [
				{
					"refId": "A",
					"relativeTimeRange": {
						"from": 0,
						"to": 0
					},
					"datasourceUid": "__expr__",
					"model": {
						"conditions": [
							{
								"evaluator": {
									"params": [
										0,
										0
									],
									"type": "gt"
								},
								"operator": {
									"type": "and"
								},
								"query": {
									"params": []
								},
								"reducer": {
									"params": [],
									"type": "avg"
								},
								"type": "query"
							}
						],
						"datasource": {
							"name": "Expression",
							"type": "__expr__",
							"uid": "__expr__"
						},
						"expression": "0",
						"intervalMs": 1000000,
						"maxDataPoints": 43200,
						"refId": "A",
						"type": "math"
					}
				}
			],
			"noDataState": "NoData",
			"execErrState": "Error",
			"for": "5m",
			"isPaused": False
		}
