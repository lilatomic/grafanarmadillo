import json

import pytest
from click.testing import CliRunner

from grafanarmadillo.cmd import grafanarmadillo
from grafanarmadillo.find import Finder
from tests.conftest import requires_alerting, read_json_file


@pytest.fixture
def cli_config(rw_shared_grafana):
	gfn = rw_shared_grafana[0]

	cfg = {
		"auth": [
			gfn.conf["security"]["admin_user"],
			gfn.conf["security"]["admin_password"],
		],
		"host": "localhost",
		"port": gfn.conf['server']['http_port'],
		"protocol": "http"
	}

	return cfg


def test_cli__import_dashboard(cli_config, rw_shared_grafana):
	runner = CliRunner()
	dashboard_path = "/f-c0/d-c0"
	result = runner.invoke(
		grafanarmadillo,
		[
			"--cfg",
			json.dumps(cli_config),
			"dashboard",
			"import",
			"--src",
			"tests/dashboard.json",
			"--dst",
			dashboard_path,
			"--env-template",
			"template",
			"--env-grafana",
			"prd",
			"--mapping",
			"file://tests/cli/mapping.json",
		]
	)
	assert result.exit_code == 0

	gfn = rw_shared_grafana[1]
	imported = Finder(gfn).get_from_path(dashboard_path)
	assert imported, "dashboard did not end up where we expected"
	dashboard = gfn.dashboard.get_dashboard(imported['uid'])
	assert "PRD" in dashboard["dashboard"]["tags"], "templating didn't replace the tag"


def test_cli__export_dashboard(cli_config, rw_shared_grafana, tmp_path):
	runner = CliRunner()
	template_path = tmp_path / "dashboard.json"
	result = runner.invoke(
		grafanarmadillo,
		[
			"--cfg",
			json.dumps(cli_config),
			"dashboard",
			"export",
			"--src",
			"/f0/f0-0",
			"--dst",
			template_path,
			"--env-grafana",
			"stg",
			"--env-template",
			"template",
			"--mapping",
			"file://tests/cli/mapping.json",
		]
	)
	assert result.exit_code == 0

	template = read_json_file(template_path)
	assert "$tag1" in template["tags"], "templating didn't replace the tag"


def test_cli__import_alert(cli_config, rw_shared_grafana):
	requires_alerting(rw_shared_grafana)

	runner = CliRunner()
	alert_path = "/f-c0/a-c0"
	result = runner.invoke(
		grafanarmadillo,
		[
			"--cfg",
			json.dumps(cli_config),
			"alert",
			"import",
			"--src",
			"tests/alert_rule.json",
			"--dst",
			alert_path,
			"--env-template",
			"template",
			"--env-grafana",
			"prd",
			"--mapping",
			"file://tests/cli/mapping.json",
		]
	)
	assert result.exit_code == 0

	gfn = rw_shared_grafana[1]
	imported = Finder(gfn).get_alert_from_path(alert_path)
	assert imported, "alert did not end up where we expected"
	alert = gfn.alertingprovisioning.get_alertrule(imported["uid"])
	assert "PRD" in alert["labels"].values()


def test_cli__export_alert(cli_config, rw_shared_grafana, tmp_path):
	requires_alerting(rw_shared_grafana)

	runner = CliRunner()
	template_path = tmp_path / "alert.json"
	result = runner.invoke(
		grafanarmadillo,
		[
			"--cfg",
			json.dumps(cli_config),
			"alert",
			"export",
			"--src",
			"/f0/a0",
			"--dst",
			template_path,
			"--env-grafana",
			"stg",
			"--env-template",
			"template",
			"--mapping",
			"file://tests/cli/mapping.json",
		]
	)
	if result.exit_code != 0:
		pytest.fail(result.output)

	template = read_json_file(template_path)
	assert "$tag1" in template["labels"].values()
