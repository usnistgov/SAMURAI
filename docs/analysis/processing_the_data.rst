.. SAMURAI documentation master file, created by
   sphinx-quickstart on Mon Dec  9 09:14:57 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _post-process:
	
Post-Processing the data
=================================

Tools
--------------

Basic tools for loading and working with the data produced by SAMURAI are included in the software.

The software includes both Python and MATLAB versions of :code:`TouchstoneEditor` for handling touchstone (e.g. *.snp) files along with 
versions of :code:`MetafileController` for handling the measurement metafiles (*.json).

The Python and MATLAB versions of :code:`TouchstoneEditor` can be found at 
:mod:`samurai.base.TouchstoneEditor` and :mat:mod:`samurai.base.TouchstoneEditor` respectively.
The Python and MATLAB versions of :code:`MetafileController` can be found at 
:mod:`samurai.analysis.support.MetafileController` and :mat:mod:`samurai.analysis.support.MetafileController` respectively.

The following sections will cover the usage of these tools for processing the SAMURAI data.


Data Processing Example
---------------------------

Now we can walk through a basic example to post-process SAMURAI data using the tools introduced in the previous section.
This example will go over importing the library, loading the metafile and data, calculating a time domain response, 
beamforming the data, and calculating a beamformed time domain response. 

The generated plots use the data from :code:`2-13-2019/aperture_0/` which tested the reflection off a cylinder using a planar aperture. 
All python plotting is done using the Plot.ly library.

Importing the tools 
++++++++++++++++++++++++++

The first step that must be taken is to import the provided SAMURAI software tools.
In Python this is done using the :code:`import` keyword. In MATLAB, the folder of each tool must be added 
to the path using the :code:`addpath` function.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 2-10
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 2-10
   :linenos:

.. important:: When using the above MATLAB code, the user MUST set the :code:`samurai_root` variable to the directory where the SAMURAI code lives on their computer. For Python, the package must be installed (see :ref:`installation`).


Loading the Metafile and Data
+++++++++++++++++++++++++++++++++++

Once the correct libraries and paths have been added, we can then use :code:`MetafileController` and :code:`TouchstoneEditor` to load in the metafile and measurement data.
The following code is an example of how this can be performed.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 12-31
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 12-31
   :linenos:


Plotting a Measurement 
+++++++++++++++++++++++++

It is useful to plot the data from a single point in the sweep before beamforming to verify the values are as expected and have been loaded correctly.
We can then also calculate the time domain version of the measured data using the :code:`ifft` to further verify the data is as expected.
The following code gives an example of how this can be done. Plotting with python is done using Plot.ly although this could be done with any number
of plotting packages. 

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 33-60
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 33-48
   :linenos:


As an example the frequency and time domain data from the first sweep position on :code:`2-13-2019/aperture_0` look as follows:

**Frequency Domain**

.. raw:: html
   :file: figs/single_fd.html

**Time Domain**

.. raw:: html
   :file: figs/single_td.html


Beamforming the Data
+++++++++++++++++++++++++

With all of the measurement data loaded, we can perform conventional beamforming on the data to get angular information.
A simplified beamforming expression for a planar array is given by [1] and [2] as

.. math::
   :nowrap:

   \begin{align}
   S_{bf} = \frac{1}{N}\sum_{n=0}^{N} S_n e^{-jk(x_nu+y_nv)}
   \end{align}

where :math:`N` is the number of sweep positions, :math:`k` is our wavenumber at the beamformed frequency, :math:`x_n` and :math:`y_n` are the x and y location of the positions in meters,
:math:`S_n` is the measured value at each position, and :math:`u` and :math:`v` are given as

.. math::
   :nowrap:
   
   \begin{align}
   u &= \sin(az)\cos(el)\\
   v &= \sin(el)
   \end{align}

as in [3].
An azimuthal cut at 0 degrees elevation can then be generated with the following code.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 62-104
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 50-82
   :linenos:

Plotting the data again for :code:`2-13-2019/aperture_0` we can plot the result as magnitude vs azimuth angle in degrees at the first frequency point.

**Beamformed Result**

.. raw:: html
   :file: figs/beamformed.html


Response at One Angle
++++++++++++++++++++++++++++

In the last section we beamformed our data at a single frequency. We can also beamform across all frequencies at a single angle. 
The resulting data can provide the frequency response of the channel from a given direction. 
The time domain impulse response can then also be calculated from each angular frequency response.
Adding onto our previous code snippets, this can be performed using the code below.

**Python**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.py
   :language: python 
   :lines: 106-154
   :linenos:


**MATLAB**

.. literalinclude:: /../samurai/analysis/sample_scripts/process_data.m 
   :language: MATLAB
   :lines: 85-115
   :linenos:

Using the data from :code:`2-13-2019/aperture_0` to beamform all frequencies at -28 degrees azimuth and 0 degrees elevation we get:

**Frequency Domain**

.. raw:: html
   :file: figs/beamformed_fd.html

**Time Domain**

.. raw:: html
   :file: figs/beamformed_td.html


Data Processing Example Downloads
---------------------------------------

The above scripts can be downloaded in their entirety from the links below 

- :download:`Python Example </../samurai/analysis/sample_scripts/process_data.py>`
- :download:`MATLAB Example </../samurai/analysis/sample_scripts/process_data.m>`


.. rubric:: References

[1] R. L. Haupt, Antenna Arrays: A Computational Approach. Hoboken, NJ, USA: John Wiley & Sons, Inc., 2010.

[2] C. A. Balanis, Antenna Theory: Analysis and Design, 4 edition. Hoboken, New Jersey: Wiley, 2016.

[3] G. F. Masters and S. F. Gregson, “Coordinate System Plotting for Antenna Measurements,” p. 10.


