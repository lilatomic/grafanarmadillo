"""Tests for templators that require integration."""
from dataclasses import dataclass
from typing import Any

from grafana_client.client import GrafanaClientError

from grafanarmadillo.templator import alert_dashboarduid_templator
from grafanarmadillo.types import GrafanaPath
from tests.conftest import read_json_file


@dataclass
class MockFinder:
	"""Fake finder."""

	result: Any
	args: Any = None

	def val(self, *args):
		self.args = args
		if isinstance(self.result, Exception):
			raise self.result
		else:
			return self.result

	def get_dashboard_by_uid(self, uid):
		return self.val()

	def create_or_get_dashboard(self, path):
		return self.val()


class TestAlertDashboardUid:
	"""Test alert_dashboarduid_templator."""

	def test_uid2ref__not_found(self):
		t = alert_dashboarduid_templator(MockFinder(GrafanaClientError(404, "", "")))

		alert = read_json_file("alert_rule.json")
		template = t.make_template(alert)

		assert template["annotations"]["__dashboardUid__"] == alert["annotations"]["__dashboardUid__"], "when dashboard uid could not be found, the uid was not preserved"

	def test_uid2ref__found(self):
		t = alert_dashboarduid_templator(MockFinder(GrafanaPath("test/name", "test+folder")))

		alert = read_json_file("alert_rule.json")
		template = t.make_template(alert)

		assert template["annotations"]["__dashboardUid__"] == "$$test%2Bfolder/test%2Fname", "when dashboard uid was found it was not replaced by the corresponding reference"

	def test_ref2uid__nonmangled(self):
		t = alert_dashboarduid_templator(MockFinder(RuntimeError("should not have been invoked")))

		alert = read_json_file("alert_rule.json")
		template = t.fill_template(alert)

		assert template["annotations"]["__dashboardUid__"] == alert["annotations"]["__dashboardUid__"], "when dashboard uid was not a ref, the uid was not preserved"

	def test_ref2uid__present(self):
		t = alert_dashboarduid_templator(MockFinder(({"uid": "testuid"}, {})))

		alert = read_json_file("alert_rule.json")
		alert["annotations"]["__dashboardUid__"] = "$$testfolder/testname"
		template = t.fill_template(alert)

		assert template["annotations"]["__dashboardUid__"] == "testuid", "when dashboard uid was a ref, the uid was dereferenced"
