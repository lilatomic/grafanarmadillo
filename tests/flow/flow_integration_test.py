import os
import shutil
from pathlib import Path

import pytest

from grafanarmadillo.cmd import load_data, make_mapping_templator
from grafanarmadillo.flow import Dashboard, FileStore, GrafanaStore, Flow, Alert
from tests.conftest import requires_alerting


@pytest.fixture
def mapping():
	return load_data("file://tests/cli/mapping.json")


def test_flow__dashboard(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)

	def mk_flow(filestore, grafanastore, templator):
		return Flow([
			Dashboard(
				name="/flow/fi-d0",
				tmpl=filestore,
				templator=templator,
				obj=grafanastore
			)
		])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-d0.json").exists()

def test_flow__alert(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)
	requires_alerting(rw_shared_grafana)

	def mk_flow(filestore, grafanastore, templator):
		return Flow([
			Alert(
				name="/flow/fi-a0",
				tmpl=filestore,
				templator=templator,
				obj=grafanastore
			)
		])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-a0.json").exists()


def test_flow__mixed(rw_shared_grafana, mapping, tmpdir):
	tmpdir = Path(tmpdir)
	requires_alerting(rw_shared_grafana)

	def mk_flow(filestore, grafanastore, templator):
		return Flow([
			Dashboard(
				name="/flow/fi-d0",
				tmpl=filestore,
				templator=templator,
				obj=grafanastore
			),
			Alert(
				name="/flow/fi-a0",
				tmpl=filestore,
				templator=templator,
				obj=grafanastore
			)
		])

	_do_flow_test(mapping, mk_flow, rw_shared_grafana, tmpdir)

	assert (tmpdir / "flow" / "fi-a0.json").exists()
	assert (tmpdir / "flow" / "fi-d0.json").exists()


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
