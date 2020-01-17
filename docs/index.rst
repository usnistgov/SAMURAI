.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SAMURAI's documentation!
===================================

- [S]ynthetic
- [A]perture
- [M]easurements with
- [U]nce[R]tainty and
- [A]ngle of
- [I]ncidence

Intoduction
----------------------

The SAMURAI system is a high accuracy millimeter-wave (mmWave) over the air (OTA) measurement system that utilizes a synthetic aperture method.
This system provides a testbed for a variety of OTA channel and device measurements as a function of both frequency and angle developed at the National Institute of Standards and Technology (NIST).
This system is designed to be both highly flexible and accurate utilizing a large signal network analyzer (LSNA) for measurement.
The LSNA allows the system to perform both linear and non-linear measurements along with a variety of other methods that are currently being researched at NIST.
The LSNA also allows very wideband measurements. Typically measurements are taken to match the operating frequency of the antenna which in most cases has been 26.5 GHz to 40 GHz
Typically the system resides on an optical table which provides stability over the possibly long measurement times. This also provides attachment points 
to repeatably reconfigure for a variety of different setups.    

.. image:: ./external_data/samurai_dual_cyl.jpg

*SAMURAI System Set up to test the scattering off of two cylinders. This test is used to test the angular resolution of different angle of arrival (AoA) algorithms.*

This documentation describes how the system is run, the data is stored, and options on how it can be processed.


Table of Contents
------------------------

.. toctree::
   acquisition/index
   analysis/index
   data/index
   base/index
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
