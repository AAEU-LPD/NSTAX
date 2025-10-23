# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import os
import sys

# Project metadata
project = 'NSTA'
copyright = '2025, AAEU-LPD'
author = 'AAEU-LPD'
release = '0.1'

sys.path.insert(0, os.path.abspath('..'))   # Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# sys.path.insert(0, r'D:\a\NSTAX\NSTAX')
# sys.path.insert(0, r'D:\a\NSTAX')

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',                  # Google/NumPy docstrings
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx_autodoc_typehints',
]
autosummary_generate = True
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_show_sphinx = False                    # hide "Created using Sphinx" footer

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
templates_path = ['_templates']
html_static_path = ['_static']

# Optional: link to type hints rather than repeating them in signatures
typehints_fully_qualified = True
