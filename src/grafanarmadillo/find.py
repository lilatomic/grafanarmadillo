"""Find Grafana dashboards and folders"""

Dashboard = type
Folder = type

from typing import List
from grafana_api.grafana_face import GrafanaFace

class Finder(object):
	def __init__(self, api: GrafanaFace) -> None:
		super().__init__()
		self.api = api

	def get_dashboards(self, name) -> List[Dashboard]:
		return self.api.search.search_dashboards(query=name, type_="dash-db")

	def get_folders(self, name) -> List[Folder]:
		return self.api.search.search_dashboards(query=name, type_="dash-folder")
