# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


project = "SlipLib"
copyright = "2024, Ruud de Jong"
author = "Ruud de Jong"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Include the example directory in sys.path\
# in order to generate the documentation for the examples
sys.path.append(os.path.abspath(os.path.join("..", "..", "examples")))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []

napoleon_google_docstring = True
# napoleon_use_rtype = False
autoclass_content = "both"
autodoc_typehints = "description"
autodoc_type_aliases = {
    "IPAddress": "IPAddress",
    "Tuple[SlipSocket, IPAddress]": "Tuple[SlipSocket, IPAddress]",
}
add_module_names = False
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
