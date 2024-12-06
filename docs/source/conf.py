# ruff: noqa: INP001

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


project = "SlipLib"
copyright = "2024, Ruud de Jong"  # noqa: A001
author = "Ruud de Jong"
github_username = "rhjdjong"
github_repository = "https://github.com/rhjdjong/SlipLib/"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Include the src and example directories in sys.path
# in order to generate the documentation for the examples
sys.path[0:0] = [
    os.path.abspath(os.path.join("..", "..", "src")),
    os.path.abspath(os.path.join("..", "..", "examples")),
]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.more_autodoc.autoprotocol",
    "sphinx_toolbox.more_autodoc.typehints",
    "sphinx_toolbox.more_autodoc.typevars",
    "sphinx_toolbox.more_autodoc.variables",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

napoleon_google_docstring = True
autoclass_content = "both"
autodoc_typehints = "description"
autodoc_type_aliases = {}
add_module_names = False
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
