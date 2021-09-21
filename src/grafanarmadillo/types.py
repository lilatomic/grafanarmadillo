"""Type hints for Grafana interaction."""

from typing import NewType


Dashboard = NewType("Dashboard", dict)
DashboardSearchResult = NewType("DashboardSearchResult", dict)
DashboardContent = NewType("DashboardContent", dict)
FolderSearchResult = NewType("Folder", dict)
