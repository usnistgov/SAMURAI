

Other SAMURAI Tools for Post-Processing
=============================================
The SAMURAI code also contains some Python tools specifically for post processing algorithms like angle of arrival (AoA). 


SAMURAI Beamforming Library
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


Leveraging for Custom algorithms
------------------------------------

The previous example utilizes abstracted libraries to perform coventional beamforming.
Custom post processing algorithms can easily be implemented by inheriting from the samurai.analysis.support.SamuraiPostProcess.SamuraiSyntheticApertureAlgorithm class.
Inheriting from this class provides the flexibility to define custom post processing functions while still providing the convenience
of tools for data IO, tapering, and plotting. Once the output data has been processed, it can be packed into the 
:class:`samurai.analysis.support.CalculatedSyntheticAperture.CalculatedSyntheticAperture` class. 
This class provides quick tools for tasks like plotting and retrieving the data in a variety of formats.
