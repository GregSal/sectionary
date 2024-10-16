# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
#sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(r'../src'))
#sys.path.insert(0, os.path.abspath(r'../..'))
#sys.path.append(r'src')

#for x in os.walk('../../src'):
#  sys.path.insert(0, x[0])

from pprint import pprint
#pprint(sys.path)

import sections
import buffered_iterator
import text_reader

# -- Project information -----------------------------------------------------

project = 'Sectionary'
copyright = '2021, Greg Salomons'
author = 'Greg Salomons'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'nbsphinx',
    'sphinx.ext.intersphinx',
    "sphinx.ext.todo",
    'sphinx_copybutton',
    'sphinx_rtd_theme'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
    }

autosummary_generate = True

# Napoleon Docstring settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

autoclass_content = "both"

autodoc_default_options = {
    'members': None,
    'no-inherited-members': None,
}

# copybutton conf
copybutton_prompt_text = r'>>> |\.\.\. '
copybutton_prompt_is_regexp = True

# intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/{.major}'.format(
        sys.version_info), None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference', None),
    'matplotlib': ('http://matplotlib.org', None),
    'IPython': ('https://ipython.readthedocs.io/en/stable/', None),
}
intersphinx_aliases = {
    ("py:class", "dictionary"): ("py:class", "dict"),
    ("py:class", "PIL.Image"): ("py:class", "PIL.Image.Image"),
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'traditional'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
