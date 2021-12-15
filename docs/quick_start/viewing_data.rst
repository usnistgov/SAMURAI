

Processing and Viewing the Data
=======================================

After a sweep has completed, the file in which the data was output should contain a number of \*.snp files equal to the number of positions that were swept over.
This file should also contain a 'metafile.json' and a 'metafile.raw' file. If the sweep finished correctly, the 'metafile.json' file contains all of the metadata in a javascript object notation (JSON)
file. The 'metafile.raw' is an intermediary storage file used during measurements and can be ignored.

#. Calibrate the Data

   Any required post-calibration should be performed at this point in time. Before usage, the data should also be run through any post processing algorithms.
   For example, the NIST SAMURAI system includes uncertainties in measurements through the use of the microwave uncertainty framework (MUF) for calibration.
   This calibration is performed after measurements have been taken.

#. Process the Data

    An in depth overview of processing the data can be found in the sections :ref:`metafile_info` and :ref:`post-process` under :ref:`analysis`

