"""Type hints for Grafana interaction."""

from typing import NewType, Optional, TypedDict, Union


UID = NewType("UID", str)


class AnySearchResult(TypedDict):
	"""Metadata for both Grafana dashboards and alerts."""

	uid: UID
	title: str
	folderUid: Optional[UID]


class DashboardSearchResult(TypedDict):
	"""Relevant keys returned by a Grafana search."""

	id: int
	uid: UID
	title: str
	folderId: Optional[int]
	folderUid: Optional[UID]
	folderTitle: Optional[str]


class AlertSearchResult(TypedDict):
	"""Relevant keys returned for an alert."""

	id: int
	uid: UID
	orgID: int
	folderUID: UID
	ruleGroup: str
	title: str


DashboardContent = NewType("DashboardContent", dict)
AlertContent = NewType("AlertContent", dict)
AnyContent = Union[DashboardContent, AlertContent]
DashboardMeta = NewType("DashboardMeta", dict)


OrgMeta = NewType("OrgMeta", dict)


class Dashboard(TypedDict):
	"""Relevant keys returned by GET of a Grafana dashboard."""

	meta: DashboardMeta
	dashboard: DashboardContent


DashboardPanel = NewType("DashboardPanel", dict)

FolderSearchResult = NewType("Folder", dict)
