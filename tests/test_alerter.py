import pytest

from grafanarmadillo._util import project_dict
from grafanarmadillo.alerter import Alerter
from grafanarmadillo.find import Finder
from tests.conftest import read_json_file


def test_import(rw_shared_grafana, unique):
	"""Test that we can import a dashboard."""
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))

	folder = finder.get_folder("f0")

	new_alert = read_json_file("alert_rule.json")
	del new_alert["id"]
	new_alert["uid"] = unique
	new_alert["ruleGroup"] = "ruleGroup " + unique
	new_alert["title"] = "title " + unique

	alerter.import_alert(new_alert, folder)

	result = alerter.api.alertingprovisioning.get_alertrule(unique)

	assert result["data"] == new_alert["data"]
	assert result["folderUID"] == folder["uid"]


def test_importexport__roundtrip(rw_shared_grafana, unique):
	"""Test that we can import a dashboard and the export is the same."""
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))

	folder_name = "f0"
	target_folder = finder.get_folder(folder_name)

	new_alert = read_json_file("alert_rule.json")
	del new_alert["id"]
	new_alert["uid"] = unique
	new_alert["ruleGroup"] = "ruleGroup " + unique
	new_alert["title"] = "title " + unique

	alerter.import_alert(new_alert, target_folder)

	alert_search_result = finder.get_alert(folder_name, "title " + unique)
	exported_alert, exported_folder = alerter.export_alert(alert_search_result)

	def coerce_comparable(a):
		noncomparables = {"id", "provenance", "folderUID", "updated"}
		return project_dict(a, noncomparables, inverse=True)

	assert coerce_comparable(exported_alert) == coerce_comparable(new_alert)

	assert target_folder["uid"] == exported_folder["uid"]
