"""Tests for helpers of the CLI which can be tested in isolation."""
from pathlib import Path

import pytest

from grafanarmadillo.cmd import (
	TOK_AUTO_MAPPING,
	EnvMapping,
	make_mapping_templator,
	resolve_object_to_filepath,
)


class TestMakeMappingTemplator:
	"""Test the function that builds the templator from a mapping file."""

	def test_auto(self):
		"""Test that the $auto token automatically builds a mapping."""
		mapping = EnvMapping({
			"stg": {
				"k0": "v0",
				"k1": "v1",
			}
		})
		templator = make_mapping_templator(mapping, "stg", TOK_AUTO_MAPPING)

		for k, v in mapping["stg"].items():
			assert templator.make_template(v) == "${%s}" % k

	def test_more_in_grafana(self):
		"""Test that extra keys in Grafana are not fine."""
		mapping = EnvMapping({
			"g": {
				"k0": "v0",
				"k1": "v1",
			},
			"t": {
				"k0": "v0",
			}
		})

		with pytest.raises(ValueError) as e:
			make_mapping_templator(mapping, "g", "t")
		assert "k1" in str(e.value)

	def test_more_in_template(self):
		"""Test that extra keys in the template are fine."""
		mapping = EnvMapping({
			"g": {
				"k0": "v0",
			},
			"t": {
				"k0": "v0",
				"k1": "v1",
			}
		})

		make_mapping_templator(mapping, "g", "t")


class TestResolveObjectToFilepath:
	"""Test resolving object paths to their files on disk."""

	base = Path("/p0/p1/p2")

	def test_absolute_name(self):
		r = resolve_object_to_filepath(self.base, "/f0/a0")
		assert r == Path("/p0/p1/p2/f0/a0.json")

	def test_relative_name(self):
		r = resolve_object_to_filepath(self.base, "f0/a0")
		assert r == Path("/p0/p1/p2/f0/a0.json")

	def test_cwd_base(self):
		r = resolve_object_to_filepath(Path("."), "f0/a0")
		assert r == Path("/p0/p1/p2/f0/a0.json")
