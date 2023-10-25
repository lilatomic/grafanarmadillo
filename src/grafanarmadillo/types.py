"""Type hints for Grafana interaction."""

from typing import NewType, Optional, TypedDict

UID = NewType("UID", str)


class DashboardSearchResult(TypedDict):
	"""Relevant keys returned by a Grafana search."""

	id: int
	uid: UID
	title: str
	folderId: Optional[int]
	folderUid: Optional[UID]
	folderTitle: Optional[str]


DashboardContent = NewType("DashboardContent", dict)
DashboardMeta = NewType("DashboardMeta", dict)


class Dashboard(TypedDict):
	"""Relevant keys returned by GET of a Grafana dashboard."""

	meta: DashboardMeta
	dashboard: DashboardContent


DashboardPanel = NewType("DashboardPanel", dict)

FolderSearchResult = NewType("Folder", dict)
