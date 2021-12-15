
.. _installation:

Installation
---------------------------

Instructions on installation of the software. MATLAB users can skip to :ref:`install_for_matlab`.

Installing Python
==========================

While any python 3.X distribution should work, Anaconda has typically been used with this package as it provides many pre-installed dependencies.
Basic instructions are also given on how to install the base python interpreter if not using Anaconda, although this is not recommended for new Python users.

- Installing Anaconda  
    #. Go to the anaconda `download page <https://www.anaconda.com/distribution/#download-section>`_
    #. Select the correct operating system and installer
    #. Download and run the executable and follow the installer to install Anaconda 3.X
    #. Install dependencies through either :code:`conda install <package>` or :code:`pip install <package>`

- Installing Python (If NOT installing Anaconda)
    #. Download the `Python interpreter <https://www.python.org/downloads/>`_
    #. install dependencies through :code:`pip install <package>`

dependencies
++++++++++++++++++++++++

The following dependencies that are required for usage of certain modules in the system.
Not all are required for all modules and therefore it may be best to install them on a as needed basis as opposed to all at once.

- Python 3.X
- Numpy 
- Scipy 
- pyvisa
- pyserial (for bislide usage)
- plotly (for plotting)


Installing SAMURAI Software Package 
=========================================

Here are instructions on how to install the SAMURAI software package.

Download 
+++++++++++++++
The current code can be downloaded or cloned from the NIST SAMURAI :git_repo:`/`.

- The repository can be cloned from git using the command :code:`git clone https://github.com/usnistgov/SAMURAI.git`.

Installation
++++++++++++++++++++++

#. Change the current directory the downloaded SAMURAI package directory (e.g., :code:`cd <download_directory>/samurai/`).
    
    - This should contain a script called :code:`setup.py`

#. Open an anaconda prompt (or whatever python environment to install in)

#. Run :code:`pip install .` to install the package into the current environment 

#. The original package can then be deleted

.. note:: If The package will be changed or developed at any point in time (i.e. changes pushed to git), the original package should be placed somewhere where 
    it will not be deleted and the package should be installed with :code:`pip install -e .` after changing into the directory. 
    This will allow edits to the code to immediately be utilized in python.

    .. seealso:: https://pip.pypa.io/en/latest/reference/pip_install/?highlight=editable#editable-installs


.. _install_for_matlab:

Installation for MATLAB Users
================================

If only MATLAB is being used, the code simply needs to be downloaded. 
All MATLAB code then must contain the :code:`addpath('<code-directory>')` where :code:`<code-directory>` 
is the path to the directory of the code being used.
For example, if the software is downloaded to :code:`\code\samurai` a script using the :code:`TouchstoneEditor` function to load in a \*.s2p file
must have something like the following.

.. code-block:: MATLAB 

    % Set the paths to our directories 
    code_install_dir = '\code\samurai';
    function_dir = fullfile(code_install_dir,'samurai\base');

    % Now add the directory to the path
    addpath(function_dir)

    % Now the function 'TouchstoneEditor()' can be used
