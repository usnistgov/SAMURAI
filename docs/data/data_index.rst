.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


###################
Datasets
###################

.. toctree::
   data_readme_2018
   data_readme_2019
   data_readme_2020
   :maxdepth: 2
   :caption: Data Sets By Year:

Dataset Information
===========================

The folders are named in the following manner

	(month)-(date)-(year)

Within each folder there is a subfolder named '/calibrated' This folder contains the most up to date calibrated data for the run and that data 
should be used for calculations.

Each subfolder within this folder contains data from a measurement. Within each of these subfolders there exists a set of measurements named 'meas#.s2p'
and a metafile named 'metaFile.json'. This metafile contains almost all information regarding to the measurement setup and run.

metaFile Description
---------------------------

The metafile is a \*.json file (typically under the name metaFile.json) that provides useful information to both load and track information on the measurements
This file is easily human readable and information on the experiment can be found at the top of the file. The following set of keys are 
the most useful within the file

 - 'working_directory' : provides the path to the current directory
 - 'experiment' : very brief info on the experiment
 - 'vna_info' : a dictionary with information on the VNA settings used during the experiment
 - 'antennas' : a list of dictionaries describing characteristics of the antennas used
 - 'notes' : More information about the experiment
 - 'measurements' : a list of dictionaries containing the following info
 
    - 'position_key' : what each position is
    - 'position'     : position used for each value in position_key
    - 'filename'     : location of the file (relative to working_directory) of the file

There are a few other keys within the file but these are the most useful. A 'units' key has been added in later versions to give the units of the axes

For more information see :ref:`metafile_info`


