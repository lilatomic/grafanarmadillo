"""Tools for manipulating path-like objects into references to Grafana objects or file-safe paths."""
from pathlib import Path
from typing import List, Sequence
from urllib.parse import quote_plus, unquote_plus

from grafanarmadillo.types import GrafanaPath, PathLike


class PathCodec:
	"""Safely encode paths which may contain invalid characters, such as forward slashes."""

	@staticmethod
	def encode_grafana(path: GrafanaPath) -> Path:
		"""Encode a GrafanaPath."""
		if path.org:
			return PathCodec.encode([path.org, path.folder, path.name])
		else:
			return PathCodec.encode([path.folder, path.name])

	@staticmethod
	def encode(segments: List[str]) -> Path:
		"""Encode segments to a path."""
		encoded_segments = [quote_plus(segment) for segment in segments]
		return Path(*encoded_segments)

	@staticmethod
	def encode_segment(segment: str) -> str:
		"""Encode a single segment."""
		return quote_plus(segment)

	@staticmethod
	def try_parse(o: PathLike) -> GrafanaPath:
		"""Try to decode a pathlike object."""
		if isinstance(o, GrafanaPath):
			return o
		elif isinstance(o, list):
			return PathCodec.parse_grafana(o)
		else:
			path = Path(o)
			parts = path.parts[1:] if path.is_absolute() else path.parts
			return PathCodec.parse_grafana(parts)

	@staticmethod
	def parse_grafana(parts: Sequence[str]) -> GrafanaPath:
		"""Assemble segments into an orderly GrafanaPath."""
		if len(parts) == 3:
			return GrafanaPath(org=parts[0], folder=parts[1], name=parts[2])
		elif len(parts) == 2:
			return GrafanaPath(folder=parts[0], name=parts[1])
		elif len(parts) == 1:
			return GrafanaPath(folder="General", name=parts[0])
		else:
			raise ValueError(f"Grafana path has too many parts {parts=} len={len(parts)}")

	@staticmethod
	def decode(path: Path) -> List[str]:
		"""Decode a path to segments."""
		parts = path.parts[1:] if path.is_absolute() else path.parts

		decoded_segments = [unquote_plus(segment) for segment in parts]
		return decoded_segments

	@staticmethod
	def decode_segment(segment: str) -> str:
		"""Decode a single segment."""
		return unquote_plus(segment)
