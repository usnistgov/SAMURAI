
Installing Python
---------------------------

Installing Python
++++++++++++++++++++++++++++++++++++++++++

While any python 3.X distribution should work, Anaconda has typically been used with this package as it provides many pre-installed dependencies.

- Installing Anaconda  
    #. Go to the anaconda `download page <https://www.anaconda.com/distribution/#download-section>`_
    #. Select the correct operating system and installer
    #. Download and run the executable and follow the installer to install Anaconda 3.X
    #. Install depedencies through either :code:`conda install <package>` or :code:`pip install <package>`

- Installing Python 
    #. Download the base python interpreter at `https://www.python.org/downloads/`_
    #. install dependencies through :code:`pip install <package>`

dependencies
++++++++++++++++++++++++

The following dependencies are some that are required for usage of certain modules in the system.
Not all are required for all modules and therefore it may be best to install them on a as needed basis as opposed to all at once.

- Python 3.X
- Numpy 
- Scipy 
- pyvisa
- pyserial (for bislide usage)
- plotly (for plotting)


Installing SAMURAI Software Package 
------------------------------------------

Here are instructions on how to install the SAMURAI software package.

Download 
+++++++++++++++
The current code can be downloaded or cloned from the :git_repo:`/` or will be directly provided in a *.zip file.

- The repository can be cloned from git when inside the git network using the command :code:`git clone https: https://gitlab.nist.gov/gitlab/uncertainteam/samurai.git`.

- If using a *.zip file, the files must be extracted before installation 

Installation
++++++++++++++++++++++

#. Change the current directory the downloaded SAMURAI package directory (e.g., :code:`cd <download_directory>/samurai/`).
    
    - This should contain a script called :code:`setup.py`

#. Open an anaconda prompt (or whatever python environment to install in)

#. Run :code:`pip install .` to install the package into the current environment 

#. The original package can then be deleted

.. note:: If The package will be changed or developed at any point in time (i.e. changes pushed to git), the original package should be placed somewhere where 
    it will not be deleted and the package should be installed with :code:`pip install -e .` after changing into the directory. 
    This will allow edits to the code to immediatly be utilized in python.

    .. seealso:: https://pip.pypa.io/en/latest/reference/pip_install/?highlight=editable#editable-installs