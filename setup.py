#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Setup dot py."""
from __future__ import absolute_import, print_function

# import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
	"""Read description files."""
	path = join(dirname(__file__), *names)
	with open(path, encoding=kwargs.get("encoding", "utf8")) as fh:
		return fh.read()


# previous approach used to ignored badges in PyPI long description
# long_description = '{}\n{}'.format(
#     re.compile(
#         '^.. start-badges.*^.. end-badges',
#         re.M | re.S,
#         ).sub(
#             '',
#             read('README.rst'),
#             ),
#     re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read(join('docs', 'CHANGELOG.rst')))
#     )

long_description = "{}\n{}".format(
	read("README.rst"), read(join("docs", "CHANGELOG.rst")),
)

setup(
	name="grafanarmadillo",
	version="0.0.6",
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
	python_requires=">=3.6, <3.9",
	install_requires=["grafana_api~=1.0"],
	extras_require={
		# eg:
		#   'rst': ['docutils>=0.11'],
		#   ':python_version=="2.6"': ['argparse'],
	},
	setup_requires=[
		#   'pytest-runner',
		#   'setuptools_scm>=3.3.1',
	],
	entry_points={
		"console_scripts": []
		#
	},
	# cmdclass={'build_ext': optional_build_ext},
	# ext_modules=[
	#    Extension(
	#        splitext(relpath(path, 'src').replace(os.sep, '.'))[0],
	#        sources=[path],
	#        include_dirs=[dirname(path)]
	#    )
	#    for root, _, _ in os.walk('src')
	#    for path in glob(join(root, '*.c'))
	# ],
)
