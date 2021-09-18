from collections import defaultdict
import random
import string
from typing import Any, Dict

import pytest
from testcontainers.core.container import DockerContainer

class GrafanaContainer(DockerContainer):
	_PORT = 3000
	_ADMIN = "admin"
	_ADMIN_PASSWORD = ''.join(random.SystemRandom().choices(string.printable, k=32))


	def __init__(self, image="grafana/grafana:latest", port=_PORT, admin_password: str = _ADMIN_PASSWORD, config_overrides: Dict[str, Dict[str, Any]] = None, **kwargs):
		super().__init__(image, **kwargs)
		self.conf = defaultdict(dict)
		# port
		self.with_exposed_ports(port)
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
				print(section, item)
				self.with_env(
					"_".join(["GF", section.upper(), item.upper()]),
					str(value)
				)

	
@pytest.fixture
def readonly_grafana():
	with GrafanaContainer() as gfn:
		yield gfn