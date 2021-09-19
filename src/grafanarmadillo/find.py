"""Find Grafana dashboards and folders"""

from typing import Dict, List, Tuple
from grafana_api.api import folder
from grafana_api.grafana_face import GrafanaFace
from pathlib import PurePath

from grafanarmadillo.util import exactly_one, flat_map

Dashboard = type
Folder = type


class Finder(object):
	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def find_dashboards(self, name) -> List[Dashboard]:
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

	def get_dashboards_in_folders(self, folders: List[str]) -> List[Dashboard]:
		folder_objects = flat_map(
			lambda folder_name: self.get_folders(name=folder_name), folders
		)
		return self._enumerate_dashboards_in_folders(
			list(map(lambda f: str(f["id"]), folder_objects))
		)

	def get_folders(self, name) -> List[Folder]:
		if name == "General":
			return [self.api.folder.get_folder_by_id(0)]
		else:
			search_result = self.api.search.search_dashboards(query=name, type_="dash-folder")
			return list(
				filter(
					lambda x: x["title"] == name,
					map(lambda sr: self.api.folder.get_folder(sr["uid"]), search_result),
				)
			)

	def get_dashboard(self, folder_name, dashboard_name) -> Folder:
		folder_object = exactly_one(self.get_folders(folder_name))
		dashboards = self._enumerate_dashboards_in_folders([str(folder_object["id"])])
		return list(filter(lambda d: d["title"] == dashboard_name, dashboards))

	def _resolve_path(self, path) -> Tuple[str, str]:
		parts = PurePath(path).parts

		# validate path
		if len(parts) > 3:
			# can support maximally ("/", "folder", "dashboard")
			raise ValueError("Dashboard path has too many parts")
		if parts[0] == "/":
			# removes optional "absolurte" signifier
			parts = parts[1:]

		if len(parts) == 2:
			folder, dashboard = parts
		else:
			folder, dashboard = "General", parts[0]

		return folder, dashboard

	def get_from_path(self, path) -> Folder:
		""" Gets a dashboard from a string path like `/folder0/dashboard0` """
		folder, dashboard = self._resolve_path(path)
		return self.get_dashboard(folder, dashboard)