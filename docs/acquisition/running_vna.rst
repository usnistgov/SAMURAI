
.. _running-the-vna:

Remotely Controlling the VNA
====================================

The VNA is typically controlled remotely from a connected computer. 
In the SAMURAI lab, this is typically connected over ethernet. Communication is performed using the VISA protocol.
The current IP address for the VNA in the SAMURAI lab is given in :ref:`hardware-config`.

There are two methods for remotely running the VNA from the computer using the SAMURAI software. 
The first is using the custom :class:`samurai.acquisition.support.PnaController.PnaController` class and the second is using PNAGrabber with :class:`samurai.acquisition.support.AutoPnaGrabber.PnaGrabber`(the NIST microwave uncertainty framework must be installed).

Using PnaController 
--------------------------

This section describes the use of the :class:`samurai.acquisition.support.PnaController.PnaController` class.
While this method cannot yet do wave parameters, it is faster to measure than PnaGrabber for s-parameter measurements (especially when a sweep contains thousands of points).
This class also does not in any way alter the state of the VNA (PNAGrabber will overwrite some settings).
An example of how this class can be used is as follows:

.. code-block:: python 

    # Import the library
    from samurai.acquisition.instrument_control.PnaController import PnaController
    
    # Create the object
    mypna = PnaController()

    # Take a measurement
    mypna.measure('path/to/file.s2p')

OR when a port mapping is required, something like the following:

.. code-block:: python 

    # Import the library
    from samurai.acquisition.instrument_control.PnaController import PnaController
    
    # Create the object
    mypna = PnaController()

    # Take a measurement and map port 3 data to port 2 in *.snp file 
    mypna.measure('path/to/file.s2p',{3:2})

This class can also be used to repeatably setup the VNA for a certain sweep. An example script showing this functionality is given below

.. literalinclude:: /../samurai/acquisition/script_templates/set_vna_params.py 
	:language: python 
	:linenos:


Using PNAGrabber
---------------------
Using PNAGrabber to communicate with the VNA has the added benefit of setting up a PNAGrabber menu and gathering data as if clicking the :code:`meas_all` button in PNAGrabber.
This works for s-parameters and wave-parameters with an arbitrary number of ports. This is performed using the :class:`samurai.acquisition.support.AutoPnaGrabber.PnaGrabber` class.

To gather a measurement using PNAGrabber, first make a template pnagrabber menu. This is what will be run each time.
This menu should have only a single measurement with the correct extension (e.g. \*.s2p,\*.s4p,\*.w2p).


.. _Setting Up PNAGrabber:

Setting up PNAGrabber 
++++++++++++++++++++++++++++++

#. Make sure your in :code:`<working-directory>/cal/calibration_pre` , from step 2.
#. Double click on :code:`cal.pnagrabber` to start PNA Grabber for the calibration.

 .. image:: ./external_data/cal_pre_pna_grabber_front_page.PNG

#. Change the settings on PNA Grabber:
    * Under :code:`Options> PNA Communication Settings> Address`, make sure this is pointing to the correct port the VNA is on (i.e. USB0::0x2A8D::0x2B01::SG49151012::INSTR)  as well as the correct communication method is selected (i.e USB or GPIB)
    * Under :code:`Options> PNA Port Mapping`, make sure the ports being used on the VNA are the ports you want mapped to the sNp file (i.e: Data File Port 1 is set to PNA Port 3 and Data File Port 2 is set to PNA Port 2). Make sure there is a checkmark next to :code:`PNA Port Mapping`
    * Under :code:`Options> IF Bandwidth Setting`, make sure this is set to the correct IF with unit of Hz (i.e 1000)
    * Dont forget to do a :code:`File> Save` as CTRL + S does not work!!

By default the python wrapper expects that this template menu is in the working directory and named 'template.pnagrabber' (so it has the relative path './template.pnagrabber' from the running code typically).
If a different template path is desired, pass the keyword parameter :code:`pnagrabber_template_path='path/to/template.pnagrabber'` when instantiating the :code:`PnaGrabber` class.

Calling PNAGrabber from Python 
++++++++++++++++++++++++++++++++++

Once this has all been setup, PNAGrabber can be used to measure with the following code:

.. code-block:: python 

    #import the library
    from samurai.acquisition.support.AutoPnaGrabber import PnaGrabber 

    # Create an object
    mypna = PnaGrabber()

    # Set the output path (with correct extension)
    output_path = 'path/to/output/file.s2p'

    # Run a measurement 
    mypna.measure(output_path)


Using different methods with SAMURAI_System.csv_sweep()
--------------------------------------------------------------

When running a typical SAMURAI Sweep using the :method:`samurai.acquisition.SAMURAI_System.SAMURAI_System.csv_sweep` method,
the system will default to using the PnaController class and using ports 1 and 3.
This can be changed with the optional input arguments :code:`meas_obj`,:code:`meas_obj_init_args`,:code:`meas_obj_meas_args`

To utilize PnaController without any port mapping, the following keywork arguments should be passed into the csv_sweep method:

.. code-block:: python 

    # This code only demonstrates what flags to set, not how to use the csv_sweep method 
    SAMURAI_System.csv_sweep(...,meas_obj_meas_args=())

In order to use PNAGrabber with the sweep, the following keyword arguments can be used:

.. code-block:: python 

    # This code only demonstrates what flags to set, not how to use the csv_sweep method 
    from samurai.acquisition.support.autoPNAGrabber import PnaGrabber
    SAMURAI_System.csv_sweep(...,meas_obj=PnaGrabber,meas_obj_init_args=(),meas_obj_meas_args=())
