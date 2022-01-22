import json
from uuid import UUID, uuid5

from grafana_api import GrafanaFace
from grafana_api.grafana_api import GrafanaClientError

from grafanarmadillo._util import extract_datasource_pk
from grafanarmadillo.types import DatasourceInfo


class Datasourcer(object):
	"""Collection of methods for managing datasources."""

	_UUID5_NS = UUID("eda3055a-6502-4701-990e-b5db7570372f")  # UUID5 requires a namespace

	def __init__(self, api: GrafanaFace, _uuid5_ns: UUID = _UUID5_NS) -> None:
		super().__init__()
		self.api = api
		self._uuid5_ns = _uuid5_ns

	def put(self, dsinfo):
		"""
		Put a datasource, recomputing the uid
		"""
		target = self.datsource_uuid(dsinfo)
		ds = dsinfo.copy()
		ds["uid"] = target
		if "version" in ds:
			del ds["version"]

		try:
			existing = self.api.datasource.get_datasource_by_name(ds["name"])
			target_id = existing["id"]
			return self.api.datasource.update_datasource(target_id, ds)
		except GrafanaClientError as e:
			if e.status_code == 404:
				return self.api.datasource.create_datasource(ds)
			else:
				raise

	def get(self, dsinfo: DatasourceInfo):
		"""Get a datasource"""
		target = self.datsource_uuid(dsinfo)

		print(target)
		return self.api.datasource.api.GET("/datasources/uid/%s" % target)

	def datsource_uuid(self, ds: DatasourceInfo) -> str:
		dumped = json.dumps(extract_datasource_pk(ds), sort_keys=True)
		return str(uuid5(self._uuid5_ns, dumped))
