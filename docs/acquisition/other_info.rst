
Other Useful Acquisition Information
+++++++++++++++++++++++++++++++++++++++

Other Calibration Information 
===============================
Other information on setting up things like files for the calibration are provided here.

.. _Setting Up PNAGrabber for Calibration:

Setting Up PNAGrabber for Calibration
------------------------------------------
For more information on basic measurements with the VNA, see :ref:`running-the-vna`

#. Make sure your in :code:`<working-directory>/cal/calibration_pre` , from step 2.
#. Double click on :code:`cal.pnagrabber` to start PNA Grabber for the calibration.

 .. image:: ./external_data/cal_pre_pna_grabber_front_page.PNG

#. Verify that the front panel has the 5 different (assuming 2.4mm cal) .s2p files with the correct name and type as shown in the above figure. Make sure the Working Directory looks the same as in the picture. This is to ensure that all files are saved at the same level as PNAGrabber.
#. Change the settings on PNA Grabber:
    * Under :code:`Options> PNA Communication Settings> Address`, make sure this is pointing to the correct port the VNA is on (e.g., USB0::0x2A8D::0x2B01::SG49151012::INSTR)  as well as the correct communication method is selected (i.e USB or GPIB)
    * Under :code:`Options> PNA Port Mapping`, make sure the ports being used on the VNA are the ports you want mapped to the sNp file (e.g., Data File Port 1 is set to PNA Port 3 and Data File Port 2 is set to PNA Port 2). Make sure there is a checkmark next to :code:`PNA Port Mapping`
    * Under :code:`Options> IF Bandwidth Setting`, make sure this is set to the correct IF with unit of Hz (e.g., 1000)
    * Don't forget to do a :code:`File> Save` as CTRL + S does not work!!

.. note:: There is an alternate method to get VNA measurements rather than using PNAGrabber. 
         For measurements with very large numbers of points (5000+ VNA points) PNAGrabber may become slow to transfer the data from the VNA.
         An alternate way of taking VNA data (not including switch terms) is to open Spyder, running :code:`set_vna_params.py` to set the parameters,
         and then in the Spyder Console type:

         .. code-block:: python 

            from samurai.acquisition.instrument_control.PnaController import PnaController
            mypna = PnaController()
            mypna.measure('path/to/file.s2p')

         OR 

         .. code-block:: python 

            from samurai.acquisition.instrument_control.PnaController import PnaController
            mypna = PnaController()
            mypna.measure('path/to/file.s2p',{3:2})

        when measuring on ports 1 and 3 (which is common in SAMURAI).


Running Python Scripts
============================

This section explains how to run the python scripts that are mentioned in this document

Running with the Spyder IDE
-----------------------------

1. Open the Spyder IDE (Make sure to use Python 3.x not 2.x)
2. Open the script in Spyder
3. Press the Green play button at the top of the window

Running from the Anaconda command prompt
-----------------------------------------

1. Run the program :code:'Anaconda Prompt'
    - This can be done by searching for this in the Windows toolbar
2. In the prompt type :code:`python <script_directory>/<script_name>.py` where :code:`<script_directory>` and :code:`<script_name>` create the path to your script

Mounting and Unmounting the antennas
==========================================

Moving the Positioner to the mounting position
----------------------------------------------------

The robotic positioner can be moved to a location that is easier to mount/unmount the antennas with the following code:

.. code-block:: python

	from samurai.acquisition.SAMURAI_System import SAMURAI_System
	mysam = SAMURAI_System()            #initialize the class
	mysam.connect_rx_positioner()       #connect and home the positioner
	mysam.move_to_mounting_position()   #move to the mounting position


Once the antennas have been remounted, return the positioner to its home position and disconnect with the following code:

.. code-block:: python

	mysam.zero()                        #move back to its home position
	mysam.disconnect_rx_positioner()    #disconnect the positioner


Connecting the antennas
-----------------------------

Both the transmit and receive antenna should always be contained in a 3D printed mounting holder. The newest version of this holder will have 3 steel ball bearings that fit into grooves on the Robot mount. Slide the antenna and its mount into the receiving side on the robot and connect the three 3mm nuts to snugly hold together the antenna and receiving mount. DO NOT OVERTIGHTEN THESE NUTS. The connection only needs to be lightly tightened (finger tight plus 1 turn or so). Overtightening will warp the plastic and damage the mount.

Demo the SAMURAI System
===========================

A script has been made to run quick demonstration of the SAMURAI system. This demo will do the following:

1. Perform a 35x35 element planar sweep at 40 GHz
2. Measure and plot 3D beamformed data for the current channel
3. Measure and plot a PDP from the measured frequency range start/stop/step = 26.5GHz/40GHz/10MHz at a single aperture position

Running the Demo
----------------------------

In order to run the demo the following steps must be taken

1. Open the Spyder IDE or the Anaconda command prompt
2. Run the script `\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\demo\quick_beamform_demo\channel_test.py`

    - See the 'Running Python Scripts' section for instructions on how to run this file

