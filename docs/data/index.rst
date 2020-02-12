.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


SAMURAI Data Information
==========================

Here we have information on each dataset stored at - :data_root:`./` measured using the SAMURAI system at the National Institute of Standards and Technology.

For examples on utilizing the samurai data please see the :ref:`SAMURAI Data Analysis` section.

.. toctree::
   data_readme.rst
   :maxdepth: 2
   :caption: Contents:

Calibration Information
---------------------------

All of the data was calibrated using the NIST Microwave Uncertainty framework. Most often a 2 port short-open-load-thru (SOLT) calibration performed 
at the face of the WR-28 waveguide section (right where the antenna is attached) using a keysight `WR-28 Calibration Kit <https://www.keysight.com/en/pd-1000000722%3Aepsg%3Apro-pn-R11644A/mechanical-calibration-kit-265-to-40-ghz-waveguide-wr-28?cc=US&lc=eng>`_.
The `Microwave Uncertainty Framework (MUF) <https://www.nist.gov/services-resources/software/wafer-calibration-software>`_
developed at national institute of standards and technology (NIST) is then used to apply the calibration to the data in post-processing.





