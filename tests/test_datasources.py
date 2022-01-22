from grafanarmadillo._util import project_dict
from grafanarmadillo.datasourcer import Datasourcer
from tests.conftest import read_json_file


class TestDatasources:
	@staticmethod
	def config_fields(d):
		return project_dict(d, {"id", "uid", "version"}, inverse=True)

	def test_put_datasource__new(self, rw_shared_grafana, unique):
		"""Test that Datasourcer.put can create a new datasource"""
		api = rw_shared_grafana[1]
		datasourcer = Datasourcer(api)

		dsinfo = read_json_file("datasource.json")
		del dsinfo["uid"]
		dsinfo["name"] = unique
		datasourcer.put(dsinfo)

		actual = api.datasource.get_datasource_by_name(unique)
		assert actual["uid"] == datasourcer.datsource_uuid(dsinfo)
		assert self.config_fields(actual) == self.config_fields(dsinfo)

	def test_put_datasource__existing(self, rw_shared_grafana, unique):
		"""Test that Datasourcer.put can update an existing datasource"""
		api = rw_shared_grafana[1]
		datasourcer = Datasourcer(api)

		dsinfo = read_json_file("datasource.json")
		del dsinfo["uid"]
		dsinfo["name"] = unique
		datasourcer.put(dsinfo)

		changed_dsinfo = dsinfo.copy()
		changed_dsinfo["type"] = "modified"
		datasourcer.put(changed_dsinfo)

		actual = api.datasource.get_datasource_by_name(unique)
		assert actual["uid"] == datasourcer.datsource_uuid(dsinfo)
		assert self.config_fields(actual) != self.config_fields(dsinfo)
		assert self.config_fields(actual) == self.config_fields(changed_dsinfo)

	def test_get_datasource(self, rw_shared_grafana, unique):
		api = rw_shared_grafana[1]
		datasourcer = Datasourcer(api)

		name = unique[:8]  # just to make sure that we're not dependent on the name

		dsinfo = read_json_file("datasource.json")
		dsinfo["name"] = name

		uid = datasourcer.datsource_uuid(dsinfo)
		dsinfo["uid"] = uid
		api.datasource.create_datasource(dsinfo)
		# ---
		result = datasourcer.get({"name": name})
		assert result["name"] == name
		assert result["uid"] == datasourcer.datsource_uuid(result)
