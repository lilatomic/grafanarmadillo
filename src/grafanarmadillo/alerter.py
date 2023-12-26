"""Push and pull Grafana alerts."""
from typing import Optional, Tuple

from grafana_client import GrafanaApi
from grafana_client.client import GrafanaClientError

from grafanarmadillo.types import AlertContent, AlertSearchResult, FolderSearchResult


class Alerter:
	"""Collection of methods for managing alert rules."""

	def __init__(self, api: GrafanaApi, disable_provenance=True) -> None:
		super().__init__()
		self.api = api
		self.disable_provenance = disable_provenance

	def import_alert(
		self, content: AlertContent, folder: FolderSearchResult
	):
		"""Import an alert into Grafana."""
		content = content.copy()
		# set the folder in case it isn't, which would happen if the metadata was scrubbed from the alert content
		content["folderUID"] = folder["uid"]
		content.pop("id", None)

		try:
			if "uid" in content:
				exists = self.api.alertingprovisioning.get_alertrule(content["uid"])
			else:
				exists = None
		except GrafanaClientError as e:
			if e.status_code == 404:
				exists = None
			else:
				raise

		if exists:
			self.api.alertingprovisioning.update_alertrule(content["uid"], content, disable_provenance=self.disable_provenance)
		else:
			self.api.alertingprovisioning.create_alertrule(content, disable_provenance=self.disable_provenance)

	def export_alert(
		self, alert: AlertSearchResult
	) -> Tuple[AlertContent, Optional[FolderSearchResult]]:
		"""Export an alert from Grafana and its folder information too."""
		alert_content = self.api.alertingprovisioning.get_alertrule(alert["uid"])

		folder = self.api.folder.get_folder(alert_content["folderUID"])

		return alert_content, folder
