# -*- coding: utf-8 -*-
"""Config file for Sphinx-docs."""
from __future__ import unicode_literals

import os

import sphinx_py3doc_enhanced_theme


extensions = [
	"sphinx.ext.autodoc",
	"sphinx.ext.autosummary",
	"sphinx.ext.coverage",
	"sphinx.ext.doctest",
	"sphinx.ext.extlinks",
	"sphinx.ext.ifconfig",
	"sphinx.ext.napoleon",
	"sphinx.ext.todo",
	"sphinx.ext.viewcode",
	"sphinx.ext.autosectionlabel",
]

todo_include_todos = True

exclude_patterns = [
	"i_*",
]

if os.getenv("SPELLCHECK"):
	extensions += ("sphinxcontrib.spelling",)
	spelling_show_suggestions = True
	spelling_lang = "en_US"
	# https://sphinxcontrib-spelling.readthedocs.io/en/latest/customize.html
	spelling_word_list_filename = ["../spelling_wordlist.txt"]

source_suffix = ".rst"
master_doc = "index"
project = "grafanarmadillo"
year = "2021"
author = "lilatomic"
copyright = "{0}, {1}".format(year, author)
version = release = "0.9.0"

pygments_style = "trac"
templates_path = ["."]
extlinks = {
	"issue": ("https://github.com/lilatomic/grafanarmadillo/issues/%s", "#"),  # noqa: E501
	"pr": ("https://github.com/lilatomic/grafanarmadillo/pull/%s", "PR #"),  # noqa: E501
}

# codecov io closes connection if host is accessed too repetitively.
# codecov links are ignored here for the same reason there's a sleep
# in the .travis.yml file
# see https://github.com/codecov/codecov-python/issues/158
linkcheck_ignore = [
	r"https://codecov.io/gh/lilatomic/grafanarmadillo/*",
]

html_theme = "sphinx_py3doc_enhanced_theme"
html_theme_path = [sphinx_py3doc_enhanced_theme.get_html_theme_path()]
html_theme_options = {
	"githuburl": "https://github.com/lilatomic/grafanarmadillo",
}

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_sidebars = {
	"**": ["searchbox.html", "globaltoc.html", "sourcelink.html"],
}
html_short_title = "%s-%s" % (project, version)

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
