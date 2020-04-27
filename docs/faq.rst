
.. _faq:

Frequently Asked Questions (FAQ)
=====================================

Here are some of the frequently asked questions (FAQ) along with some not so frequently asked questions (NSFAQ) with answers.

|


Analysis Questions
------------------------

|

----

**Q:** What is a touchstone file?


**A:** Touchstone files are a standard method for storing s-parameter data (e.g. \*.s1p,\*.s2p,\*.snp). These files store data measured by the VNA. 
Wave-parameter files (\*.wnp for nonlinear measurements), and waveforms (\*.waveform) are subsets of this filetype. 

.. seealso: `https://en.wikipedia.org/wiki/Touchstone_file`_

|

----

**Q:** How do I load touchstone files? (\*.snp,\*.wnp,\*.waveform,\*.meas)


**A:** All of these filetypes (\*.snp,\*.wnp,\*.waveform,\*.meas) can be loaded with :class:`samurai.base.TouchstoneEditor.TouchstoneEditor`
for Python or the MATLAB function :mat:func:`read_touchstone`.
If loading a \*.meas file, only the nominal result (no uncertainties) is loaded. 

|

----

**Q:** What is a binary touchstone file (\*.snp_binary, \*.wnp_binary) and how do I work with it?


**A:** Binary touchstone files store the same data as a typical touchstone file but in a binary format. This allows for smaller file sizes and faster reading.
Starting from the beginning of the file, the binary data is stored as follows:

- 32 bit integer giving the number of rows
- 32 bit integer giving the number of columns
- 64 bit floating point data in row order

This can also be loaded in using :class:`samurai.base.TouchstoneEditor.TouchstoneEditor` for Python or the MATLAB function :mat:func:`read_touchstone`.
It can also be read in manually with code similar to the following.

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


|

----

**Q:** What is a \*.meas file?


**A:** \*.meas files are files utilized by the Microwave Uncertainty Framework (MUF) to handle measurements with uncertainties.
These files are nothing more than eXtensible Markup Language (XML) files containing paths to nominal data, monte-carlo simulations, and perturbed results.

|

----

**Q:** How can I load \*.meas files with uncertainties?


**A:** These files can be loaded with all uncertainties using either :class:`samurai.base.SamuraiMeasurement.SamuraiMeasurement` or :class:`samurai.base.MUF.MUFResult.MUFResult`.
See the API documentation on each of these classes for more information.

|

----

Measurement Questions
------------------------

|

----

**Q:** How do I use PNAGrabber as opposed to :code:`PNAController` class when running :code:`SAMURAI_System.csv_sweep()`?

**A:** See :ref:`running-the-vna`

|

----

**Q:** How do I incorporate more devices into my sweeps?


**A:** Custom scripts will be required for this depending on the application. Running :code:`SAMURAI_System.csv_sweep()` multiple times with 
external information in multiple different metafiles can be a solution to this. 
Otherwise, developing a custom script based off of the code in :code:`SAMURAI_System.csv_sweep()` may provide the best results
without changing the metafile or file structure.







