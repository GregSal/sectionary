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
    'sphinx.ext.intersphinx',
    "sphinx.ext.todo",
    'sphinxcontrib.bibtex',  # for bibliographic references  # get "last updated" from Git
    'sphinx_codeautolink',  # automatic links from code to documentation
    'nbsphinx'
]
intersphinx_mapping = {
    'IPython': ('https://ipython.readthedocs.io/en/stable/', None),
    'matplotlib': ('https://matplotlib.org/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'python': ('https://docs.python.org/3/', None),
    # 'numpy': ('http://docs.scipy.org/doc/numpy/', None),
    # 'scipy': ('http://docs.scipy.org/doc/scipy/reference/', None),
    # 'matplotlib': ('http://matplotlib.sourceforge.net/', None),
    # 'pandas': ('http://pandas.pydata.org/pandas-docs/stable/', None),
    # 'IPython': ('http://ipython.org/ipython-doc/stable/', None),
 }
intersphinx_aliases = {
    ("py:class", "dictionary"): ("py:class", "dict"),
    ("py:class", "PIL.Image"): ("py:class", "PIL.Image.Image"),
    ("py:class", "nbconvert.preprocessors.base.Preprocessor"): (
        "py:class",
        "nbconvert.preprocessors.Preprocessor",
    ),
    ("py:class", "nbformat.notebooknode.NotebookNode"): (
        "py:class",
        "nbformat.NotebookNode",
    ),
    ("py:class", "NotebookNode"): ("py:class", "nbformat.NotebookNode"),
    ("py:class", "traitlets.config.configurable.Configurable"): (
        "py:module",
        "traitlets.config",
    ),
}

# Napoleon Docstring settings
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
    '.ipynb": "jupyter_notebook'
    }

autosummary_generate = True

autoclass_content = "both"
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
html_theme = 'basic'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
