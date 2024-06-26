import json
import logging
import os
from pathlib import Path

from click.testing import CliRunner
from grafana_client import GrafanaApi

from grafanarmadillo.cmd import grafanarmadillo
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.migrate import _wait_until_ready, with_container
from grafanarmadillo.paths import PathCodec
from tests.conftest import read_json_file


def test_cli__migrator(tmp_path: Path, caplog):
	caplog.set_level(logging.DEBUG)
	folder_name = "f0"

	def init_db_file(path: Path) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.touch(exist_ok=True)
		os.chmod(path, 0o666)
		if os.getenv("GITHUB_ACTIONS"):
			import subprocess

			subprocess.run(["sudo", "chown", "472", path.as_posix()])

	legacy_db_path = tmp_path / "legacy" / "grafana_legacy.db"
	init_db_file(legacy_db_path)
	migrated_db_path = legacy_db_path.with_name("migrated")
	init_db_file(migrated_db_path)  # shim to change file permissions so later copy works

	ds_uid = "nfke3J2Sz"
	mapping_args = [
		"--mapping",
		json.dumps({"e": {"ds_uid": ds_uid}}),
		"--env-grafana=e",
		"--env-template=$auto"
	]

	unified_db_path = tmp_path / "unified" / "grafana_unified.db"
	init_db_file(unified_db_path)
	with with_container(
		"grafana/grafana:8.5.27",
		legacy_db_path,
		{"GF_UNIFIED_ALERTING_ENABLED": "false", "GF_ALERTING_ENABLED": "true"},
	) as grafana_legacy:
		(tmp_path / "unified").parent.mkdir(parents=True, exist_ok=True)

		# Add dashboard with legacy alert to legacy Grafana
		_wait_until_ready(grafana_legacy)

		gfn_legacy = GrafanaApi(
			host="localhost", port=grafana_legacy.host_port, auth=("admin", "admin")
		)
		dashboarder_legacy, finder_legacy = Dashboarder(gfn_legacy), Finder(gfn_legacy)
		legacy_dashboard = read_json_file("legacy_alert_dashboard.json")
		folder = finder_legacy.create_or_get_folder(folder_name)
		gfn_legacy.datasource.create_datasource(
			{
				"name": "test_datasource",
				"type": "graphite",
				"url": "http://mydatasource.com",
				"access": "proxy",
				"basicAuth": False,
				"uid": ds_uid,
			}
		)

		dashboarder_legacy.import_dashboard(legacy_dashboard, folder)

	# Run migration
	runner = CliRunner()
	output_path = tmp_path / "output"
	output_path.mkdir(parents=True, exist_ok=True)
	result = runner.invoke(
		grafanarmadillo,
		[
			"--cfg",
			json.dumps({"auth": ["admin", "admin"]}),
			"migrate",
			"upgrade-alerting",
			"--grafana-db-path",
			legacy_db_path,
			"-o",
			output_path,
			*mapping_args
		],
	)

	# Check migrate exported things
	try:
		assert result.exit_code == 0
		assert len(list((output_path / "dashboards").rglob("*.json"))) == 1
		assert len(list((output_path / "alerts").rglob("*.json"))) == 1
		with (output_path / "dashboards" / PathCodec.encode(["Main Org.", folder_name, "New dashboard (1/1)"])).with_suffix(".json").open() as f:
			assert "${ds_uid}" in f.read(), "templating didn't happen in export"
	except AssertionError:
		print(f"{result.output=}")
		if result.exception:
			print(f"{result.exception=}")
			raise result.exception
		else:
			raise

	with with_container(
		"grafana/grafana:10.4.3", unified_db_path, {}
	) as grafana_unified:
		# Import into new Grafana
		_wait_until_ready(grafana_unified)

		gfn_unified = GrafanaApi(
			host="localhost", port=grafana_unified.host_port, auth=("admin", "admin")
		)
		gfn_unified.datasource.create_datasource(
			{
				"name": "test_datasource",
				"type": "graphite",
				"url": "http://mydatasource.com",
				"access": "proxy",
				"basicAuth": False,
				"uid": ds_uid,
			}
		)

		result2 = runner.invoke(
			grafanarmadillo,
			[
				"-c",
				json.dumps(
					{
						"host": "localhost",
						"port": grafana_unified.host_port,
						"auth": ("admin", "admin"),
					}
				),
				"resources",
				"import",
				"--root-directory",
				output_path,
				*mapping_args
			],
		)
		try:
			assert result2.exit_code == 0
			finder_unified = Finder(gfn_unified)
			assert len(finder_unified.list_dashboards()) == 1
			assert len(finder_unified.list_alerts()) == 1
		except AssertionError:
			print(f"{result2.output=}")
			if result2.exception:
				print(f"{result2.exception=}")
				raise result2.exception
			else:
				raise
