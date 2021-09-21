"""Find Grafana dashboards and folders."""

from pathlib import PurePath
from typing import List, Tuple

from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo._util import exactly_one, flat_map
from grafanarmadillo.types import DashboardSearchResult, FolderSearchResult


class Finder(object):
	"""Collection of methods for finding Grafana dashboards and folders."""

	def __init__(self, api: GrafanaFace) -> None:
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
				list(
					filter(
						lambda x: x["title"] == name,
						map(lambda sr: self.api.folder.get_folder(sr["uid"]), search_result),
					)
				)
			)

	def get_dashboard(self, folder_name, dashboard_name) -> DashboardSearchResult:
		"""
		Get a dashboard by its parent folder and dashboard name.

		Dashboards without a parent are children of the "General" folder.
		"""
		folder_object = self.get_folder(folder_name)
		dashboards = self._enumerate_dashboards_in_folders([str(folder_object["id"])])
		return exactly_one(list(filter(lambda d: d["title"] == dashboard_name, dashboards)))

	def _resolve_path(self, path) -> Tuple[str, str]:
		parts = PurePath(path).parts

		# validate path
		if len(parts) > 3:
			# can support maximally ("/", "folder", "dashboard")
			raise ValueError("Dashboard path has too many parts")
		if PurePath(path).is_absolute() or parts[0] == "/" or parts[0] == "\\":
			# removes optional "absolurte" signifier
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
