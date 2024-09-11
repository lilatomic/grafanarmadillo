import os
import shutil
import subprocess
from pathlib import Path

import pytest

from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.flow import (
	Alert,
	Dashboard,
	FileStore,
	Flow,
	FlowException,
	GrafanaStore, URLStore,
)
from grafanarmadillo.templator import make_mapping_templator, Templator, fill_grafana_templating_options
from grafanarmadillo.util import load_data
from tests.conftest import requires_alerting, set_cli_cfg


@pytest.fixture
def mapping():
	return load_data("file://tests/cli/mapping.json")


def test_flow__dashboard(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)

	def mk_flow(filestore, grafanastore, templator):
		return Flow(
			store_obj=grafanastore,
			store_tmpl=filestore,
			flows=[
				Dashboard(
					name_obj="/flow0/fi-d0",
					name_tmpl="/flow/fi-d0",
					templator=templator,
				)
			])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-d0.json").exists()


def test_flow__alert(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)
	requires_alerting(rw_shared_grafana)

	def mk_flow(filestore, grafanastore, templator):
		return Flow(
			store_obj=grafanastore,
			store_tmpl=filestore,
			flows=[
				Alert(
					name_obj="/flow1/fi-a0",
					name_tmpl="/flow/fi-a0",
					templator=templator,
				)
			])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-a0.json").exists()


def test_flow__mixed(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)
	requires_alerting(rw_shared_grafana)

	def mk_flow(filestore, grafanastore, templator):
		return Flow(
			store_obj=grafanastore,
			store_tmpl=filestore,
			flows=[
				Dashboard(
					name_obj="/flow2/fi-d0",
					name_tmpl="/flow/fi-d0",
					templator=templator,
				),
				Alert(
					name_obj="/flow2/fi-a0",
					name_tmpl="/flow/fi-a0",
					templator=templator,
				)
			])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-a0.json").exists()
	assert (tmpdir / "flow" / "fi-d0.json").exists()


def test_flow__failure(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)

	def mk_flow(filestore, grafanastore, templator):
		return Flow(
			store_obj=grafanastore,
			store_tmpl=filestore,
			flows=[
				Dashboard(
					name_obj="/flow3/fi-d0",
					name_tmpl="/flow/fail",
					templator=templator,
				),
				Dashboard(
					name_obj="/flow3/fi-d0",
					name_tmpl="/flow/fi-d0",
					templator=templator,
				),
			])

	with pytest.raises(FlowException):
		_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-d0.json").exists()
	assert not (tmpdir / "flow" / "fail.json").exists()


def _do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir):
	os.mkdir(tmpdir / "flow")
	dst_d = shutil.copy("tests/dashboard.json", tmpdir / "flow" / "fi-d0.json")
	dst_a = shutil.copy("tests/alert_rule.json", tmpdir / "flow" / "fi-a0.json")
	filestore = FileStore(tmpdir)
	grafanastore = GrafanaStore(rw_shared_grafana[1])
	templator = make_mapping_templator(mapping, "prd", "template")
	flow = mk_flow(filestore, grafanastore, templator)
	r0 = flow.tmpl_to_obj()
	r0.raise_first()

	os.remove(dst_d)
	os.remove(dst_a)
	r1 = flow.obj_to_tmpl()
	r1.raise_first()


def test_usage_flow_cli(rw_shared_grafana, tmpdir):
	finder = Finder(rw_shared_grafana[1])
	finder.create_or_get_dashboard("/dev0/MySystem TEST")

	env_cfg = set_cli_cfg(rw_shared_grafana)

	subprocess.run(
		["python3", "tests/flow/example.py", "my-system", "export", f"--basedir={tmpdir}"],
		check=True,
		env=env_cfg,
		capture_output=True,
	)
	subprocess.run(
		["python3", "tests/flow/example.py", "my-system", "import", f"--basedir={tmpdir}"],
		check=True,
		env=env_cfg,
		capture_output=True,
	)

	for deployment in ["east", "west", "north"]:
		dashboard = finder.get_dashboard(f"{deployment}0", "my_system")
		assert dashboard


def test_flow__remote(rw_shared_grafana, unique, tmpdir):
	grafanastore = GrafanaStore(rw_shared_grafana[1])
	urlstore = URLStore()

	flow = Flow(
		store_obj=grafanastore,
		store_tmpl=urlstore,
		flows=[
			Dashboard(
				name_obj=f"/{unique}/MySystem TEST",
				name_tmpl="https://grafana.com/api/dashboards/14900/revisions/2/download",
				templator=Templator(fill_template=fill_grafana_templating_options({"datasource": "my_datasource"})),
			),
		]
	)

	r0 = flow.tmpl_to_obj()
	r0.raise_first()

	finder, dashboarder = Finder(rw_shared_grafana[1]), Dashboarder(rw_shared_grafana[1])
	d = finder.get_dashboard(unique,"MySystem TEST")
	assert d, "did not find dashboard in grafana"

	d_content = dashboarder.get_dashboard_content(d)
	indexed_options = {e["name"]: e for e in d_content["templating"]["list"]}
	assert indexed_options["datasource"]["current"] == "my_datasource", "did not set templating option"
