from pathlib import Path

import pytest

from grafanarmadillo.paths import PathCodec
from grafanarmadillo.types import GrafanaPath


def test_encode_decode():
	segments = ["folder", "subfolder", "file with / in name"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_encode_decode_special_characters():
	segments = ["&", "?", "!"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_encode_decode_unicode_characters():
	segments = ["😀", "🚀", "🌟"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_encode_decode_numbers():
	segments = ["123", "456", "789"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_encode_decode_path_with_space():
	segments = ["path with space"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_encode_decode_path_with_special_characters():
	segments = ["$path^with!special&characters"]
	encoded_path = PathCodec.encode(segments)
	decoded_segments = PathCodec.decode(encoded_path)
	assert decoded_segments == segments


def test_absolute():
	assert PathCodec.decode(Path("/absolute/path")) == ["absolute", "path"]


def test_resolve_path__general():
	assert PathCodec.decode_grafana(Path("/folder/dashboard")) == GrafanaPath(folder="folder", name="dashboard")


def test_resolve_path__no_absolute_slash():
	assert PathCodec.decode_grafana(Path("folder/dashboard")) == GrafanaPath(folder="folder", name="dashboard")


def test_resolve_path__implicit_general():
	assert PathCodec.decode_grafana(Path("/dashboard")) == GrafanaPath(folder="General", name="dashboard")


def test_resolve_path__bare_dashboard():
	assert PathCodec.decode_grafana(Path("dashboard")) == GrafanaPath(folder="General", name="dashboard")


def test_resolve_path__too_many_parts():
	with pytest.raises(ValueError):
		PathCodec.decode_grafana(Path("/org/folder/dashboard/invalidpart"))


def test_resolve_path__with_org():
	assert PathCodec.decode_grafana(Path("/org/folder/name")) == GrafanaPath(org="org", folder="folder", name="name")
