import json
import os
import platform
import random
import socket
import string
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import pytest
import requests
from grafana_client import GrafanaApi
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.util import erase_alert_rule_identity, erase_dashboard_identity


class GrafanaContainer(DockerContainer):
	"""Grafana Test Container."""

	_PORT = 3000
	_ADMIN_USER = "admin"
	_ADMIN_PASSWORD = "".join(
		random.SystemRandom().choices(
			string.ascii_letters + string.digits + string.punctuation, k=32
		)
	)

	def __init__(
		self,
		image: str,
		port: int = _PORT,
		admin_user: str = _ADMIN_USER,
		admin_password: str = _ADMIN_PASSWORD,
		config_overrides: Dict[str, Dict[str, Any]] = None,
		**kwargs,
	):
		super().__init__(image, **kwargs)
		self.conf = defaultdict(dict)
		# port
		self.with_bind_ports(port, port)
		self._set_grafana_conf("server", "http_port", port)
		self._set_grafana_conf("security", "admin_password", admin_password)
		self._set_grafana_conf("security", "admin_user", admin_user)

		if config_overrides:
			self.conf.update(config_overrides)

		self._apply_grafana_conf()

	def _set_grafana_conf(self, section: str, key: str, value: Any):
		self.conf[section][key] = value

	def _apply_grafana_conf(self):
		for section, items in self.conf.items():
			for item, value in items.items():
				self.with_env("_".join(["GF", section.upper(), item.upper()]), str(value))

	def _try_connecting(self) -> bool:
		try:
			requests.get(self.url)
			return True
		except requests.exceptions.ConnectionError as e:
			raise ConnectionError from e

	@property
	def url(self):
		return f"http://localhost:{self.conf['server']['http_port']}/"

	@property
	def api(self):
		return self.url + "api/"

	@property
	def major_version(self):
		tag = self.image.split(':')[1]
		major = tag.split('.')[0]
		return int(major)

	def start(self):
		ret = super().start()
		wait_for(self._try_connecting)
		return ret


def read_json_file(filename: Union[str, Path]):
	if isinstance(filename, str):
		filename = Path(filename)

	if not filename.is_absolute():
		base = Path.cwd()
		if base.name != "tests":
			base = base / "tests"
		filename = base / filename
	with filename.open("r") as f:
		return json.load(f)


def requires_alerting(rw_shared_grafana):
	if rw_shared_grafana[0].major_version < 9:
		pytest.skip("Grafana does not support provisioning in version 8")


def create_dashboard(gfn: GrafanaApi, name: str, folder_id: int = 0):
	dashboard = read_json_file("dashboard.json")
	dashboard = erase_dashboard_identity(dashboard)
	dashboard["title"] = name
	return gfn.dashboard.update_dashboard(
		dashboard={"dashboard": dashboard, "overwrite": True, "folderId": folder_id}
	)


def create_alert(gfn: GrafanaApi, name: str):
	alert_rule = read_json_file("alert_rule.json")
	alert_rule = erase_alert_rule_identity(alert_rule)
	alert_rule["title"] = name
	return gfn.alertingprovisioning.create_alertrule(alert_rule, disable_provenance=True)


def create_folder(gfn: GrafanaApi, name: str, uid=None):
	return gfn.folder.create_folder(name, uid)


@pytest.fixture(scope="module", params=["8.5.27", "9.5.21", "10.4.8", "11.2.0"])
def grafana_image(request):
	yield f"grafana/grafana:{request.param}"


@pytest.fixture
def grafana(grafana_image):
	with GrafanaContainer(grafana_image) as gfn_ctn:
		yield gfn_ctn


@pytest.fixture(scope="module")
def ro_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaApi]:
	"""
	Create a fixture of a grafana instance with many dashboards.

	Readonly, please don't modify this instance
	"""
	__skip_container_test_if_necessary()
	yield from mk_demo_grafana(grafana_image)


@pytest.fixture()
def rw_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaApi]:
	"""
	Create a fixture of a grafana instance with many dashboards.

	Readwrite, feel free to modify this instance
	"""
	__skip_container_test_if_necessary()
	yield from mk_demo_grafana(grafana_image)


@pytest.fixture(scope="module")
def rw_shared_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaApi]:
	"""
	Create a fixture of a grafana instance with many dashboards.
	
	This readwrite instance is shared between tests,
	please use the `unique` fixture to not conflict with other tests
	"""
	__skip_container_test_if_necessary()
	yield from mk_demo_grafana(grafana_image)


def __skip_container_test_if_necessary() -> bool:
	if "do_containertest" in os.environ:
		should_do_containertest = bool(os.environ.get("do_containertest"))
	else:
		should_do_containertest = platform.system() == "Linux"
	if not should_do_containertest:
		pytest.skip("Platform isn't Linux and not 'do_containertest'")
	return should_do_containertest


def mk_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaApi]:
	def get_free_tcp_port():
		tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp.bind(("", 0))
		tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		addr, port = tcp.getsockname()
		tcp.close()
		return port

	with GrafanaContainer(image=grafana_image, port=get_free_tcp_port()) as gfn_ctn:
		gfn = GrafanaApi(
			auth=(
				gfn_ctn.conf["security"]["admin_user"],
				gfn_ctn.conf["security"]["admin_password"],
			),
			port=gfn_ctn.conf["server"]["http_port"],
		)

		gfn.datasource.create_datasource(read_json_file("datasource.json"))

		dashboard = create_dashboard(gfn, "0", 0)
		f0 = create_folder(gfn, "f0")
		create_dashboard(gfn, "f0-0", f0["id"])

		create_folder(gfn, "f0_similar")

		if gfn_ctn.major_version >= 9:
			# alert provisioning was introduced only with Grafana 9
			assert f0["title"] == "f0"
			alert = read_json_file("alert_rule.json")
			alert["folderUID"] = f0["uid"]
			alert["uid"] = str(uuid.uuid4())  # make this instance of the alert unique
			alert["annotations"]["__dashboardUid__"] = dashboard["uid"]  # make the alert point to the real dashboard
			gfn.alertingprovisioning.create_alertrule(alert, True)

		yield gfn_ctn, gfn


@pytest.fixture
def ro_dashboarder(ro_demo_grafana) -> Dashboarder:
	return Dashboarder(ro_demo_grafana[1])


@pytest.fixture
def ro_finder(ro_demo_grafana) -> Finder:
	return Finder(ro_demo_grafana[1])


@pytest.fixture
def ro_alerter(ro_demo_grafana) -> Alerter:
	return Alerter(ro_demo_grafana[1])


# Marks container tests

container_fixtures = set(
	map(lambda f: f.__name__, [grafana, ro_demo_grafana, ro_dashboarder, ro_finder])
)


def pytest_collection_modifyitems(items):
	for item in items:
		fixtures = set(getattr(item, "fixturenames", ()))
		if container_fixtures & fixtures:
			item.add_marker("containertest")


@pytest.fixture(scope="function")
def unique():
	yield str(uuid.uuid4())


def set_cli_cfg(rw_shared_grafana):
	grafanarmadillo_cfg = read_json_file("usage/grafana_cfg.json")
	# change to settings from our ephemeral container
	grafana_container_config = rw_shared_grafana[0].conf
	grafanarmadillo_cfg["port"] = grafana_container_config["server"]["http_port"]
	grafanarmadillo_cfg["auth"] = [
		grafana_container_config["security"]["admin_user"],
		grafana_container_config["security"]["admin_password"],
	]
	env_cfg = os.environ.copy()
	env_cfg["grafanarmadillo_cfg"] = json.dumps(grafanarmadillo_cfg)
	env_cfg["GRAFANARMADILLO_CFG"] = json.dumps(grafanarmadillo_cfg)
	return env_cfg
