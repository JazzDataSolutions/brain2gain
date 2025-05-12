import os
import sys
# Add project root to sys.path
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'Full Stack FastAPI - Store & Website'
author = 'Brain2Gain'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',
    'sphinxcontrib.mermaid',
    'sphinxcontrib.openapi',
]

# Support both .rst and .md
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for myst-parser ------------------------------------------------
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]