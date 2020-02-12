# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
matlab_src_dir = os.path.abspath('..')


# -- Docstring Parsing -------------------------------------------------------
import commonmark
import re

dox_funct_dict = {
    "brief"  : lambda str: re.sub(' +',' ',str.strip().strip("brief").replace('\n','').strip()),
    "param"  : lambda str: re.sub(' +',' ',':param '+' '.join(str.strip().split(' ')[1:]).replace(' -',':').replace('\n','')+'\n'),
    "example": lambda str: re.sub(' +',' ',('.. code-block:: python\n'+str.strip().strip('example')).replace('\n','\n   ')+'\n').lstrip(),
    "return" : lambda str: re.sub(' +',' ',":return: "+str.strip().strip("return").replace('\n','')+'\n'),
	"note"   : lambda str: re.sub(' +',' ',".. note:"+str.strip().strip("note").replace('\n','')+'\n'),
    "warning": lambda str: re.sub(' +',' ',".. warning:"+str.strip().strip("warning").replace('\n','')+'\n'),
    "todo"   : lambda str: re.sub(' +',' ',".. todo::"+str.strip().strip("todo").replace('\n','')+'\n'),
    "cite"   : lambda str: re.sub(' +',' ',".. seealso:: "+"*"+str.strip().strip("cite").replace('\n','')+"*\n"),
}

def docstring_preprocess(doc_str):
    '''@brief preprocess our doc strings'''
    doc_str = doc_str.replace('*','\*')
    doc_str = doc_str.replace('"','\"')
    return doc_str

def doxygen2rst(dox_str):
    '''@brief take doxygen-like docstrings that are partially rst and make them restructured text'''
    dox_str = dox_str.strip() #remove any leading or trailing whitespaces
    dox_lines = dox_str.split('@')[1:] #split lines on ampersand and remove first empty bit
    rst_str_list = []
    for dl in dox_lines: #loop through each split line
        for k in dox_funct_dict.keys(): #look for the key 
            if dl.startswith(k):
                dl = dox_funct_dict[k](dl) #format the line 
        rst_str_list.append(dl) #add the line to the lines
    return ' \n'.join(rst_str_list)

def docstring(app, what, name, obj, options, lines): #change this to not use markdown
    dox  = '\n'.join(lines)
    rst = docstring_preprocess(dox)
    #ast = commonmark.Parser().parse(md)
    #rst = commonmark.ReStructuredTextRenderer().render(ast)
    lines.clear()
    rst = doxygen2rst(rst)
    if name=='samurai.base.generic':
        print("")
        print("{}:".format(name))
    for line in rst.splitlines():
        lines.append(line)
        if name=='samurai.base.generic':
            print("{}".format(line))

def setup(app):
    app.connect('autodoc-process-docstring', docstring)


# -- Project information -----------------------------------------------------

project = 'SAMURAI'
copyright = ('This software was developed by employees of the National Institute of Standards and Technology (NIST),'+
              ' an agency of the Federal Government and is being made available as a public service.'+
              ' Pursuant to title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.'+
              ' This software may be subject to foreign copyright.  Permission in the United States and in foreign countries, to the extent that NIST may hold copyright,'+
              ' to use, copy, modify, create derivative works, and distribute this software and its documentation without fee is hereby granted on a non-exclusive basis,'+
              ' provided that this notice and disclaimer of warranty appears in all copies.'+
              ' See the `Copyright Notice` section on the home page for more information.')
author = 'NIST'

# The short X.Y version
version = ''
# The full version, including alpha/beta/rc tags
release = '0.1'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
	'sphinxcontrib.matlab',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
	'recommonmark',
    'sphinx.ext.extlinks'
]

#link root directories
extlinks = {
    'data_root': (r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\%s','SAMURAI Data '),
    'git_repo': (r'https://gitlab.nist.gov/gitlab/uncertainteam/samurai/%s','Git Repository '),
}

#exclusions
#exclude_patterns = [
#    './README.md' #this is for how to build the docs
#    ] 

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'

#source_parsers = {
#   '.md': 'recommonmark.parser.CommonMarkParser',
#}

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'SAMURAIdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'SAMURAI.tex', 'SAMURAI Documentation',
     'NIST', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'samurai', 'SAMURAI Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'SAMURAI', 'SAMURAI Documentation',
     author, 'SAMURAI', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True