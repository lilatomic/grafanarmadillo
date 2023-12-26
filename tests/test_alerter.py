import pytest

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.find import Finder
from grafanarmadillo.util import project_dict
from tests.conftest import read_json_file, requires_alerting


def uniquify_alert(alert, unique):
	alert.pop("id", None)
	alert["uid"] = unique
	alert["ruleGroup"] = "ruleGroup " + unique
	alert["title"] = "title " + unique

	return alert


def test_import(rw_shared_grafana, unique):
	"""Test that we can import a dashboard."""
	requires_alerting(rw_shared_grafana)

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))
	folder = finder.get_folder("f0")

	new_alert = uniquify_alert(read_json_file("alert_rule.json"), unique)

	alerter.import_alert(new_alert, folder)

	result = alerter.api.alertingprovisioning.get_alertrule(unique)
	assert result["data"] == new_alert["data"]
	assert result["folderUID"] == folder["uid"]


def test_import__just_content(rw_shared_grafana, unique):
	"""Test that an alert with uid removed can be imported."""
	requires_alerting(rw_shared_grafana)

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))
	folder = finder.get_folder("f0")

	new_alert = uniquify_alert(read_json_file("alert_rule.json"), unique)
	del new_alert["uid"]  # The important part

	alerter.import_alert(new_alert, folder)

	result = finder.get_alert("f0", "title " + unique)
	assert result["data"] == new_alert["data"]
	assert result["folderUID"] == folder["uid"]


def test_import__update(rw_shared_grafana, unique):
	"""Test that importing for an existing dashboard overwrite."""
	requires_alerting(rw_shared_grafana)

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))
	folder = finder.get_folder("f0")
	new_alert = uniquify_alert(read_json_file("alert_rule.json"), unique)
	alerter.import_alert(new_alert, folder)

	new_alert["isPaused"] = not new_alert["isPaused"]  # modify the alert
	alerter.import_alert(new_alert, folder)

	result = finder.get_alert("f0", "title " + unique)
	assert result["isPaused"] == new_alert["isPaused"]


def test_importexport__roundtrip(rw_shared_grafana, unique):
	"""Test that we can import a dashboard and the export is the same."""
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")

	finder, alerter = (Finder(rw_shared_grafana[1]), Alerter(rw_shared_grafana[1]))

	folder_name = "f0"
	target_folder = finder.get_folder(folder_name)

	new_alert = read_json_file("alert_rule.json")
	new_alert = uniquify_alert(new_alert, unique)

	alerter.import_alert(new_alert, target_folder)

	alert_search_result = finder.get_alert(folder_name, "title " + unique)
	exported_alert, exported_folder = alerter.export_alert(alert_search_result)

	def coerce_comparable(a):
		noncomparables = {"id", "provenance", "folderUID", "updated"}
		return project_dict(a, noncomparables, inverse=True)

	assert coerce_comparable(exported_alert) == coerce_comparable(new_alert)

	assert target_folder["uid"] == exported_folder["uid"]
