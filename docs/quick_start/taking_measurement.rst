
Taking a Measurement
=========================

Create a working directory
--------------------------------

    The first step for a new measurement is to create a new directory that will store all of the files for the measurement and all the data from the measurement.
    This directory will be refered to from here on as :code:`<working_directory>`. 
    The typical layout for the NIST measurement directory structure is given in :ref:`running-samurai-wdir` although it is not necessary to follow this layout.

Define an Aperture
--------------------------------

    A comma separated value (CSV) file must then be created or downloaded that describes the positions for the sweep.
    Examples sweep files and more information on generating custom sweeps can be found in :ref:`creating-apertures`. 
    The planar apertures can be downloaded and moved into :code:`<working_directory>`. For this example lets assume it is placed at
    :code:`<working_directory>/position_templates/samurai_planar_dp.csv`.

Calibrate the System
--------------------------------

    At or before this point in time, the system should be calibrated.
    This will be system and measurement dependent. 
    Measurements taken on the NIST SAMURAI system measure SOLT standards before and after a measurement and perform calibration of data in post-processing. 
    More info on the typical NIST SAMURAI calibration can be found in :ref:`Samurai Calibration Procedure`.

    If, for example, a normal VNA calibration is being performed using the on-board software, no post-processing of the data is required.
    The calibration can be performed once at this point in time and not again until the next measurement.

Mount the Antennas
--------------------------------

    After calibration, it is likely the user will have to then mount the antennas onto the robotic positioner. 
    In many situations it is likely to be difficult to mount the antennas when the robot is zeroed, therefore a predefined mounting position was defined.
    To move the robot to the mounting position, connect to the robot with 

    .. code-block:: python 

        # Import the library
        from samurai.acquisition.SamuraiSystem import SamuraiSystem 

        # Initialize the object providing the VNA visa address and the robot IP address (likely 192.168.0.XXX)
        mysam = SamuraiSystem(vna_visa_address='MY::VISA::ADDRESS',rx_positioner_address='192.168.0.XXX')

        mysam.connect_rx_positioner()      # connect to the Meca500
        mysam.zero()                       # zero its position
        mysam.move_to_mounting_position()  # move the Meca500 to its mounting position

    This mounting position is located to the lower left when looking from behind the robot. The robot can then be returned to its zero position and disconnected after mounting with 

    .. code-block:: python 

        # Zero
        mysam.zero()

        # Disconnect
        mysam.disconnect_rx_positioner()

Run a Sweep 
--------------------------------

    With the system set up, calibrated, mounted, and the sweep defined we can then begin the synthetic aperture measurement. Each of the commands described in this section
    will be assumed to be run in :code:`<working_directory>`.

    We can begin by defining any metadata that we may want to include with the measurement. This is done by passing key/value pairs in the form of a dictionary.
    For example, the NIST SAMURAI measurements usually include the following

    .. code-block:: python 

        from collections import OrderedDict

        metafile_info_dict = {}
        metafile_info_dict["experiment"] = 'test experiment'
        metafile_info_dict["experiment_photo_path"] = "../external_data/pictures/"
        rx_ant = OrderedDict()
        rx_ant["name"]          = "Sage Millimeter 17dBi rectangular horn (SAR-1725-28-S2)"
        rx_ant["txrx"]          = "rx"
        rx_ant["location"]      = None
        rx_ant["gain_dbi"]      = 17
        rx_ant["beamwidth_e"]   = 23
        rx_ant["beamwidth_h"]   = 24
        rx_ant["serial_number"] = "14172-01"
        tx_ant1 = OrderedDict()
        tx_ant1["name"]          = "Sage Millimeter 17dBi rectangular horn (SAR-1725-28-S2)"
        tx_ant1["txrx"]          = "tx"
        tx_ant1["location"]      = None
        tx_ant1["gain_dbi"]      = 17
        tx_ant1["beamwidth_e"]   = 23
        tx_ant1["beamwidth_h"]   = 24
        tx_ant1["serial_number"] = "14172-02"
        metafile_info_dict["antennas"] = [rx_ant,tx_ant1]
        metafile_info_dict["notes"] = "Here we can write some more complicated Notes on the measurement"

    This metadata can include anything that the user wants and will be included in the final metafile output after the sweep is completed.
    We can then connect to the positioner and run the measurement using the sweep defined in our position file. The following code will place all measurements
    in the directory which it is executed (assumed to be :code:`working_directory`).

    .. code-block:: python 

        # Import the library
        from samurai.acquisition.SamuraiSystem import SamuraiSystem

        # Initialize the object providing the VNA visa address and the robot IP address (likely 192.168.0.XXX)
        mysam = SamuraiSystem(vna_visa_address='MY::VISA::ADDRESS',rx_positioner_address='192.168.0.XXX')

        # Connect to the Meca500
        mysam.connect_rx_positioner()  

        # Perform the sweep 
        mysam.csv_sweep('./','./position_templates/samurai_planar_dp.csv,metafile_header_values=metafile_info_dict)

        # Disconnect when finished   
        mysam.diconnect_rx_positioner()




    The :meth:`samurai.acquisition.SamuraiSystem.SamuraiSystem.csv_sweep` method performs the coordination of multiple systems used in the NIST SAMURAI system and sets many values by default.
    The robot can also be controlled using :class:`samurai.acquisition.instrument_control.Meca500`, but this removes many of the checks in place to insure damage to the system and therefore extra caution should be taken when controlling the robot directly.
    The metafiles can also be created without :meth:`samurai.acquisition.SamuraiSystem.SamuraiSystem.csv_sweep` by directly using the 
    :class:`samurai.acquision.support.SamuraiMetafile.SamuraiMetafile` with the :code:`SamuraiMetafile.init()`, :code:`SamuraiMetafile.update()`, and :code:`SamuraiMetafile.finalize()` methods.
    More information on running these measurements along with a sample script for controlling the NIST SAMURAI system can be found at :ref:`running-samurai`.





