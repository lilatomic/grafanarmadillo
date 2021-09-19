from collections import defaultdict
import random
import string
from typing import Any, Dict
import time

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for

class GrafanaContainer(DockerContainer):
	_PORT = 3000
	_ADMIN = "admin"
	_ADMIN_PASSWORD = ''.join(random.SystemRandom().choices(string.printable, k=32))


	def __init__(self, image="grafana/grafana:latest", port=_PORT, admin_password: str = _ADMIN_PASSWORD, config_overrides: Dict[str, Dict[str, Any]] = None, **kwargs):
		super().__init__(image, **kwargs)
		self.conf = defaultdict(dict)
		# port
		self.with_bind_ports(port, 3000)
		self._set_grafana_conf("server", "http_port", port)
		self._set_grafana_conf("security", "admin_password", admin_password)

		if config_overrides:
			self.conf.update(config_overrides)

		self._apply_grafana_conf()

	def _set_grafana_conf(self, section: str, key: str, value: Any):
		self.conf[section][key] = value

	def _apply_grafana_conf(self):
		for section, items in self.conf.items():
			for item, value in items.items():
				self.with_env(
					"_".join(["GF", section.upper(), item.upper()]),
					str(value)
				)

	def _try_connecting(self)->bool:
		requests.get(self.url)

	@property
	def url(self):
		return f"http://localhost:{self.conf['server']['http_port']}/"

	@property
	def api(self):
		return self.url + "api/"

	def start(self):
		ret =  super().start()
		wait_for(self._try_connecting)
		return ret


@pytest.fixture
def readonly_grafana():

	with GrafanaContainer() as gfn:
		yield gfn