.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _post-process:
	
Post-Processing the data
=================================

Tools
--------------

Basic tools for loading and working with the data produced by SAMURAI are included in the software.

The software includes both Python and MATLAB versions of :code:`TouchstoneEditor` for handling touchstone (e.g. *.snp) files along with 
versions of :code:`MetafileController` for handling the measurement metafiles (*.json).

The Python and MATLAB versions of :code:`TouchstoneEditor` can be found at 
 :mod:`samurai.base.TouchstoneEditor` and :mat:mod:`samurai.base.TouchstoneEditor` respectively.
 The Python and MATLAB versions of :code:`MetafileController` can be found at 
 :mod:`samurai.analysis.support.MetafileController` and :mat:mod:`samurai.analysis.support.MetafileController` respectively.

The following sections will cover the usage of these tools for processing the SAMURAI data.


Data Processing Example
---------------------------

Now we can walk through a basic example to post-process SAMURAI data using the tools introduced in the previous section.
This example will go over importing the library, loading the metafile and data, calculating a time domain response, 
beamforming the data, and calculating a beamformed time domain response. 

The generated plots use the data from :code:`2-13-2019/aperture_0/` which tested the reflection off a cylinder using a planar aperture. 
All python plotting is done using the Plot.ly library.

Importing the tools 
++++++++++++++++++++++++++

The first step that must be taken is to import the provided SAMURAI software tools.
In Python this is done using the :code:`import` keyword. In MATLAB, the folder of each tool must be added 
to the path using the :code:`addpath` function.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 2-10
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 2-10
   :linenos:

.. important:: When using the above MATLAB code, the user MUST set the :code:`samurai_root` variable to the directory where the SAMURAI code lives on their computer.


Loading the Metafile and Data
+++++++++++++++++++++++++++++++++++

Once the correct libraries and paths have been added, we can then use :code:`MetafileController` and :code:`TouchstoneEditor` to load in the metafile and measurement data.
The following code is an example of how this can be performed.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 12-31
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 12-31
   :linenos:


Plotting a Measurement 
+++++++++++++++++++++++++

It is useful to plot the data from a single point in the sweep before beamforming to verify the values are as expected and have been loaded correctly.
We can then also calculate the time domain version of the measured data using the :code:`ifft` to further verify the data is as expected.
The following code gives an example of how this can be done. Plotting with python is done using Plot.ly although this could be done with any number
of plotting packages. 

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 34-61
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 33-48
   :linenos:


As an example the frequency and time domain data from the first sweep position on :code:`2-13-2019/aperture_0` look as follows:

**Frequency Domain**

.. raw:: html
   :file: figs/single_fd.html

**Time Domain**

.. raw:: html
   :file: figs/single_td.html





Utilizing SAMURAI Tools for Post-Processing
=============================================
Here we have tools specifically for post processing algorithms like angle of arrival (AoA). 
There are also some base functions that may help users develop custom algorithms without having to rewrite routines for things such as loading data.

.. toctree::
   load_the_data
   :maxdepth: 2
   :caption: Contents:

Simple Python Beamforming Example
-----------------------------------
A simple analysis of the data is to perform conventional beamforming on the SAMURAI data. This can be done using the 
example :class:`samurai.analysis.support.SamuraiBeamform.SamuraiBeamform` that utilizes tools in other classes and serves
as an example on how a user could implement custom algorithms with relative ease. The following code is used to perform
beamforming on SAMURAI data using this class at a single measured frequency (40 GHz in this case).

.. code-block:: python 

   #import numpy
   import numpy as np

   #import the beamforming class
   from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform
   
   #provide a path to the metafile 
   metafile_path = "./path/to/metafile.json"

   #create our beamforming class 
   my_samurai_beamform = SamuraiBeamform(metafile_path,verbose=True)

   #add a hamming window to reduce sidelobes
   my_samurai_beamform.set_cosine_sum_window_by_name('hamming')
   
   #perform beamforming
   calc_synthetic_aperture = my_samurai_beamform.beamforming_farfield_azel(
                                   np.arange(-90,90,1),np.arange(-90,90,1),freq_list=[40e9])
   
   #plot our data in 3D
   myplot = calc_synthetic_aperture.plot_3d()

   #show the plot in a browser
   myplot.show(renderer='browser')

`myplot` then produces the following 3D representation of measured data at the synthetic aperture:

.. raw:: html
   :file: figs/3d_cup_test.html

.. note:: This plot is produced from the 8-12-2019 dataset in a highly multipath utility plant.

Making Custom algorithms
------------------------------------
The previous example utilizes abstracted libraries to perform coventional beamforming.
Custom post processing algorithms can easily be implemented by inheriting from the samurai.analysis.support.SamuraiPostProcess.SamuraiSyntheticApertureAlgorithm class.
Inheriting from this class provides the flexibility to define custom post processing functions while still providing the convenience
of tools for data IO, tapering, and plotting. Once the output data has been processed, it can be packed into the 
:class:`samurai.analysis.support.CalculatedSyntheticAperture.CalculatedSyntheticAperture` class. This class provides quick tools for tasks like plotting the data in a variety of formats.

Direct Extraction of measured data
-----------------------------------
If only measured data is desired (with no other tools), the measured data and positions of the synthetic aperture can be extracted using the following code:

.. code-block:: python
   
   #import the controller class
   from samurai.analysis.support.MetaFileController import MetaFileController
   
   #provide a path to the metafile 
   metafile_path = "./path/to/metafile.json"

   #load the metafile into an object
   mymetafile = MetaFileController(metafile_path)

   #load the S parameter data from the metafile 
   data = mymetafile.load_data(verbose=True)

   #extract S21 to data block
   block_data = np.array([d.S[21] for d in data])

   #get array position data corresponding to each set of values in the block_data list
   position_data = mymetafile.positions
   

With this code we have the raw data that was taken which can then be utilized for any post processing algorithm.


