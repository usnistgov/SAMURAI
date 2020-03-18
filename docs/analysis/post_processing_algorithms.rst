.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _post-process:
	
SAMURAI Post Processing Algorithms
========================================
Here we have tools specifically for post processing algorithms like angle of arrival (AoA).

.. toctree::
   metafile
   :maxdepth: 2
   :caption: Contents:

Simple Python Beamforming Example
-----------------------------------
A simple analysis of the data is to perform conventional beamforming on the SAMURAI data. This can be done using the 
example class samurai.analysis.support.SamuraiBeamform.SamuraiBeamform that utilizes tools in other classes and serves
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
samurai.analysis.support.CalculatedSyntheticAperture.CalculatedSyntheticAperture class. This class provides quick tools for tasks like plotting the data in a variety of formats.

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


Algorithm code
----------------

.. automodule:: samurai.analysis.support.SamuraiPostProcess
	:members:

.. automodule:: samurai.analysis.support.SamuraiCalculatedSyntheticAperture
	:members:

.. automodule:: samurai.analysis.support.SamuraiBeamform
	:members:
