import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, List, Optional, Tuple

from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.cmd import resolve_object_to_filepath
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator


class Store(ABC):
	"""A destination or source for items"""

	@abstractmethod
	def read_alert(self, name):
		"""Read an alert from this store"""

	@abstractmethod
	def read_dashboard(self, name):
		"""Read a dashboard from this store"""

	@abstractmethod
	def write_alert(self, name, alert):
		"""Write an alert to this store"""

	@abstractmethod
	def write_dashbaord(self, name, dashboard):
		"""Write an alert to this store"""


@dataclass
class FileStore(Store):
	"""Store Grafana objects in the filesystem"""
	root: Path

	@staticmethod
	def _read(file: Path) -> dict:
		with file.with_suffix(".json").open(mode="r", encoding="utf-8") as f:
			return json.load(f)

	@staticmethod
	def _write(file: Path, content: dict):
		with file.with_suffix(".json").open(mode="w", encoding="utf-8") as f:
			json.dump(content, f)


	def read_alert(self, name):
		return self._read(resolve_object_to_filepath(self.root, name))

	def read_dashboard(self, name):
		return self._read(resolve_object_to_filepath(self.root, name))

	def write_alert(self, name, alert):
		return self._write(resolve_object_to_filepath(self.root, name), alert)

	def write_dashbaord(self, name, dashboard):
		return self._write(resolve_object_to_filepath(self.root, name), dashboard)


@dataclass
class GrafanaStore(Store):
	gfn: GrafanaApi

	def read_alert(self, name):
		finder, alerter = Finder(self.gfn), Alerter(self.gfn)
		alert_info, _ = finder.create_or_get_alert(name)
		alert, _ = alerter.export_alert(alert_info)
		return alert_info

	def read_dashboard(self, name):
		finder, dashboarder = Finder(self.gfn), Dashboarder(self.gfn)
		dashboard_info, _ = finder.create_or_get_dashboard(name)
		dashboard_content, _ = dashboarder.export_dashboard(dashboard_info)
		return dashboard_content

	def write_alert(self, name, alert):
		finder, alerter = Finder(self.gfn), Alerter(self.gfn)
		alert_info, folder_info = finder.create_or_get_alert(name)
		alerter.import_alert(alert, folder_info)

	def write_dashbaord(self, name, dashboard):
		finder, dashboarder = Finder(self.gfn), Dashboarder(self.gfn)
		dashboard_info, folder = finder.create_or_get_dashboard(name)
		dashboarder.import_dashboard(dashboard, folder)


@dataclass
class Alert:
	name: str
	templator: Templator



@dataclass
class Dashboard:
	name: str
	templator: Templator


Flowable = Union[Alert, Dashboard]



class FlowException(Exception):
	def __init__(self, item: Flowable, cause: Optional[BaseException] = None):
		self.item = item
		if cause:
			self.__cause__ = cause


@dataclass
class FlowResult:
	successes: List[Flowable]
	failures: List[FlowException]

	def raise_first(self):
		"""Raise the first exception, if present"""
		if self.failures:
			raise self.failures[0]


@dataclass
class Flow:
	"""A collection of templating actions to do"""
	obj: Store
	tmpl: Store
	flows: List[Flowable] = field(default=list)

	def append(self, flow: Flowable):
		self.flows.append(flow)

	def obj_to_tmpl(self) -> FlowResult:
		"""Import from the source to the destination"""
		return self.run(obj_to_tmpl=True)

	def tmpl_to_obj(self) -> FlowResult:
		"""Export from the destination to the source"""
		return self.run(obj_to_tmpl=False)

	def run(self, obj_to_tmpl: bool) -> FlowResult:
		"""Run the flow"""
		failures = []
		successes = []

		for item in self.flows:
			try:
				if isinstance(item, Alert):
					if obj_to_tmpl:
						obj = self.obj.read_alert(item.name)
						tmpl = item.templator.make_template_from_dashboard(obj)
						self.tmpl.write_alert(item.name, tmpl)
					else:
						tmpl = self.tmpl.read_alert(item.name)
						info = self.obj.read_alert(item.name)
						obj = item.templator.make_dashboard_from_template(info, tmpl)
						self.obj.write_alert(item.name, obj)
				elif isinstance(item, Dashboard):
					if obj_to_tmpl:
						obj = self.obj.read_dashboard(item.name)
						tmpl = item.templator.make_template_from_dashboard(obj)
						self.tmpl.write_dashbaord(item.name, tmpl)
					else:
						tmpl = self.tmpl.read_dashboard(item.name)
						info = self.obj.read_dashboard(item.name)
						obj = item.templator.make_dashboard_from_template(info, tmpl)
						self.obj.write_dashbaord(item.name, obj)
				else:
					raise TypeError(f"Invalid flow, expected one of {Alert.__name__}, {Dashboard.__name__}, received {item.__class__.__name__}")

				successes.append(item)
			except Exception as e:
				failures.append(FlowException(item, e))

		return FlowResult(successes, failures)