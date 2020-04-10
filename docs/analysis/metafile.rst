.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _metafile_info:

Interacting with the Metafile
====================================

Each SAMURAI measurement contains a metafile that provides a information on the measurement and location of data.
The data is saved into a JavaScript Object Notation (JSON) file format. 
When loaded into Python, it is loaded as a dictionary and data can be accessed using the typical :code:`metafile[key]` instructions.
In MATLAB (using MATLAB's JSON parser), this is loaded as a structure and therefore would be accessed as :code:`metafile.(key)`.
Some of the data recorded in the metafile is:

- Working Directory                         (:code:`working_directory` key)
- Experiment Notes                          (:code:`notes` key)
- Vector Network Analyzer (VNA) Settings    (:code:`vna_info` key)
- Antenna Information                       (:code:`antennas` key)
- Information on each measurement including (:code:`measurements` key): 

   - Measurement file path                      (:code:`filename` key)
   - Timestamp                                  (:code:`timestamp` key)
   - Synthetic Aperture Position                (:code:`position` key)
   - Measurement Specific Notes                 (:code:`notes` key)
   - Position measurements from External system (:code:`external_position_measurements` key)

Interaction with the metafile can easily be performed using the :class:`samurai.analysis.support.MetafileController.MetafileController`.
After loading into python, data on the whole measurement can be accessed with :code:`metafile[key]`, while information at each aperture 
position can be accessed with :code:`metafile['measurements'][aperture_position_number][key]`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Loading in a Metafile Object
-------------------------------
A metafile can be loaded using the following code

.. code-block:: python
   
   #import the controller class
   from samurai.analysis.support.MetafileController import MetafileController
   
   #provide a path to the metafile 
   metafile_path = "./path/to/metafile.json"

   #load the metafile into an object
   mymetafile = MetafileController(metafile_path)

Loading the Measurement Data
-------------------------------

The file paths of each measurement can be retrieved with :code:`MetafileController.file_paths` property. 
The position of the synthetic aperture from each measurement can be retrieved with the :code:`MetafileController.positions` property.
The data from each of the files can be loaded as :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` objects using the :code:`MetafileController.load_data()` method.

This process can also be done manually by looping through the file paths contained in the metafile (the :code:`MetafileController.file_paths` property) along with the :class:`samurai.base.TouchstoneEditor.TouchstoneEditor`.
An example of this is given as follows

.. code-block:: python

   #first import our TouchstoneEditor Class 
   from samurai.base.TouchstoneEditor import TouchstoneEditor

   # Assume the metafile has already been loaded
   fpaths = mymetafile.file_paths

   # Now lets loop through and load the data
   data_list = []
   for fpath in fpaths:
      data_list.append(TouchstoneEditor(fpath))

Data for the SAMURAI measurements is typically contained in the Touchstone file format (e.g. \*.s2p). 
A reference explaining this format can be found `here<http://na.support.keysight.com/plts/help/WebHelp/FilePrint/SnP_File_Format.htm>`_ .
While this data is typically stored in an ASCII format, because of the large amount of data taken with the SAMURAI system, data is sometimes
stored in a binary format (e.g. \*.s2p_binary). Starting from the beginning of the file, the binary data is stored as follows:

- 32 bit integer giving the number of rows
- 32 bit integer giving the number of columns
- 64 bit floating point data in row order

An example of how this data is read in is given below in python:

.. code-block: python 

   # First import NumPy
   import numpy as np

   # Then load the row and column count
   [num_rows,num_cols] = np.fromfile(file_path,dtype=np.uint32,count=2) 

   # And load the floating point data
   raw_data = np.fromfile(file_path,dtype=np.float64) #read raw data
   raw_data = raw_data[1:] #remove header

   # Set to the correct shape
   raw_data = raw_data.reshape((num_rows,num_cols)) #match the text output

.. seealso:: This is the same format described in the help guide of the `NIST Microwave Uncertainty Framework <https://www.nist.gov/services-resources/software/wafer-calibration-software>`_

Both binary and regular snp files can be loaded with :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` without any extra user work.
If using MATLAB, the :code:`read_snp_binary.m` function in :code:`samurai/analysis/support/` can be used to load binary snp data.

An example of how data can be accessed with :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` is given below.

.. code-block: python

   # Import the library
   from samurai.base.TouchstoneEditor import TouchstoneEditor

   # Load the file 
   mypath = 'path/to/file.s2p' # (could also be 'file.s2p_binary')
   mysnp = TouchstoneEditor(mypath)

   # Now lets get some data from this
   frequencies        = mysnp.freq_list
   block_data_complex = mysnp.raw 
   s11_complex        = mysnp.S[11]
   s12_complex        = mysnp.S[12]
   s21_complex        = mysnp.S[21]
   s22_complex        = mysnp.S[22]

Loading external positioning information
-----------------------------------------

Later SAMURAI measurements use an Optitrack optical positioning system to provide positoning information on multiple points in the measurement such
as the transmit and recieve antennas, and possible scatterers in the scene. A dictionary with data on each marker can quickly be extracted from the metafile using the 
the metafile using the :code:`MetaFileController.get_external_positions()` method.


Loading with MATLAB
----------------------
Some of these functions have also been implemented in MATLAB with the SamuraiMetafile Class.
An example of how to load filepaths and positions in MATLAB is as follows:

.. note:: The user must provide the correct loading of the data from the filepaths in this scenario.

.. literalinclude:: ../test_scripts/metafile_test_script.m
    :language: matlab 
    :linenos:


Metafile Interface Classes
---------------------------
Code information for both MetaFileController (Python) and SamuraiMetafile (MATLAB)

Python 
+++++++++++++++++

.. automodule:: samurai.analysis.support.MetafileController
    :members:

MATLAB
++++++++++++
    
.. mat:automodule:: samurai.analysis.support 
.. mat:autoclass:: SamuraiMetafile 
    :members:




