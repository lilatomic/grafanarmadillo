"""Tests for helpers of the CLI which can be tested in isolation."""
import pytest

from grafanarmadillo.cmd import TOK_AUTO_MAPPING, EnvMapping, make_mapping_templator


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
