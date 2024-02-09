"""Migrate from Classic to Unified alerting"""
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import sleep

import docker
from typing import Dict

from docker.models.containers import Container
from grafana_client.client import GrafanaException


@dataclass
class DockerContainer:
	container: Container
	image: str
	host_port: int

	@property
	def status(self):
		return self.container.status

def start_container(image_name, volume_path: Path, environment_vars: Dict[str, str]):
	client = docker.from_env()
	volumes = {str(volume_path): {'bind': '/var/lib/grafana/grafana.db', 'mode': 'rw'}}
	container = client.containers.run(image_name, detach=True, ports={'3000/tcp': 3000}, volumes=volumes, environment=environment_vars)
	container.reload()
	host_port = container.attrs['NetworkSettings']['Ports']['3000/tcp'][0]['HostPort']
	return DockerContainer(container, image_name, int(host_port))

def read_container_logs(container: DockerContainer):
	return container.container.logs().decode('utf-8')

def stop_container(container: DockerContainer):
	container.container.stop()


def migrate(grafana_image, grafana_db: Path, extra_env_vars: Dict[str, str]) -> None:
	"""Migrate from classic to Unified alerting"""
	new_grafana_db = grafana_db.with_name("migrated.sqlite3").absolute()
	shutil.copyfile(grafana_db, new_grafana_db)

	container = start_container(grafana_image, new_grafana_db, extra_env_vars)

	if container.status != "running":
		raise RuntimeError(f"Could not start Grafana container {container=}")

	sleep(5)
	print(read_container_logs(container))
	print(f"{container.host_port=}")
	sleep(300)


	stop_container(container)


