"""Type hints for Grafana interaction."""

import sys


if (sys.version_info[0] == 3) and (sys.version_info[1] in [6, 7]):
	from typing import NewType, Optional
	from typing_extensions import TypedDict
else:
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
