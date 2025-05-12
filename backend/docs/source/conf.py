import os
import sys

# Insert the project root and app directory into sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'app')
))

project = 'Brain2Gain Backend'
author = 'Brain2Gain Team'
release = '0.1.0'

# Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

# Paths that contain templates, relative to this directory.
templates_path = ['_templates']

# The master toctree document.
master_doc = 'index'

# Patterns to ignore
exclude_patterns = []

# HTML theme
html_theme = 'sphinx_rtd_theme'

# Static files
html_static_path = ['_static']