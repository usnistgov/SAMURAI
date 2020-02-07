.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Getting Started
=========================
The following steps explain how to download and install the SAMURAI python package.


Download 
--------------------
The current code can be downloaded or cloned from the :git_repo:`/`

Installation
------------------

#. Change into the downloaded SAMURAI package directory.
    
    - This should contain a script called :code:`setup.py`

#. Open an anaconda prompt (or whatever python environment to install in)

#. Run :code:`pip install .` to install the package into the current environment 

#. The original package can then be deleted

.. note:: If The package will be changed or developed at any point in time (i.e. changes pushed to git), the original package should be placed somewhere where 
    it will not be deleted and the package should be installed with :code:`pip install -e .` after changing into the directory.

.. seealso:: https://pip.pypa.io/en/latest/reference/pip_install/?highlight=editable#editable-installs

Taking the first measurement
------------------------------

Assuming the setup and hardware is the same or close to that in the SAMURAI lab (more info should be added on this), 
the first measurement can be taken using the steps on how to run from a script described in :ref:`running-samurai`

.. todo:: More information on the hardware setup may be useful. Unless it is found to be described enough in :ref:`hardware-config`

