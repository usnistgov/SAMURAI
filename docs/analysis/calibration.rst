Calibrating the Data
===========================

Before any other post-processing steps are performed, all data should be calibrated. 

.. note:: Any data listed in :ref:`_samurai_data` will already be calibrated, but for any new data the following steps must be taken.

Calibration is typically performed using a script that calls the :class:`samurai.analysis.calibration.CalibrateSamurai`.
This is only for VNA (or LSNA) based measurements performing calibrations on raw measured data NOT calibrated directly with the VNA (or LSNA).

With the typical SAMURAI directory structure, the script template from :mod:`samurai.analysis.calibration.script_templates.calibrate`
lays out a common way the data will be calibrated. This script utilizes a measurement metafile (*.json file) along with a microwave uncertainty framework (MUF)
post-processor template (*.post) which are located in the :code:`samurai/analysis/calibration/templates` directory.

The metafile will first be split in the case of multiple sweeps taken during a single measurement (e.g. vertical and horizontal polarization)
This script will then populate a post-processor file with the settings from the template and the files from the metafile for each of the split measurements.
This file will automatically be saved and run and all the measurement data will be calibrated in the provided output directory and split subdirectories.

After all of the data is calibrated, a copy of each of the measurement (*.meas) files is copied into the base output directory for easier access.
A copy of only the touchstone data (*.snp) will be created along with a new metafile in the :code:`touchstone/` subdirectory.

The code listing for this example calibration script is given as:

.. module:: samurai.analysis.calibration.script_templates.calibrate
.. data::   samurai.analysis.calibration.script_templates.calibrate

.. literalinclude:: /../samurai/analysis/calibration/script_templates/calibrate.py 
	:language: python 
	:linenos:

where :code:`<measurement-year>` and :code:`<measurement-date-mm-dd-yy>` in :code:`output_directory` will typically be replaced with 
the year and date (in mm-dd-yy) format when using the NIST system.
The variable :code:`out_folder_labels` should be provided as a list of descriptive names of the multiple aperture sweeps contained in the metafile.
If only a single sweep was taken, this should be a list of only a single subdirectory name (e.g. :code:`['mymeasurement']`).


