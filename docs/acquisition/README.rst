
Acquisition Software
=====================

This information pertains to data acquisition using the SAMURAI system. The code has been tested lately with python 3.7. 
This set of libraries uses some common python libraries. The code can be cloned from the NIST internal Gitlab server.

dependencies
------------------

- Anaconda with python 3.X
- pyvisa
- cannot remember the last one

Installing Anaconda and Dependencies
--------------------------------------

- Install Anaconda
    1. Go to the anaconda `download page <https://www.anaconda.com/distribution/#download-section>`_
    2. Select the correct operating system and installer
    3. Download and run the executable and follow the installer to install Anaconda 3.X
- Install pyvisa
    1. Type into the windows search 'anaconda prompt' and run the program
    2. In the terminal run `conda install -c conda-forge pyvisa` to install pyvisa

Hardware
===========

(PICTURE OF SETUP)

Meca 500 6 axis positioner
-------------------------------

Small 6 axis positioner.

- `Mecademic Website <https://www.mecademic.com/products/Meca500-small-robot-arm>`_
- `Meca500 R3 User Manual <https://www.mecademic.com/Documentation/Meca500-R3-User-Manual.pdf>`_
- `Meca500 R3 Programming Manual <https://www.mecademic.com/Documentation/Meca500-R3-Programming-Manual.pdf>`_

Keysight PNA-X (N5245A)
----------------------------

10MHz to 50GHz VNA. Ports are 2.4mm Male typically with 2.4mm F-F connector savers on them.

- `N5245A Datasheet <https://literature.cdn.keysight.com/litweb/pdf/N5245-90008.pdf>`_

Antennas
--------------

- Sage-millimeter 17dBi WR-28 Horn antenna  
   - `17 dBi WR-28 Sage Horn Datasheet <https://www.sagemillimeter.com/content/datasheets/SAR-1725-28-S2.pdf>`_

- Sage-millimeter 23dBi WR-28 Horn antenna  
   - `23 dBi WR-28 Sage Horn Datasheet <https://www.sagemillimeter.com/content/datasheets/SAR-2309-28-S2.pdf>`_


Cables
------------

- Junkosha 2.4mm (M-M) 3m Cables (MWX251)
- Junkosha 2.4mm (M-M) 0.25m Cables (MWX251)

.. seealso:: http://www.junkosha.co.jp/english/products/cable/c03.html

Adapters
-------------

- Sage-millimeter 2.4mm to WR-28 right angle adapters
   - `WR-28 to 2.4mm Female Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-282F-R1.pdf>`_
   - `WR-28 to 2.4mm Male Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-282M-R1.pdf>`_

- Sage-millimeter K (2.92mm) to WR-28 right angle adapters
   - `WR-28 to K Female Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-28KF-R1.pdf>`_
   - `WR-28 to K Male Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-28KM-R1.pdf>`_


Networking
--------------

Currently, the samurai system is run over a custom local network run through a simple network switch. This connects to the VNA, Meca500 Robot arm, and eventually cameras.

Remote PNA-X control
------------------------

A remote Keyboard, Video, Mouse box is used. This allows a keyboard, monitor, and a mouse to be placed far away from our VNA and a single CAT-5 cable (ethernet) to be run between the two. This comprises of a small box with 2 usb ports and a VGA connection. This box is then connected directly via a CAT-5 Cable near the VNA with a usb-B output and a second VGA connection. These two boxes provide remote control over the VNA
.. NOTE: This is not connected to the local network. These two boxes are only connected to one another and cannot be run over a network. They simply translate the usb and VGA info and transmit over a CAT-5 cable.

IP and VISA Addresses
------------------------

- PNA-X 
   - IP Address   = `192.168.0.2 <http://192.168.0.2>`_
   - VISA Address = 'TCPIP0::10.0.0.2::inst0::INSTR'

- Meca500
   - IP Address   = `192.168.0.5 <http://192.168.0.5>`_ 
   - VISA Address = Could not get VISA to work correctly! Connect using sockets.

- IP Webcam 
   - IP Address   = `192.168.0.11 <http://192.168.0.11>`_ 
   - Username: :code:`admin` -- Password: :code:`123456`
   - A live stream will show up if you go to the above address and login
   - A VLC stream has higher latency but can be connected by the following steps:
      #. Open VideoLAN (VLC with the construction cone icon)
      #. Select :code:`Media->Open Network Stream...`
      #. Enter :code:`rtsp://admin:123456@192.168.0.11:554/cam1/mpeg4` and click connect
      #. To take a snapshot click :code:`Video->Take Snapshot`. This will save a snapshot to the users `Pictures` folder from which it can then be renamed and copied
         - The VLC stream has not always been reliable and may freeze. For this reason it is recommended to use the web interface except when taking snapshots of the setup

- Computer 
   - IP Address   = `192.168.0.1 <http://192.168.0.1>`_ 
   - Setting Network adapter settings for local network:
      #. Go to :code:`Control Panel->Network and Internet->Network Connections`
      #. Right click on the network controller for the local network and select `Properties` (admin status required)
      #. Click on `TCP/IPv4` and then click `Properties`
      #. Click the radio button for `Use the following IP address` and type in the following parameters
         - IP address = 192.168.0.1
         - subnet mask = 255.255.255.0
         - Default gateway = DO NOT POPULATE
      #. Then click `OK` and `Close` to close out of the properties menu. You should now be able to access items on the local network.
- Network Switch
   - IP Address   = `192.168.0.239 <http://192.168.0.239>`_ 
   - Password is `password` 

- Optitrack Cameras
   - These IP addresses are unkown to the user

.. warning:: It is possible at some point in time The optitrack IP addresses may conflict with one of the other devices on the network. 
	If so change the IP of whatever device is conflicting to something new. This may take some trial and error.

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

1. Run the program 'Anaconda Prompt'
    - This can be done by searching for this in the Windows toolbar
2. In the prompt type `python <script_directory>/<script_name>.py` where `<script_directory>` and `<script_name>` create the path to your script

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

Both the transmit and recieve antenna should always be contained in a 3D printed mounting holder. The newest version of this holder will have 3 steel ball bearings that fit into grooves on the Robot mount. Slide the antenna and its mount into the recieving side on the robot and connect the three 3mm nuts to snugly hold together the antenna and recieving mount. DO NOT OVERTIGHTEN THESE NUTS. The connection only needs to be lightly tightened (finger tight plus 1 turn or so). Overtightening will warp the plastic and damage the mount.

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

Running the SAMURAI System
=============================

This section covers the steps required to run a SAMURAI measurement

Running from script
-------------------------

This section shows how to run from a premade python script. This requires the lowest amount of user input and is therefore the recommended method of control.

1.Create a new SAMURAI measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++

a. Make a copy of `meas_template` in the directory `U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture`
b. Rename the copy to the current date in the format `mm-dd-yyyy`
    - From here on, this newly created directory will be referred to as `<working-directory>`
c. Copy and paste the correct comma separated value (CSV) file containing the positions into `<working-directory>/synthetic_aperture/raw`
    - Some commonly used templates are contained in `<working-directory>/synthetic_aperture/raw/position_templates` directory.
    - Once the desired CSV file has been copied, rename it `positions.csv`

2. Perform 2 Port VNA Calibration
++++++++++++++++++++++++++++++++++++++++

a. In the windows file explorer navigate to `<working-directory>/cal/calibration_pre`
b. double click on 'cal.pnagrabber' to start PNAGrabber for the calibration.
c. Attach each of the standards to the calibration plane with the naming convention `<standard-port-1>_<standard-port-2>.s2p`
    - (e.g. load_short.s2p is load on port 1 and short on port 2)
d. When the calibration is completed, make a copy of each of the `.s2p` files generated and put them into the `<working-directory>/cal/calibration_pre/raw` folder

3. Open and update the script
++++++++++++++++++++++++++++++++++++++

a. Open the file `<working-directory>/synthetic_aperture/raw/run_script.py`
    - This contains the code to run the sweep along with metadata information and other input parameters
b. Set the csv file path by changing the line `position_file = './position_templates/samurai_planar_dp.csv'` to set `position_file` to the relative path to the csv file of positions
c. Set the motive dictionary for camera tracking. For all rigid bodies create a new line with the entry `motive_dict['<rigid-body-name>'] = None`. For each marker create a new line `motive_dict['<marker-name>'] = <marker-id-number>`
d. Add any experiment info and notes to `metafile_info_dict['experiment']` and `metafile_info_dict['notes']`
e. Add any additional metafile info to to the `metafile_info_dict` dictionary.

4. Run the script
+++++++++++++++++++++

Run the newly updated `run_script.py` using the directions listed in section 'Running Python Scripts'. This will save all data into the same directory as the run script.

Running from python command line interface (CLI) (DEPRECATED)
------------------------------------------------------------------

[CLI]: Command Line Interface  
[IDE]: Integrated Development Environment (e.g. Spyder)  
The following steps are to run a SAMURAI measurement from the python CLI. The steps using the python CLI here are valid for the integrated command line within the Spyder IDE. While these steps will be similar using a basic python setup, the importing of the SAMURAI classes and libraries may be a bit more complex.

1. Create a new SAMURAI measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++++

a. Make a copy of `meas_template` in the directory `U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture`
b. Rename the copy to the current date in the format `mm-dd-yyyy`
    - From here on, this newly created directory will be referred to as `<working-directory>`
c. Copy and paste the correct comma separated value (CSV) file containing the positions into `<working-directory>/synthetic_aperture/raw`
    - Some commonly used templates are contained in `<working-directory>/synthetic_aperture/raw/position_templates` directory.
    - Once the desired CSV file has been copied, rename it `positions.csv`

2. Perform 2 Port VNA Calibration
++++++++++++++++++++++++++++++++++++++++++++++++++

a. In the windows file explorer navigate to `<working-directory>/cal/calibration_pre`
b. double click on 'cal.pnagrabber' to start PNAGrabber for the calibration.
c. Attach each of the standards to the calibration plane with the naming convention `<standard-port-1>_<standard-port-2>.s2p`
    - (e.g. load_short.s2p is load on port 1 and short on port 2)
d. When the calibration is completed, make a copy of each of the `.s2p` files generated and put them into the `<working-directory>/cal/calibration_pre/raw` folder

3. Import the SAMURAI_System Module
++++++++++++++++++++++++++++++++++++++++++++++++++

a. Open the python CLI (e.g. the command window in Spyder)
b. Within the command line type the following

.. code-block:: python 

  from samurai.acquisition.SAMURAI_System import SAMURAI_System

 
.. note:: FOR NEW COMPUTERS ONLY - the code must be cloned from the gitlab repo and the directory containing the cloned `samurai` directory must be added the systems `PYTHONPATH`.

c. Create a SAMURAI_System Object
++++++++++++++++++++++++++++++++++++++++++++++++++

a. With the SAMURAI_System module imported, create a SAMURAI_System object by typing `mysam = SAMURAI_System()` into the CLI.

5. Change directory to measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++++

a. Change the directory to `<working-directory>/synthetic_aperture/raw` by running the following set of commands:

.. code-block:: python 

    import os
    os.chdir(<working-directory>/synthetic_aperture/raw)

**OR in certain iPython CLIs**

.. code-block:: python 

    cd <working-directory>/synthetic_aperture/raw


6. Mount the Antennas
++++++++++++++++++++++++++++++++++++++++++++++++++

a. Mount the Tx Antenna (usually port 2) to the fixed holder
b. Move the SAMURAI Robot to the mountain position using the commands below
    - The `mysam` object must exist for this step to work
    - Keep in mind, after this code the positioner is still connected and activated after these commands

.. code-block:: python 

    mysam.connect_rx_positioner() #connect and home the positioner
    mysam.move_to_mounting_position() #move to an easy position to mount the antenna
  

c. Use the four m3 screws to attach the Antenna to the Meca500

7. Open the Robot's Web interface (Optional)
++++++++++++++++++++++++++++++++++++++++++++++++++

Before running the sweep we can perform the extra step of viewing the robot's movement and status through its web monitoring interface.
To open up the web monitoring interface:

a. Open a web browser (tested in chrome)
b. type [10.0.0.5](http://10.0.0.5) into the address bar
c. In the web interface, click the 'Connection' button on the top toolbar.
d. In the pop-up window select 'Monitoring' and click 'Connect'

8. Run the Synthetic Aperture Sweep
++++++++++++++++++++++++++++++++++++++++++++++++++

Now we can begin the sweep

a. Ensure the working directory is set to `<working-directory>/synthetic_aperture/raw` (see step 5)
    - Some editors/IDE's (e.g. spyder) show this in a top bar of the screen
    - The current directory can be found from a python CLI by typing `import os; os.getcwd()`
b. Type the following code and hit enter to begin the sweep
    - This step assumes the robot has previously been connected and initialized (activated and homed)
    - This also assumes the `mysam` object has already been created

.. code-block::

    mysam.csv_sweep('./','./positions.csv',template_path='template.pnagrabber');disconnect_rx_positioner()


.. note:: If a csv file is being tested, the flag `run_vna=False` can be added to the `mysam.csv_sweep()` call to prevent the VNA from running
.. note:: The robot can also be put into simulation mode where all commands are sent and the web interface shows the robot moving, but the robot does not physically move. For more information on this reference the code documentation.

9. Unmount the Antennas
++++++++++++++++++++++++++++++++++++++++++++++++++

a. Create `mysam` object if it does not exist
b. Connect to positioner (refer to 'Mount the Antennas' section)

10. Collect and Save data
++++++++++++++++++++++++++++++++++++++++++++++++++

a. copy data from `<working-directory>/synthetic_aperture/raw` to `<working-directory>/synthetic_aperture/`
b. Perform post-calibration in `<working-directory>/cal/calibration_post` (refer to 'Perform 2 Port VNA Calibration' section)

Example python script
++++++++++++++++++++++++++++++
Here we have an example python script to run the sweep. This is assuming we have already created a `<working-directory>`. This also assumes we have placed a pnagrabber template named `template.pnagrabber` and a list of positions called `positions.csv` in `<working-directory>/synthetic_aperture/raw`.

.. code-block:: python 

	import os #import os for chdir
	from samurai.acquisition.SAMURAI_System import SAMURAI_System #import the samurai system class

	mysam = SAMURAI_System() #create a samurai system object
	mysam.connect_rx_positioner() #connect to the Meca500 (or other positioner)
	mysam.move_to_mounting_position() #move to the position to unmount the antenna for calibration

	###################################
	# Unmount antenna from Meca500
	###
	# PERFORM CALIBRATION HERE
	###
	# Mount antenna onto Meca500
	###################################

	mysam.zero() #return the robot to its zero position
	os.chdir('<working-directory>/syntetic_aperture/raw') #change into our measurement directory
	mysam.csv_sweep('./','./positions.csv',template_path='./template.pnagrabber') #run the csv sweep with the vna

	mysam.disconnect_rx_positioner() #disconnect from the Meca500 when finished


