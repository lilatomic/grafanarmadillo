#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Setup dot py."""
from __future__ import absolute_import, print_function

import re
# import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
	"""Read description files."""
	path = join(dirname(__file__), *names)
	with open(path, encoding=kwargs.get("encoding", "utf8")) as fh:
		return fh.read()


long_description = "{}\n{}".format(
	read("README.rst"), read(join("docs", "CHANGELOG.rst")),
)
long_description = re.sub(r":doc:`(.*)`", r"https://github.com/lilatomic/grafanarmadillo/tree/main/docs/rst/\1.rst", long_description)

setup(
	name="grafanarmadillo",
	version="0.4.0",
	description="Simplifies interacting with Grafana, with a focus on templating dashboards ",
	long_description=long_description,
	long_description_content_type="text/x-rst",
	license="MIT License",
	author="lilatomic",
	url="https://github.com/lilatomic/grafanarmadillo",
	packages=find_packages("src"),
	package_dir={"": "src"},
	py_modules=[splitext(basename(i))[0] for i in glob("src/*.py")],
	include_package_data=True,
	zip_safe=False,
	classifiers=[],
	project_urls={
		"webpage": "https://github.com/lilatomic/grafanarmadillo",
		"Documentation": "https://grafanarmadillo.readthedocs.io/en/latest/",
		"Changelog": "https://github.com/lilatomic/grafanarmadillo/blob/main/docs/CHANGELOG.rst",
		"Issue Tracker": "https://github.com/lilatomic/grafanarmadillo/issues",
		"Discussion Forum": "https://github.com/lilatomic/grafanarmadillo/discussions",
	},
	keywords=[],
	python_requires=">=3.8, <4",
	install_requires=["grafana-client~=3.0"],
	extras_require={
		'cli': ["click>=8"],
		'migrate': ["docker>=5"]
	},
	setup_requires=[
		#   'pytest-runner',
		#   'setuptools_scm>=3.3.1',
	],
	entry_points={
		"console_scripts": ["grafanarmadillo=grafanarmadillo.cmd:grafanarmadillo"]
		#
	},
)
