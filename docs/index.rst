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

Introduction
----------------------

The National Institute of Standards and Technology (NIST) Communication Technology Laboratory (CTL) developed the Synthetic Aperture Measurement with Uncertainties
and Angle of Arrival (SAMURAI) millimeter-wave testbed and technique. SAMURAI utilizes a synthetic aperture method using a robotic arm and vector network analyzer/large signal network analyzer (VNA/LSNA) for flexible and accurate propagation channel and device measurements as a function of both frequency and angle. Note: this technique can use a measurement tool.

In the NIST configuration of SAMURAI, linear and non-linear measurements are possible leveraging the large signal network LSNA measurement capability. We perform wideband measurements from 26.5 to 40 GHz on an optical table in a controlled laboratory to ensure stability during our measurements. The robotic arm allows for multiple configuration scan types from rectangular to cylindrical.

In this documentation, we provide a getting started documentation, software for both data acquisition and data analysis. We also provide past measurement campaigns data from an Angle-of-Arrival measurements to the Central Utility Plant measurements. Finally, we provide base software libraries and frequently asked questions.



.. image:: ./external_data/image_authors.jpg

*Rod Leonhardt, Alec Weiss, and Jeanne Quimby (left to right) setting up the SAMURAI system.*

This documentation describes how the system is run, the data is stored, and options on how it can be processed.

Getting started
++++++++++++++++++++

For first time users trying to get up and started please go to :ref:`quick_start`.

Documentation Layout
++++++++++++++++++++++++++

This documentation is separated into a few main sections:

- :ref:`quick_start` provides a brief introduction on how to get started measuring and processing data.
- :ref:`data_acquisition` includes information on how to set up a measurement system utilizing similar hardware and software to the NIST system.
- :ref:`analysis` includes information on how to calibrate, load, and process data taken with the SAMURAI (or similar) system.
- :ref:`samurai_data` provides data and information on measurements taken with the NIST SAMURAI system.
- :ref:`api` gives in depth information on each module, class, and function of the code.
- :ref:`faq` answers some commonly asked questions.

Table of Contents
------------------------

.. toctree::
   quick_start/index
   :maxdepth: 2
   :numbered:
   :caption: Quick Start:

.. toctree::
   acquisition/index
   analysis/index
   data/index
   :maxdepth: 2
   :numbered:
   :caption: Contents:

.. toctree::
   api/index
   faq
   :maxdepth: 1
   :numbered:
   :caption: Other Information:


Authors
-----------------
- Alec Weiss (alec.weiss@nist.gov)
- Jeanne Quimby (jeanne.quimby@nist.gov)
- Ben Jamroz (benjamin.jamroz@nist.gov)
- Rod Leonhardt (rodney.leonhardt@nist.gov)
- Peter Vouras (peter.vouras@nist.gov)
- Kate Remley (kate.remley@nist.gov)
- Dylan Williams (dylan.williams@nist.gov) 
- NIST SAMURAI Team


Copyright Notice
-----------------------
This software was developed by employees of the National Institute of Standards and Technology (NIST), an agency of the Federal Government and is being made available as a public service. Pursuant to title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.  This software may be subject to foreign copyright.  Permission in the United States and in foreign countries, to the extent that NIST may hold copyright, to use, copy, modify, create derivative works, and distribute this software and its documentation without fee is hereby granted on a non-exclusive basis, provided that this notice and disclaimer of warranty appears in all copies. 

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE.  IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
