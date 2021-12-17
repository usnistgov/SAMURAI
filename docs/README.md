# Documentation folder for SAMURAI

All of this final docs are built using sphinx.

# Building the Docs

To build the documentation, open a command prompt (I have only tested this with anaconda prompt) and run `make html`.

This will build the docs into ./_build/html/

## Setting the root directory to data

In the sphinx `config.py` file, make sure to set the correct root directories for `extlinks` for data and other things. More info on this can be found at https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

# Requirements

- Sphinx - Run `conda install sphinx` or go to http://www.sphinx-doc.org/en/master/usage/installation.html (this should already be included with anaconda)
- commonmark - run `pip install commonmark`
- recommonmark - run `pip install recommonmark`
- sphinx_rtd_theme - run `pip install sphinx_rtd_theme` or `conda install -c anaconda sphinx_rtd_theme`
- MATLAB Sphinx support - run `pip install -U sphinxcontrib-matlabdomain` or go to https://pypi.org/project/sphinxcontrib-matlabdomain/


