import json
import os
import platform
import random
import socket
import string
from collections import defaultdict
from typing import Any, Dict, Tuple

import pytest
import requests
from grafana_api.grafana_face import GrafanaFace
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for

from grafanarmadillo._util import erase_dashboard_identity
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder


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
		image,
		port=_PORT,
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
		except requests.exceptions.ConnectionError as e:
			raise ConnectionError from e

	@property
	def url(self):
		return f"http://localhost:{self.conf['server']['http_port']}/"

	@property
	def api(self):
		return self.url + "api/"

	def start(self):
		ret = super().start()
		wait_for(self._try_connecting)
		return ret


def read_json_file(filename: str):
	with open(os.path.join("tests", filename), "r") as f:
		return json.load(f)


def create_dashboard(gfn: GrafanaFace, name, folderId=0):
	dashboard = read_json_file("dashboard.json")
	dashboard = erase_dashboard_identity(dashboard)
	dashboard["title"] = name
	return gfn.dashboard.update_dashboard(
		dashboard={"dashboard": dashboard, "overwrite": True, "folderId": folderId}
	)


def create_folder(gfn: GrafanaFace, name, uid=None):
	return gfn.folder.create_folder(name, uid)


@pytest.fixture(scope="module")
def grafana_image():
	yield "grafana/grafana:8.5.9"


@pytest.fixture
def grafana(grafana_image):
	with GrafanaContainer(grafana_image) as gfn_ctn:
		yield gfn_ctn


@pytest.fixture(scope="module")
def ro_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaFace]:
	"""
	Create a fixture of a grafana instance with many dashboards.

	Readonly, please don't modify this instance
	"""
	__skip_container_test_if_necessary()
	yield from mk_demo_grafana(grafana_image)


@pytest.fixture()
def rw_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaFace]:
	"""
	Create a fixture of a grafana instance with many dashboards.

	Readwrite, feel free to modify this instance
	"""
	__skip_container_test_if_necessary()
	yield from mk_demo_grafana(grafana_image)


@pytest.fixture(scope="module")
def rw_shared_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaFace]:
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


def mk_demo_grafana(grafana_image) -> Tuple[GrafanaContainer, GrafanaFace]:
	def get_free_tcp_port():
		tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp.bind(("", 0))
		tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		addr, port = tcp.getsockname()
		tcp.close()
		return port

	with GrafanaContainer(image=grafana_image, port=get_free_tcp_port()) as gfn_ctn:
		gfn = GrafanaFace(
			auth=(
				gfn_ctn.conf["security"]["admin_user"],
				gfn_ctn.conf["security"]["admin_password"],
			),
			port=gfn_ctn.conf["server"]["http_port"],
		)

		gfn.datasource.create_datasource(read_json_file("datasource.json"))

		create_dashboard(gfn, "0", 0)
		f0 = create_folder(gfn, "f0")
		create_dashboard(gfn, "f0-0", f0["id"])

		create_folder(gfn, "f0_similar")

		yield gfn_ctn, gfn


@pytest.fixture
def ro_dashboarder(ro_demo_grafana) -> Dashboarder:
	return Dashboarder(ro_demo_grafana[1])


@pytest.fixture
def ro_finder(ro_demo_grafana) -> Dashboarder:
	return Finder(ro_demo_grafana[1])


# Marks container tests

container_fixtures = set(
	map(lambda f: f.__name__, [grafana, ro_demo_grafana, ro_dashboarder, ro_finder])
)


def pytest_collection_modifyitems(items):
	for item in items:
		fixtures = set(getattr(item, "fixturenames", ()))
		if container_fixtures & fixtures:
			item.add_marker("containertest")


@pytest.fixture()
def unique():
	import uuid

	yield str(uuid.uuid4())
