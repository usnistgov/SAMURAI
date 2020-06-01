.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _samurai_data:

##############################
Data Information
##############################

Here we have information on each dataset stored at - :data_root:`./` measured using the SAMURAI system at the National Institute of Standards and Technology.

For examples on utilizing the samurai data please see the :ref:`analysis` section.

.. toctree::
   data_readme_2020
   data_readme_2019
   data_readme_2018
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

Calibration Information
---------------------------

All of the data was calibrated using the NIST Microwave Uncertainty framework. Most often a 2 port short-open-load-thru (SOLT) calibration performed 
at the face of the WR-28 waveguide section (right where the antenna is attached) using a keysight `WR-28 Calibration Kit <https://www.keysight.com/en/pd-1000000722%3Aepsg%3Apro-pn-R11644A/mechanical-calibration-kit-265-to-40-ghz-waveguide-wr-28?cc=US&lc=eng>`_.
The `Microwave Uncertainty Framework (MUF) <https://www.nist.gov/services-resources/software/wafer-calibration-software>`_
developed at national institute of standards and technology (NIST) is then used to apply the calibration to the data in post-processing.
For information on the calibration measurement process see :ref:`Samurai Calibration Procedure`.



