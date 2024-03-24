"""
Perform bulk operations on Grafana.

BulkOperations defines the basic interface. It is meant to be parametrised in 2 phases:
- information source: Subclasses of BulkOperations implement methods to get orgs and resources
- actions: Subclasses of those classes implement the actions to take

For example:
	BulkGrafanaOperation uses a Grafana instance as its source
	BulkExporter uses BulkGrafanaOperations to list all objects and write them to disk
"""
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Generator, List, Tuple

from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.paths import PathCodec
from grafanarmadillo.templator import Templator
from grafanarmadillo.types import AlertContent, DashboardContent, GrafanaPath, OrgMeta
from grafanarmadillo.util import exactly_one, read_from_file, write_to_file


l = logging.getLogger(__name__)


@lru_cache
def get_all_orgs(gfn_multiorg) -> List[OrgMeta]:
	"""Get a list of all orgs."""
	return gfn_multiorg.organizations.list_organization()


@lru_cache
def get_org(gfn_multiorg, org_name: str):
	"""Get an org by name, efficiently."""
	return exactly_one(
		list(filter(lambda o: o["name"] == org_name, get_all_orgs(gfn_multiorg))),
		f"org with name {org_name}"
	)


class BulkOperation(ABC):
	"""Run bulk operations on Grafana."""

	def __init__(self, cfg: dict):
		self.cfg = cfg
		self.gfn_multiorg = GrafanaApi(**self.cfg)

	def run(self):
		"""Run this bulk operation."""
		for org, gfn in self.all_orgs():
			for out_path, dashboard_content in self.get_all_dashboards(org, gfn):
				self.each_dashboard(out_path, dashboard_content)
			for out_path, alert_content in self.get_all_alerts(org, gfn):
				self.each_alert(out_path, alert_content)

	@abstractmethod
	def all_orgs(self) -> Generator[Tuple[OrgMeta, GrafanaApi], None, None]:
		"""
		Iterate over all organisations.

		This method should be implemented for each source of information.
		"""

	@abstractmethod
	def get_all_dashboards(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, DashboardContent], None, None]:
		"""
		Iterate over all dashboards.

		This method should be implemented for each source of information.
		"""

	@abstractmethod
	def get_all_alerts(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, AlertContent], None, None]:
		"""
		Iterate over all alerts.

		This method should be implemented for each source of information.
		"""

	@abstractmethod
	def each_dashboard(self, path: GrafanaPath, dashboard: DashboardContent):
		"""
		Act on each dashboard in Grafana.

		This method should be implemented for each operation.
		"""

	@abstractmethod
	def each_alert(self, path: GrafanaPath, alert: AlertContent):
		"""
		Act on each alert in Grafana.

		This method should be implemented for each operation.
		"""


class BulkGrafanaOperation(BulkOperation, ABC):
	"""Bulk operations which uses a Grafana instance as its source."""

	def all_orgs(self) -> Generator[Tuple[OrgMeta, GrafanaApi], None, None]:
		"""Iterate over all organisations in Grafana."""
		orgs = self.gfn_multiorg.organizations.list_organization()
		for org in orgs:
			gfn = GrafanaApi(**{**self.cfg, "organization_id": org["id"]})
			yield org, gfn

	def get_all_dashboards(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, DashboardContent], None, None]:
		"""Get all dashboards."""
		finder, dashboarder = Finder(gfn), Dashboarder(gfn)
		dashboards = finder.list_dashboards()
		for dashboard in dashboards:
			dashboard_content, folder = dashboarder.export_dashboard(dashboard)

			if folder is None:
				folder_name = "General"
			else:
				folder_name = folder["title"]

			out_path = GrafanaPath(dashboard_content["title"], folder_name, org["name"])

			yield out_path, dashboard_content

	def get_all_alerts(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, AlertContent], None, None]:
		"""Get all alerts."""
		finder, alerter = Finder(gfn), Alerter(gfn)
		alerts = finder.list_alerts()
		for alert in alerts:
			alert_content, folder = alerter.export_alert(alert)

			folder_name = folder["title"]
			out_path = GrafanaPath(alert_content["title"], folder_name, org["name"])

			yield out_path, alert_content


class BulkFileOperation(BulkOperation, ABC):
	"""Bulk operation which uses a filetree as its source."""

	def __init__(self, cfg: dict, root_directory: Path):
		self.root_directory = root_directory
		super().__init__(cfg)

	def all_orgs(self) -> Generator[Tuple[OrgMeta, GrafanaApi], None, None]:
		"""Iterate over all organisations in Grafana."""
		orgs = {PathCodec.decode_segment(o.name) for o in self.root_directory.glob("*/*")}
		for org_name in orgs:
			org = self.gfn_multiorg.organization.find_organization(org_name)
			gfn = GrafanaApi(**{**self.cfg, "organization_id": org["id"]})

			yield org, gfn

	def get_all_dashboards(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, DashboardContent], None, None]:
		"""Get all dashboards."""
		folders = (self.root_directory / "dashboards" / PathCodec.encode_segment(org["name"])).glob("*")
		for folder_path in folders:
			for dashboard_path in folder_path.glob("*.json"):
				content = read_from_file(dashboard_path)
				yield GrafanaPath(PathCodec.decode_segment(dashboard_path.name), PathCodec.decode_segment(folder_path.name), org["name"]), content

	def get_all_alerts(self, org: OrgMeta, gfn: GrafanaApi) -> Generator[Tuple[GrafanaPath, AlertContent], None, None]:
		"""Get all alerts."""
		folders = (self.root_directory / "alerts" / PathCodec.encode_segment(org["name"])).glob("*")
		for folder_path in folders:
			for alert_path in folder_path.glob("*.json"):
				content = read_from_file(alert_path)
				yield GrafanaPath(PathCodec.decode_segment(alert_path.name), PathCodec.decode_segment(folder_path.name), org["name"]), content


class BulkExporter(BulkGrafanaOperation):
	"""Export all resources from Grafana to files."""

	def __init__(self, cfg: dict, root_directory: Path, templator: Templator):
		self.root_directory = root_directory
		self.templator = templator
		super().__init__(cfg)

	def each_dashboard(self, path: GrafanaPath, dashboard: DashboardContent):
		"""Write each dashboard to files."""
		dashboard_templated = self.templator.make_template_from_dashboard(dashboard)
		l.info(f"export dashboard path={path}")
		write_to_file((self.root_directory / "dashboards" / PathCodec.encode_grafana(path)).with_suffix(".json"), dashboard_templated)

	def each_alert(self, path: GrafanaPath, alert: AlertContent):
		"""Write each alert to files."""
		alert_templated = self.templator.make_template_from_dashboard(alert)
		l.info(f"export alert path={path}")
		write_to_file((self.root_directory / "alerts" / PathCodec.encode_grafana(path)).with_suffix(".json"), alert_templated)


class BulkImporter(BulkFileOperation):
	"""Import all resources from files into Grafana."""

	def __init__(self, cfg: dict, root_directory: Path, templator: Templator):
		self.templator = templator
		super().__init__(cfg, root_directory)

	def each_dashboard(self, path: GrafanaPath, dashboard: DashboardContent):
		"""Import each dashboard into Grafana."""
		org = get_org(self.gfn_multiorg, path.org)
		gfn = GrafanaApi(**{**self.cfg, "organization_id": org["id"]})

		finder, dashboarder = Finder(gfn), Dashboarder(gfn)
		folder = finder.create_or_get_folder(path.folder)
		dashboard_templated = self.templator.make_dashboard_from_template(
			dashboard, dashboard
		)
		l.info(f"import dashboard path={path}")
		dashboarder.import_dashboard(dashboard_templated, folder)

	def each_alert(self, path: GrafanaPath, alert: AlertContent):
		"""Import each alert into Grafana."""
		org = get_org(self.gfn_multiorg, path.org)
		gfn = GrafanaApi(**{**self.cfg, "organization_id": org["id"]})

		finder, alerter = Finder(gfn), Alerter(gfn)
		folder = finder.create_or_get_folder(path.folder)
		alert_templated = self.templator.make_dashboard_from_template(alert, alert)
		l.info(f"import alert path={path}")
		alerter.import_alert(alert_templated, folder)
