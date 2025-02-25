"""Pieces for templating multiple dashboards at once."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Type, Union

import urllib3
from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.dashboarder import Dashboarder
from grafanarmadillo.find import Finder
from grafanarmadillo.templator import Templator
from grafanarmadillo.types import PathLike
from grafanarmadillo.util import CacheMode, resolve_object_to_filepath


class Store(ABC):
	"""A destination or source for items."""

	@abstractmethod
	def read_alert(self, name: PathLike):
		"""Read an alert from this store."""

	@abstractmethod
	def read_dashboard(self, name: PathLike):
		"""Read a dashboard from this store."""

	@abstractmethod
	def write_alert(self, name: PathLike, alert):
		"""Write an alert to this store."""

	@abstractmethod
	def write_dashboard(self, name: PathLike, dashboard):
		"""Write an alert to this store."""


@dataclass
class FileStore(Store):
	"""
	Store and retrieve Grafana objects in the filesystem.

	Objects will be stored under the same path as in Grafana.
	For example, a dashboard titled "MyDashboard" in a folder titled "MyFolder"
	will appear at `{root}/MyFolder/MyDashboard.json`.

	You can customise the path these files will be stored under.
	Override the method `resolve_object_to_filepath`.
	"""

	root: Path
	json_encoder: Type[json.JSONEncoder] = json.JSONEncoder
	json_decoder: Type[json.JSONDecoder] = json.JSONDecoder

	TOK_DASHBOARD = "dashboard"
	TOK_ALERT = "alert"

	@staticmethod
	def _read(file: Path, codec: Type[json.JSONDecoder]) -> dict:
		with file.with_suffix(".json").open(mode="r", encoding="utf-8") as f:
			return json.load(f, cls=codec)

	@staticmethod
	def _write(file: Path, content: dict, codec: Type[json.JSONEncoder]):
		file.parent.mkdir(exist_ok=True)
		with file.with_suffix(".json").open(mode="w", encoding="utf-8") as f:
			json.dump(content, f, cls=codec)

	def resolve_object_to_filepath(self, name: PathLike, type_: str):
		"""
		Find the file on disk that contains the object.

		@param name:
		@param type_: The kind of object to find, one of "dashboard" or "alert".
		"""
		return resolve_object_to_filepath(self.root, name)

	def read_alert(self, name):
		"""Read an alert from this store."""
		return self._read(self.resolve_object_to_filepath(name, self.TOK_ALERT), self.json_decoder)

	def read_dashboard(self, name):
		"""Read a dashboard from this store."""
		return self._read(self.resolve_object_to_filepath(name, self.TOK_DASHBOARD), self.json_decoder)

	def write_alert(self, name, alert):
		"""Write an alert to this store."""
		return self._write(self.resolve_object_to_filepath(name, self.TOK_ALERT), alert, self.json_encoder)

	def write_dashboard(self, name, dashboard):
		"""Write an alert to this store."""
		return self._write(self.resolve_object_to_filepath(name, self.TOK_DASHBOARD), dashboard, self.json_encoder)


class GrafanaStore(Store):
	"""Store and retrieve objects from a Grafana instance."""

	def __init__(self, gfn: GrafanaApi):
		self.gfn = gfn
		self.finder = Finder(gfn, cache_mode=CacheMode.SESSION)

	def read_alert(self, name):
		"""Read an alert from this store."""
		alerter = Alerter(self.gfn)
		alert_info, _ = self.finder.create_or_get_alert(name)
		alert, _ = alerter.export_alert(alert_info)
		return alert_info

	def read_dashboard(self, name):
		"""Read a dashboard from this store."""
		dashboarder = Dashboarder(self.gfn)
		dashboard_info, _ = self.finder.create_or_get_dashboard(name)
		dashboard_content, _ = dashboarder.export_dashboard(dashboard_info)
		return dashboard_content

	def write_alert(self, name, alert):
		"""Write an alert to this store."""
		alerter = Alerter(self.gfn)
		alert_info, folder_info = self.finder.create_or_get_alert(name)
		alerter.import_alert(alert, folder_info)

	def write_dashboard(self, name, dashboard):
		"""Write an alert to this store."""
		dashboarder = Dashboarder(self.gfn)
		dashboard_info, folder = self.finder.create_or_get_dashboard(name)
		dashboarder.import_dashboard(dashboard, folder)


@dataclass
class URLStore(Store):
	"""Store and retrieve objects from remote URLs, such as https://grafana.com/grafana/dashboards/ or GitHub."""

	def read_url(self, url: str):
		"""GET a URL."""
		resp = urllib3.request("GET", url)
		return resp.json()

	def read_alert(self, name):
		"""Read an alert from this store."""
		if not isinstance(name, str):
			raise TypeError(f"URLStore can only read remote URLs, not {type(name)}")
		return self.read_url(name)

	def read_dashboard(self, name):
		"""Read a dashboard from this store."""
		if not isinstance(name, str):
			raise TypeError(f"URLStore can only read remote URLs, not {type(name)}")
		return self.read_url(name)

	def write_alert(self, name, alert):
		"""Write an alert to this store."""
		raise NotImplementedError("URLStore cannot write")

	def write_dashboard(self, name, dashboard):
		"""Write an alert to this store."""
		raise NotImplementedError("URLStore cannot write")


@dataclass
class Alert:
	"""Flowable request for an Alert."""

	name_obj: PathLike
	name_tmpl: PathLike
	templator: Templator


@dataclass
class Dashboard:
	"""Flowable request for a Dashboard."""

	name_obj: PathLike
	name_tmpl: PathLike
	templator: Templator


Flowable = Union[Alert, Dashboard]


class FlowException(Exception):
	"""Wrapped Exception of running a Flow."""

	def __init__(self, item: Flowable, cause: Optional[BaseException] = None):
		self.item = item
		if cause:
			self.__cause__ = cause


@dataclass
class FlowResult:
	"""Result of running a Flow."""

	successes: List[Flowable]
	failures: List[FlowException]

	def raise_first(self):
		"""Raise the first exception, if present."""
		if self.failures:
			raise self.failures[0]

	def ensure_success(self) -> FlowResult:
		"""Inline raise the first exception, if present."""
		self.raise_first()
		return self


@dataclass
class Flow:
	"""A collection of templating actions to do."""

	store_obj: Store
	store_tmpl: Store
	flows: List[Flowable] = field(default=list)

	def append(self, flow: Flowable):
		"""Add a Flowable request to this Flow."""
		self.flows.append(flow)

	def extend(self, flows: Iterable[Flowable]):
		"""Add several Flowable requests to this Flow."""
		self.flows.extend(flows)

	def obj_to_tmpl(self) -> FlowResult:
		"""Import from the source to the destination."""
		return self.run(obj_to_tmpl=True)

	def tmpl_to_obj(self) -> FlowResult:
		"""Export from the destination to the source."""
		return self.run(obj_to_tmpl=False)

	def run(self, obj_to_tmpl: bool) -> FlowResult:
		"""Run the flow."""
		failures = []
		successes = []

		for item in self.flows:
			try:
				if isinstance(item, Alert):
					if obj_to_tmpl:
						obj = self.store_obj.read_alert(item.name_obj)
						tmpl = item.templator.make_template_from_dashboard(obj)
						self.store_tmpl.write_alert(item.name_tmpl, tmpl)
					else:
						tmpl = self.store_tmpl.read_alert(item.name_tmpl)
						info = self.store_obj.read_alert(item.name_obj)
						obj = item.templator.make_dashboard_from_template(info, tmpl)
						self.store_obj.write_alert(item.name_obj, obj)
				elif isinstance(item, Dashboard):
					if obj_to_tmpl:
						obj = self.store_obj.read_dashboard(item.name_obj)
						tmpl = item.templator.make_template_from_dashboard(obj)
						self.store_tmpl.write_dashboard(item.name_tmpl, tmpl)
					else:
						tmpl = self.store_tmpl.read_dashboard(item.name_tmpl)
						info = self.store_obj.read_dashboard(item.name_obj)
						obj = item.templator.make_dashboard_from_template(info, tmpl)
						self.store_obj.write_dashboard(item.name_obj, obj)
				else:
					raise TypeError(
						f"Invalid flow, expected one of {Alert.__name__}, {Dashboard.__name__}, received {item.__class__.__name__}")

				successes.append(item)
			except Exception as e:
				failures.append(FlowException(item, e))

		return FlowResult(successes, failures)
