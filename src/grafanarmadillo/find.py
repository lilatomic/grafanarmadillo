"""Find Grafana dashboards and folders"""

from typing import Dict, List
from grafana_api.grafana_face import GrafanaFace

from grafanarmadillo.util import flat_map

Dashboard = type
Folder = type


class Finder(object):
	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboards(self, name) -> List[Dashboard]:
		return list(filter(
			lambda x: x['title'] == name, 
			self.api.search.search_dashboards(query=name, type_="dash-db")
		))

	def _enumerate_dashboards_in_folders(self, folder_ids):
		return self.api.search.search_dashboards(query=None, type_="dash-db", folder_ids=folder_ids)

	def get_dashboards_in_folders(self, folders: List[str]) -> List[Dashboard]:
		folder_objects = flat_map(lambda folder_name: self.get_folders(name=folder_name), folders)
		folder_ids = ','.join(map(lambda f: str(f['id']), folder_objects))
		print(folder_ids)
		return self._enumerate_dashboards_in_folders(folder_ids)

	def get_folders(self, name) -> List[Folder]:
		if name == "General":
			return [self.api.folder.get_folder_by_id(0)]
		else:
			search_result = self.api.search.search_dashboards(query=name, type_="dash-folder")
			return list(map(lambda sr: self.api.folder.get_folder(sr["uid"]), search_result))
