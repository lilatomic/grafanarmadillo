import json
import os
import random
import string
from collections import defaultdict
from typing import Any, Dict, Tuple

import pytest
import requests
from grafana_api.grafana_face import GrafanaFace
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for


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
		image="grafana/grafana:latest",
		port=_PORT,
		admin_user: str = _ADMIN_USER,
		admin_password: str = _ADMIN_PASSWORD,
		config_overrides: Dict[str, Dict[str, Any]] = None,
		**kwargs,
	):
		super().__init__(image, **kwargs)
		self.conf = defaultdict(dict)
		# port
		self.with_bind_ports(port, 3000)
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
		requests.get(self.url)

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
	dashboard["title"] = name
	return gfn.dashboard.update_dashboard(
		dashboard={"dashboard": dashboard, "overwrite": True, "folderId": folderId}
	)


def create_folder(gfn: GrafanaFace, name, uid=None):
	return gfn.folder.create_folder(name, uid)


@pytest.fixture
def grafana():
	with GrafanaContainer() as gfn_ctn:
		yield gfn_ctn


@pytest.fixture(scope="module")
def ro_demo_grafana() -> Tuple[GrafanaContainer, GrafanaFace]:
	"""Create a fixture of a grafana instance with many dashboards."""
	with GrafanaContainer() as gfn_ctn:
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
