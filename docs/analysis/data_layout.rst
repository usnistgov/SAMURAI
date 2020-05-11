.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _metafile_info:

Data Layout
====================================

SAMURAI Measurement Layout
----------------------------------

SAMURAI measurements taken at NIST consist of two parts, a metafile (\*.json) and measured data (\*.snp, \*.wnp, \*.meas).
When first opening the data folder for measurements taken at NIST, the folder will contain a metafile (\*.json) multiple measurement files (\*.meas),
along with a folder called :code:`touchstone`. 
The :code:`touchstone` sub-directory contains its own metafile (\*.json) along with a copy of all of the nominal measurement results as touchstone files (e.g. \*.snp_binary).
This folder can also be used when uncertainties are not of interest. 
If using :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` or :mat:func:`read_touchstone`, the data from both directories
(and therefore the data when using either metafile) should return the same values when loaded.

The Metafile
+++++++++++++++++++

The metafile associated with each measurement tracks a variety of information on the measurement as it sweeps through the aperture positions.
This provides information on experimental setup along with associating aperture positions with measured data files.
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
For MATLAB, loading and some other functionality is built into :mat:class:`SamuraiMetafile`.
After loading into python, data on the whole measurement can be accessed with :code:`metafile[key]`, while information at each aperture 
position can be accessed with :code:`metafile['measurements'][aperture_position_number][key]`.

The Data
+++++++++++

Each entry in the :code:`metafile['measurements']` list correspods to a measurement at a position in the aperture.
These entries include the position of the robot along with a path to the measurement taken by the VNA/LSNA.
These filepaths can be extracted with :code:`data_paths = metafile.file_paths`.

Each of these paths will point to either a touchstone file (\*.snp,\*.wnp,\*.snp) or a measurement file (\*.meas) which contain uncertainties on the measurements.
A reference explaining the touchstone format can be found `here <http://na.support.keysight.com/plts/help/WebHelp/FilePrint/SnP_File_Format.htm>`_ .
Data can be loaded without uncertainties with :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` (:mat:func:`read_touchstone` for MATLAB)
or with uncertainties using :class:`samurai.base.SamuraiMeasurement.SamuraiMeasurement`.

While touchstone data is typically stored in an ASCII format, because of the large amount of data taken with the SAMURAI system, data is sometimes
stored in a binary format (e.g. \*.s2p_binary). Starting from the beginning of the file, the binary data is stored as follows:

- 32 bit integer giving the number of rows
- 32 bit integer giving the number of columns
- 64 bit floating point data in row order

.. seealso:: This is the same format described in the help guide of the `NIST Microwave Uncertainty Framework <https://www.nist.gov/services-resources/software/wafer-calibration-software>`_

Both  :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` and :mat:func:`read_touchstone` for MATLAB can handle this with no issue.
An example of how :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` loads binary touchstone data is given below:


Working with Touchstone Files
------------------------------------------------

This section covers in a bit more detail working with touchstone files using :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` in python
and :mat:func:`TouchstoneEditor` in MATLAB.

.. seealso:: For more in depth information on loading and post-processing SAMURAI data, please see :ref:`post-process`

Python
+++++++++++

Touchstone files can be worked with in Python using :class:`samurai.base.TouchstoneEditor.TouchstoneEditor`.
This class loads data into a pandas DataFrame and places it in an attribute :code:`S` for s-parameters and :code:`A` and :code:`B` for wave parameters.
The following code then demonstrates how to access each of the S parameters of a 2 port S-parameter file (\*.s2p).

.. code-block:: python

   # Import the library
   from samurai.base.TouchstoneEditor import TouchstoneEditor

   # Load the file 
   mypath = r'path/to/file.s2p' # (could also be 'file.s2p_binary')
   mysnp = TouchstoneEditor(mypath)

   # Now lets get some data from this.
   # Accessing in this way automatically 
   # returns an editable reference to each parameter
   frequencies        = mysnp.freq_list
   sAll_complex       = mysnp.S
   s11_complex        = mysnp.S11
   s12_complex        = mysnp.S12
   s21_complex        = mysnp.S21
   s22_complex        = mysnp.S22

   # We can then access the data like
   freq = 26.5e9
   val = s11_complex[freq] # access by the frequency
   val = s11_complex.iloc[0] # access by integer index

This loaded data inherits from the pandas DataFrame type, allowing this data to also be manipulated similar to that.
More information on the pandas DataFrame can be found at the `Pandas DataFrame Documentation <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_.

MATLAB
+++++++++

In MATLAB, touchstone data is loaded using the :mat:func:`TouchstoneEditor` function. 
This function takes a file path and returns a MATLAB table object with all of the loaded data.
The following code again demonstrates how to access each of the S parameters of a 2 port S-parameter file.

.. code-block:: MATLAB

   % Add the directory of the function
   addpath(fullfile('<samurai-base-path>','samurai/analysis/support');

   % Load the file 
   mypath = 'path/to/file.s2p' % (could also be 'file.s2p_binary');
   mysnp = read_touchstone(mypath);

   % Now lets get some data from this
   frequencies        = mysnp.frequency;
   s11_complex        = mysnp.S11;
   s12_complex        = mysnp.S12;
   s21_complex        = mysnp.S21;
   s22_complex        = mysnp.S22;

External positioning information
-----------------------------------------

Later SAMURAI measurements use an Optitrack optical positioning system to provide positoning information on multiple points in the measurement such
as the transmit and recieve antennas, and possible scatterers in the scene. A dictionary with data on each marker can quickly be extracted from the metafile using the 
the metafile using the :code:`MetaFileController.get_external_positions()` method.








