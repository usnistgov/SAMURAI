
Taking a Measurement
=========================

#. Create a working directory

The first step for a new measurement is to create a new directory that will store all of the files for the measurement and all the data from the measurement.
This directory will be refered to from here on as :code:`<working_directory>`. 
The typical layout for the NIST measurement directory structure is given in :ref:`running-samurai-wdir` although it is not necessary to follow this layout.

#.Define an Aperture

A comma separated value (CSV) file must then be created or downloaded that describes the positions for the sweep.
Examples sweep files and more information on generating custom sweeps can be found in :ref:`creating-apertures`. 
The planar apertures can be downloaded and moved into :code:`<working_directory>`. For this example lets assume it is placed at
:code:`<working_directory>/position_templates/samurai_planar_dp.csv`.

#.Calibrate the System

At or before this point in time, the system should be calibrated.
This will be system and measurement dependent. 
Measurements taken on the NIST SAMURAI system measure SOLT standards before and after a measurement and perform calibration of data in post-processing. 
More info on the typical NIST SAMURAI calibration can be found in :ref:`Samurai Calibration Procedure`.

If, for example, a normal VNA calibration is being performed using the on-board software, no post-processing of the data is required.
The calibration can be performed once at this point in time and not again until the next measurement.

#.Run a Sweep 

With the system set up, calibrated, and the sweep defined, we can then begin the synthetic aperture measurement.





More information on running these measurements along with a sample script for controlling the NIST SAMURAI system can be found at :ref:`running-samurai`.




