"""Migrate from Classic to Unified alerting."""
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, Tuple

import docker
import requests
from docker.models.containers import Container
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder


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
	volumes = {str(volume_path): {'bind': '/var/lib/grafana/grafana.db', 'mode': 'rw'}}
	container = client.containers.run(
		image_name,
		detach=True,
		ports={'3000/tcp': 0},
		volumes=volumes,
		environment=environment_vars,
	)
	container.reload()
	host_port = container.attrs['NetworkSettings']['Ports']['3000/tcp'][0]['HostPort']
	return DockerContainer(container, image_name, int(host_port))


def read_container_logs(container: DockerContainer):
	"""Read logs from the docker container."""
	return container.container.logs().decode('utf-8')


def stop_container(container: DockerContainer):
	"""Stop container."""
	container.container.stop()


def _wait_until_ready(container: DockerContainer):
	"""Wait until container's readiness check passes."""
	while True:
		try:
			if requests.get(f"http://localhost:{container.host_port}/api/health").ok:
				break
		except (ConnectionError, requests.exceptions.ConnectionError):
			pass


def get_all_dashboards(org, gfn: GrafanaApi):
	"""Get all dashboards."""
	finder, dashboarder = Finder(gfn), Dashboarder(gfn)
	dashboards = finder.list_dashboards()
	for dashboard in dashboards:
		dashboard_content, folder = dashboarder.export_dashboard(dashboard)

		if folder is None:
			folder_name = "General"
		else:
			folder_name = folder["name"]

		out_path = Path(str(org["id"]), folder_name, dashboard_content["title"])

		yield out_path, dashboard_content


def get_all_alerts(org, gfn: GrafanaApi):
	"""Get all alerts."""
	finder, alerter = Finder(gfn), Alerter(gfn)
	alerts = finder.list_alerts()
	for alert in alerts:
		alert_content, folder = alerter.export_alert(alert)

		folder_name = folder["name"]
		out_path = Path(str(org["id"]), folder_name, alert_content["title"])

		yield out_path, alert_content


def all_orgs(container) -> Generator[Tuple[dict, GrafanaApi], None, None]:
	"""Iterate over all organisations in Grafana."""
	gfn_multiorg = GrafanaApi(host="localhost", port=container.host_port, auth=("admin", "admin"))
	orgs = gfn_multiorg.organizations.list_organization()
	for org in orgs:
		gfn = GrafanaApi(host="localhost", port=container.host_port, organization_id=org["id"], auth=("admin", "admin"))
		yield org, gfn


def write_to_file(out_path: Path, obj: dict):
	"""Write an object to file."""
	out_path.parent.mkdir(parents=True, exist_ok=True)
	with out_path.open(mode="w+", encoding="utf-8") as f:
		json.dump(obj, f, ensure_ascii=False, indent="\t")


def migrate(grafana_image, grafana_db: Path, extra_env_vars: Dict[str, str]) -> None:
	"""Migrate from classic to Unified alerting."""
	new_grafana_db = grafana_db.with_name("migrated.sqlite3").absolute()
	shutil.copyfile(grafana_db, new_grafana_db)

	container = start_container(grafana_image, new_grafana_db, extra_env_vars)

	if container.status != "running":
		raise RuntimeError(f"Could not start Grafana container {container=}")

	_wait_until_ready(container)

	root_path = Path("/tmp/o")
	for org, gfn in all_orgs(container):
		for out_path, dashboard_content in get_all_dashboards(org, gfn):
			write_to_file(root_path / out_path, dashboard_content)
		for out_path, alert_content in get_all_alerts(org, gfn):
			write_to_file(root_path / out_path, alert_content)

	stop_container(container)
