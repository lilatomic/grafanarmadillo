"""Find Grafana dashboards and folders"""

from typing import Dict, List
from grafana_api.grafana_face import GrafanaFace

Dashboard = type
Folder = type


class Finder(object):
	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboards(self, name, folder_ids=None) -> List[Dashboard]:
		return self.api.search.search_dashboards(query=name, type_="dash-db", folder_ids=folder_ids)

	def get_folders(self, name) -> List[Folder]:
		if name == "General":
			return [self.api.folder.get_folder_by_id(0)]
		else:
			search_result = self.api.search.search_dashboards(query=name, type_="dash-folder")
			return list(map(lambda sr: self.api.folder.get_folder(sr["uid"]), search_result))
