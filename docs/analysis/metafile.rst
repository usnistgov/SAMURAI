.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

	
Interacting with the metafile
====================================
Interaction with the metafile can easily be performed using the samurai.analysis.support.MetaFileController.MetafileController.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Loading in a Metafile Object
-------------------------------
A metafile can be loaded using the following code

.. code-block:: python
   
   #import the controller class
   from samurai.analysis.support.MetaFileController import MetaFileController
   
   #provide a path to the metafile 
   metafile_path = "./path/to/metafile.json"

   #load the metafile into an object
   mymetafile = MetaFileController(metafile_path)

Loading the data
-------------------
The file paths of each measurement can be retrieved with ``MetaFileController.filenames`` property. 
The position of the synthetic aperture from each measurement can be retrieved with the ``MetaFileController.positions`` property.
The data from each of the files can be loaded as samurai.base.TouchstoneEditor.TouchstoneEditor objects using the ``MetaFileController.load_data()`` method.

Loading external positioning information
-----------------------------------------
Later SAMURAI measurements use an Optitrack optical positioning system to provide positoning information on multiple points in the measurement such
as the transmit and recieve antennas, and possible scatterers in the scene. A dictionary with data on each marker can quickly be extracted from the metafile using the 
the metafile using the ``MetaFileController.get_external_positions()`` method.


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

.. automodule:: samurai.analysis.support.MetaFileController
    :members:

MATLAB
++++++++++++
    
.. mat:automodule:: samurai.analysis.support 
.. mat:autoclass:: SamuraiMetafile 
    :members:




