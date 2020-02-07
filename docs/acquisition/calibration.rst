
Samurai Calibration Procedure
=================================

1. Turn off the VNA Power (If Necessary)
------------------------------------------
If required to meet NIST safety standards, go to :code:`Stimulus->Power->Power...` and unclick the checkbox :code:`Power On (All Channels)` to turn off the VNA transmit power.

.. note:: While this is not typically necessary, for high powers and high gain horns, not doing this may be dangerous.


2. Unmount the antennas
---------------------------

#. Move the Meca500 into its mounting position with the following code to initialize the meca 

.. code-block:: python

    from samurai.acquisition.SAMURAI_System import SAMURAI_System
    mysam = SAMURAI_System()           # initialize the object
    mysam.connect_rx_positioner()      # connect to the Meca500
    mysam.zero()                       # zero its position
    mysam.move_to_mounting_position()  # move the Meca500 to its mounting position

#. Remove the three screws attaching the waveguide mount to the robot mount on the Meca500

.. note:: When using the open ended waveguide, the absorber mount must be removed before removing the waveguide mount

#. Remove the transmit antenna from its mount (typically also three screws attaching the waveguide mount)

#. Disconnect the antennas from the Intermediate waveguide section.


3. Setup the VNA sweep settings
----------------------------------

Before performing the waveguide calibration, the VNA sweep settings must be set for the measurement. 

- For automatically setting the sweep settings with :code:`set_vna_params.py`

    #. Open :code:`<working_directory>/synthetic_aperture/raw/set_vna_params.py` in Spyder or a text editor
    #. Set the desired sweep values in the script
    #. Run the script to set the VNA parameters

- For manually setting the sweep, go into the VNA and set the desired parameters 

For calibrations at multiple frequency ranges, a copy of :code:`set_vna_params.py` with a new name and the sweep settings for the other measurement.
Perform the waveguide calibration for each of these VNA settings in a different folder with a different PNAGrabber menu.

.. note:: For faster calibration, multiple PNAGrabber windows can be opened and for each standard, the following process can be followed:
            
            #. Connect the calibration standards
            #. Run :code:`set_vna_params_0.py` for the first sweep range
            #. Measure the standards with the first PNAGrabber window 
            #. Run :code:`set_vna_params_1.py` for the next sweep range
            #. Measure the standards with the next PNAGrabber window 
            #. Perform for as many sweep setups as needed


4. Perform the waveguide calibration 
------------------------------------------

#. Turn on the VNA power (If required) 
    
    - Go to :code:`Stimulus->Power->Power...` and click the checkbox :code:`Power On (All Channels)`
    - Setting the VNA sweep parameters may have already turned the power back on

#. Open the PNAGrabber template file at :code:`<working_directory>/cal/calibration_pre/cal.pnagrabber`.

.. note:: If a new measurement device such as a new VNA is in use, the networking address should be changed. See :ref:`Setting Up PNAGrabber` for more information.

#. Measure :code:`short_load.s2p`

    #. Connect a WR-28 short to port 1 and load to port 2 (The robot and transmit sides respectively)
    #. Make sure the measurement type is set to :code:`Normal`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`short_load.s2p` box in PNAGrabber and wait for the measurement to be completed

#. Measure :code:`load_short.s2p`

    #. Connect a WR-28 load to port 1 and short to port 2 (The robot and transmit sides respectively)
    #. Make sure the measurement type is set to :code:`Normal`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`load_short.s2p` box in PNAGrabber and wait for the measurement to be completed

#. Measure :code:`offsetShort.s2p`

    #. Connect a WR-28 offset short to port 1
    #. Make sure the measurement type is set to :code:`One at a time`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`offsetShort.s2p` box in PNAGrabber.
    #. A message box will show up with the message *Please connect standard to next port and press OK. DO NOT CLICK OK YET.
    #. Connect a WR-28 offset short to port 2
    #. Click the OK button on the message box to measure port 2

#. Measure :code:`offsetThru.s2p`

    #. Connect a WR-28 a shim between ports 1 and 2
    #. Make sure the measurement type is set to :code:`Normal`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`offsetThru.s2p` box in PNAGrabber and wait for the measurement to be completed

#. Measure :code:`thru.s2p`

    #. Remove the bolts from port 2 (the transmit side) and directly connect ports 1 and 2. The port 2 mount is specially designed to allow the removal of these bolts.
    #. Make sure the measurement type is set to :code:`Normal`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`load_short.s2p` box in PNAGrabber and wait for the measurement to be completed

#. Measure :code:`gthru.s2p`

    #. Remove the bolts from port 2 (the transmit side) and directly connect ports 1 and 2. The port 2 mount is specially designed to allow the removal of these bolts.
    #. Make sure the measurement type is set to :code:`Switch Terms`
    #. Measure the s-parameters by clicking the :code:`measure` button to the right of the :code:`load_short.s2p` box in PNAGrabber and wait for the measurement to be completed

#. Make a copy of all this data into the :code:`<working_directory>/cal/calibration_pre/raw` folder. This simply provides a copy of the raw data in case a problem arises.

.. note:: If only running a post calibration (e.g. no measurement the following day) These same steps should be performed in :code:`<working_directory>/cal/calibration_post`.

#. Make a copy of calibration data into :code:`<working_directory>/cal/calibration_post` for previous day (if applicable)


5. Create the Calibration Solution
-----------------------------------------

#. The previously described calibration routine is easy to calibrate but not ordered correctly for calibration of data. :code:`load_short.s2p` and :code:`short_load.s2p`
need to be reordered to get :code:`short.s2p` and :code:`load.s2p`. To reorder the data, simply run the :code:`swap_script_s-params.py` in the calibration directory.
The listing of this is as follows:

.. code-block:: python

    from samurai.base.TouchstoneEditor import SnpEditor

    # our file names
    ls_fn = 'load_short.s2p';
    sl_fn = 'short_load.s2p';

    #open classes to get data from
    ls = SnpEditor(ls_fn);
    sl = SnpEditor(sl_fn);

    s = SnpEditor([2,sl.freq_list/1e9])
    l = SnpEditor([2,ls.freq_list/1e9])

    #swap the data
    l.S[11] = ls.S[11]; l.S[22] = sl.S[22]
    l.S[21] = ls.S[21]; l.S[12] = sl.S[12]
    s.S[11] = sl.S[11]; s.S[22] = ls.S[22]
    s.S[21] = sl.S[21]; s.S[12] = ls.S[12]

    #set the header to write out GHz
    s.set_header('#GHz S RI 50')
    l.set_header('#GHz S RI 50')

    #write out the new files
    s.write('short.s2p');
    l.write('load.s2p');

#. Open :code:`cal_pre.vnauncert` in the current calibration directory. If running locally on the SAMURAI computer, use :code:`cal_pre_local.vnauncert` to have valid paths to the models.

#. Click on the :code:`Main calibration` tab and you should be greeted with the following:

#. Click :code:`Run->Calibrate` to calibrate the data. 

.. note:: If errors arise, the following may help:

        #. Verify that the file location/name under :code:`Location` is pointing to the folder that :code:`cal_pre.vnauncert` is in. If not, you will need to drag each of  the .s2p files into the :code:`Location` block. This should update the path.

            - Paths can also quickly be replaced by opening the \*.PNAGrabber

        #. Switch to the :code:`DUTs` tabs on :code:`cal_pre.vnauncert` .

        #. Drag the :code:`load.s2p` , :code:`open.s2p` , :code:`short.s2p` , and :code:`thru.s2p` into here so it looks like the following image

        .. image:: ../external_data/cal_pre_duts.png

        If this still does not work, please see the MUF documentation.

#. This will create a :code:`cal_pre_vnauncert_Results` directory containing a :code:`Solution.meas` file that will be used later to calibrate the measured data.

6. Remount the antennas
-------------------------------------

.. warning:: This applies to all parts of this section. DO NOT overtighten the mounting nuts. It will either become very difficult for the next user to undo them or warp the 3D printed parts of the mount. It is recommended to hand tighten and then snug with a half turn of the wrench.

#. Remount the antenna onto the Meca500 positioner. If the open ended waveguide is in use, also remount the absorber plate.

#. Remount the transmit antenna to its base

7. Zero and Disconnect from the Positioner 
----------------------------------------------

.. warning:: This step should only be performed after calibration and remounting have been completed. Make sure the cable is not twisted and will not get caught
            when moving to the robots zero position.

#. Move the Meca500 to its zero position and disconnect with the following code assuming that the robot has not been disconnected since originally moving it to its mounting position before the calibration:

.. code-block:: python 

    mysam.zero()
    mysam.disconnect_rx_positioner()

Other Calibration Information 
===============================
Other information on setting up things like files for the calibration are provided here.



.. _Setting Up PNAGrabber:

Setting Up PNAGrabber
-------------------------
#. Make sure your in :code:`<working-directory>/cal/calibration_pre` , from step 2.
#. Double click on :code:`cal.pnagrabber` to start PNA Grabber for the calibration.

 .. image:: ../external_data/cal_pre_pna_grabber_front_page.PNG

#. Verify that the front panel has the 5 different (assuming 2.4mm cal) .s2p files with the correct name and type as shown in the above figure. Make sure the Working Directory looks the same as in the picture. This is to ensure that all files are saved at the same level as PNAGrabber.
#. Change the settings on PNA Grabber:
    * Under :code:`Options> PNA Communication Settings> Address`, make sure this is pointing to the correct port the VNA is on (i.e. USB0::0x2A8D::0x2B01::SG49151012::INSTR)  as well as the correct communication method is selected (i.e USB or GPIB)
    * Under :code:`Options> PNA Port Mapping`, make sure the ports being used on the VNA are the ports you want mapped to the sNp file (i.e: Data File Port 1 is set to PNA Port 3 and Data File Port 2 is set to PNA Port 2). Make sure there is a checkmark next to :code:`PNA Port Mapping`
    * Under :code:`Options> IF Bandwidth Setting`, make sure this is set to the correct IF with unit of Hz (i.e 1000)
    * Dont forget to do a :code:`File> Save` as CTRL + S does not work!!

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


