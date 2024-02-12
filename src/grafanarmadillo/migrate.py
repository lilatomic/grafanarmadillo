"""Migrate from Classic to Unified alerting."""
import contextlib
import datetime
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import docker
import requests
from docker.models.containers import Container

from grafanarmadillo.bulk import BulkExporter


@dataclass
class DockerContainer:
	"""Handle on a docker container."""

	container: Container
	image: str
	host_port: int

	@property
	def status(self):
		"""Get the status of the docker container."""
		return self.container.status


def start_container(image_name, volume_path: Path, environment_vars: Dict[str, str]):
	"""Start a container."""
	client = docker.from_env()
	volumes = {str(volume_path): {"bind": "/var/lib/grafana/grafana.db", "mode": "rw"}}
	container = client.containers.run(
		image_name,
		detach=True,
		ports={"3000/tcp": 0},
		volumes=volumes,
		environment=environment_vars,
	)
	container.reload()
	host_port = container.attrs["NetworkSettings"]["Ports"]["3000/tcp"][0]["HostPort"]
	return DockerContainer(container, image_name, int(host_port))


def read_container_logs(container: DockerContainer):
	"""Read logs from the docker container."""
	return container.container.logs().decode("utf-8")


def stop_container(container: DockerContainer):
	"""Stop container."""
	container.container.stop()


def exec_in_container(container: DockerContainer, command: str):
	"""Execute a command in a running docker container."""
	result = container.container.exec_run(command)
	return result.output.decode("utf-8").strip()


@contextlib.contextmanager
def with_container(image_name, volume_path: Path, environment_vars: Dict[str, str]):
	"""Context manager for Grafana docker container."""
	container = start_container(image_name, volume_path, environment_vars)
	try:
		yield container
	finally:
		stop_container(container)


DEFAULT_TIMEOUT = datetime.timedelta(seconds=30)


def _wait_until_ready(
	container: DockerContainer,
	timeout: datetime.timedelta = DEFAULT_TIMEOUT,
):
	"""Wait until container's readiness check passes."""
	end = datetime.datetime.now() + timeout
	while True:
		if datetime.datetime.now() > end:
			raise RuntimeError(
				f"Could not connect to container in {timeout} logs={read_container_logs(container)}"
			)
		try:
			if requests.get(f"http://localhost:{container.host_port}/api/health").ok:
				break
		except (
			ConnectionError,
			requests.exceptions.ConnectionError,
			requests.exceptions.HTTPError,
		):
			pass


def migrate(
	grafana_image,
	grafana_db: Path,
	output_directory: Path,
	extra_env_vars: Dict[str, str] = None,
) -> None:
	"""Migrate from classic to Unified alerting."""
	extra_env_vars = extra_env_vars or {}

	backup_db = grafana_db.with_name("backup.sqlite3").absolute()
	shutil.copyfile(grafana_db, backup_db)

	with with_container(grafana_image, grafana_db, extra_env_vars) as container:
		if container.status != "running":
			raise RuntimeError(f"Could not start Grafana container {container=}")

		_wait_until_ready(container)

		exporter = BulkExporter(
			{
				"host": "localhost",
				"port": container.host_port,
				"auth": ("admin", "admin"),
			},
			output_directory,
		)

		exporter.run()
