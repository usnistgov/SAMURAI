
Running the SAMURAI System
=============================

This section covers the steps required to run a SAMURAI measurement

Running from script
-------------------------

This section shows how to run from a premade python script. This requires the lowest amount of user input and is therefore the recommended method of control.

1. Create a new SAMURAI measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++

#. Make a copy of :code:`meas_template` in the directory :code:`U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture`
#. Rename the copy to the current date in the format :code:`mm-dd-yyyy`
    - From here on, this newly created directory will be referred to as :code:`<working-directory>`
#. Copy and paste the correct comma separated value (CSV) file containing the positions into :code:`<working-directory>/synthetic_aperture/raw`
    - Some commonly used templates are contained in :code:`<working-directory>/synthetic_aperture/raw/position_templates` directory.
    - Once the desired CSV file has been copied, rename it :code:`positions.csv`


2. Perform 2 Port VNA Calibration
++++++++++++++++++++++++++++++++++++++++

#. In the windows file explorer navigate to :code:`<working-directory>/cal/calibration_pre`
#. double click on :code:'cal.pnagrabber' to start PNAGrabber for the calibration.
#. Attach each of the standards to the calibration plane with the naming convention :code:`<standard-port-1>_<standard-port-2>.s2p`
    - (e.g. load_short.s2p is load on port 1 and short on port 2)
#. When the calibration is completed, make a copy of each of the `.s2p` files generated and put them into the :code:`<working-directory>/cal/calibration_pre/raw` folder

3. Open and update the script
++++++++++++++++++++++++++++++++++++++

#. Open the file :code:`<working-directory>/synthetic_aperture/raw/run_script.py`
    - This contains the code to run the sweep along with metadata information and other input parameters
#. Set the csv file path by changing the line :code:`position_file = './position_templates/samurai_planar_dp.csv'` to set `position_file` to the relative path to the csv file of positions
#. Set the motive dictionary for camera tracking. For all rigid bodies create a new line with the entry :code:`motive_dict['<rigid-body-name>'] = None`. For each marker create a new line :code:`motive_dict['<marker-name>'] = <marker-id-number>`
#. Add any experiment info and notes to :code:`metafile_info_dict['experiment']` and :code:`metafile_info_dict['notes']`
#. Add any additional metafile info to to the :code:`metafile_info_dict` dictionary.

4. Run the script
+++++++++++++++++++++

Run the newly updated `run_script.py` using the directions listed in section 'Running Python Scripts'. This will save all data into the same directory as the run script.

Measurement Scripts
-------------------------

run_script.py
+++++++++++++++++++
This is the script for running and configuring the samurai system.

.. code-block:: python 

	"""
	Created on Fri May 17 14:08:56 2019
	@author: ajw5
	"""

	from samurai.acquisition.SAMURAI_System import SAMURAI_System
	from collections import OrderedDict

	## configuration for motive
	motive_dict = {}
	motive_dict['meca_head'] = None
	motive_dict['origin']    = None
	motive_dict['tx_antenna'] = None
	#labeled markers
	motive_dict['vna_marker'] = 50716

	position_file = './position_templates/samurai_planar_dp.csv'
	output_dir = './'

	#info to put into metafile
	metafile_info_dict = {}
	metafile_info_dict["experiment"] = None
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
	#metafile_info_dict["scatterers"] = "Active scatterers (sources) see \"antennas\" data" #[cyl_1,cyl_2]
	metafile_info_dict["notes"] = None


	mysam = SAMURAI_System()
	mysam.connect_rx_positioner()
	mysam.csv_sweep(output_dir,position_file,external_position_measurements=motive_dict,metafile_header_values=metafile_info_dict)
	mysam.disconnect_rx_positioner()

set_vna_params.py 
+++++++++++++++++++++

This script is useful for repeatably setting many parameters of the VNA.

.. code-block:: python 

	"""
	Created on Fri Aug  2 09:11:34 2019
	@author: ajw5
	"""

	from samurai.acquisition.instrument_control.PnaController import PnaController

	if_bw = 100
	sweep_delay = 0.0005
	dwell_time = 0.001
	start_freq = 26.5e9
	stop_freq = 40e9
	num_pts = 1351
	pow_dbm = 0

	visa_addr = 'TCPIP0::192.168.0.2::inst0::INSTR'

	mypna = PnaController(visa_addr)

	mypna.setup_s_param_measurement([11,31,13,33]) #with comb on use port 3
	mypna.set_continuous_trigger('ON')

	mypna.write('if_bandwidth',if_bw)
	mypna.write('sweep_delay_time',sweep_delay)
	mypna.write('dwell_time',dwell_time)
	mypna.write('power',pow_dbm)
	mypna.set_freq_sweep(start_freq,stop_freq,num_pts= num_pts)

channel_test.py 
+++++++++++++++++
This is a script that will take a quick sweep and generate beamformed data of a channel at 40 GHz.

.. code-block:: python 

	"""
	Created on Tue Jul 30 11:32:39 2019
	Script to test the approximate response of the channel
	This will give a PDP at a single point, and a beamformed set at a signle frequency
	@author: ajw5
	"""
	###############################################################################
	gather_flg = True #whether or not to gather the data
	process_flg = True #whether or not to process the data
	aoa_flg = True #do we do aoa measurements
	pdp_flg = True #do we do pdp measurements
	###############################################################################

	##############################################################################
	#first lets gather the data
	if gather_flg:
		from samurai.acquisition.SAMURAI_System import SAMURAI_System
		from samurai.acquisition.instrument_control.PnaController import PnaController

		mysam = SAMURAI_System()
		mysam.connect_rx_positioner()
		
		pna_visa_addr ='TCPIP0::192.168.0.2::inst0::INSTR'
		mypna = PnaController(pna_visa_addr)
		
		if aoa_flg:
			#start with the synthetic aperture at a single frequency
			position_file = '../synthetic_aperture/raw/position_templates/samurai_planar_vp.csv'
			#position_file = '../synthetic_aperture/raw/position_templates/samurai_planar_vp_short.csv'
			#position_file = '../synthetic_aperture/raw/position_templates/samurai_planar_hp.csv'
			output_dir = './'
			meas_freq = 40e9;
			
			#info to put into metafile
			metafile_info_dict = {}
			metafile_info_dict["experiment"] = 'preliminary channel testing measurements'
			metafile_info_dict["notes"] = None
			
			#setup the vna for single frequency sweep
			mypna.setup_s_param_measurement([31])
			mypna.set_freq_sweep(meas_freq,meas_freq,num_pts=1)
			mypna.write('if_bandwidth',100)
			mypna.write('power',0)
			mypna.set_continuous_trigger('OFF')
		
			#now run the system
			mysam.csv_sweep(output_dir,position_file,metafile_header_values=metafile_info_dict,external_meas_obj=PnaController,external_meas_obj_init_args=(pna_visa_addr,),external_meas_obj_meas_args=({3:2},))
			
		if pdp_flg:
			mysam.set_position([0,80,60,0,0,0])
			mypna.setup_s_param_measurement([31])
			mypna.set_freq_sweep(26.5e9,40e9,num_pts=1351)
			mypna.write('if_bandwidth',100)
			mypna.measure_s_params('meas_all_freqs.s2p',{3:2})
			
		mysam.disconnect_rx_positioner()

	#now lets process it
	if process_flg:
		from samurai.base.SamuraiPlotter import SamuraiPlotter
		import numpy as np
		
		sp = SamuraiPlotter('matplotlib')

		if aoa_flg:
			from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform
			metafile_path = './metafile.json'
		
			mysp = SamuraiBeamform(metafile_path,verbose=True) 
			mysp.set_cosine_sum_window_by_name('hamming')
			mycsa,_ = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),[40e9],verbose=True) #beamform
			fig = mycsa.plot_3d()
			fig.layout['scene']['aspectmode']='cube'
			fig.show(renderer='browser')
			
		if pdp_flg:
			from samurai.base.TouchstoneEditor import SnpEditor
			file_path = './meas_all_freqs.s2p'
			snp = SnpEditor(file_path)
			times,td_data = snp.S[21].calculate_time_domain_data()
			sp.plot(times,20.*np.log10(np.abs(td_data)))


Running from python command line interface (CLI) (DEPRECATED)
------------------------------------------------------------------

.. warning:: This method of measurement is deprecated and may contain innacuracies. It is currently kept for reference but may be removed in future iterations.

- [CLI]: Command Line Interface  
- [IDE]: Integrated Development Environment (e.g. Spyder)  

The following steps are to run a SAMURAI measurement from the python CLI. The steps using the python CLI here are valid for the integrated command line within the Spyder IDE. While these steps will be similar using a basic python setup, the importing of the SAMURAI classes and libraries may be a bit more complex.

1. Create a new SAMURAI measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++++

#. Make a copy of `meas_template` in the directory `U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture`
#. Rename the copy to the current date in the format `mm-dd-yyyy`
    - From here on, this newly created directory will be referred to as `<working-directory>`
#. Copy and paste the correct comma separated value (CSV) file containing the positions into `<working-directory>/synthetic_aperture/raw`
    - Some commonly used templates are contained in `<working-directory>/synthetic_aperture/raw/position_templates` directory.
    - Once the desired CSV file has been copied, rename it `positions.csv`

2. Perform 2 Port VNA Calibration
++++++++++++++++++++++++++++++++++++++++++++++++++

#. In the windows file explorer navigate to `<working-directory>/cal/calibration_pre`
#. double click on 'cal.pnagrabber' to start PNAGrabber for the calibration.
#. Attach each of the standards to the calibration plane with the naming convention `<standard-port-1>_<standard-port-2>.s2p`
    - (e.g. load_short.s2p is load on port 1 and short on port 2)
#. When the calibration is completed, make a copy of each of the `.s2p` files generated and put them into the `<working-directory>/cal/calibration_pre/raw` folder

3. Import the SAMURAI_System Module
++++++++++++++++++++++++++++++++++++++++++++++++++

#. Open the python CLI (e.g. the command window in Spyder)
#. Within the command line type the following

.. code-block:: python 

  from samurai.acquisition.SAMURAI_System import SAMURAI_System

 
.. note:: FOR NEW COMPUTERS ONLY - the code must be cloned from the gitlab repo and the directory containing the cloned `samurai` directory must be added the systems `PYTHONPATH`.

c. Create a SAMURAI_System Object
++++++++++++++++++++++++++++++++++++++++++++++++++

#. With the SAMURAI_System module imported, create a SAMURAI_System object by typing `mysam = SAMURAI_System()` into the CLI.

5. Change directory to measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++++

#. Change the directory to `<working-directory>/synthetic_aperture/raw` by running the following set of commands:

.. code-block:: python 

    import os
    os.chdir(<working-directory>/synthetic_aperture/raw)

*OR in certain iPython CLIs*

.. code-block:: python 

    cd <working-directory>/synthetic_aperture/raw


6. Mount the Antennas
++++++++++++++++++++++++++++++++++++++++++++++++++

#. Mount the Tx Antenna (usually port 2) to the fixed holder
#. Move the SAMURAI Robot to the mountain position using the commands below
    - The `mysam` object must exist for this step to work
    - Keep in mind, after this code the positioner is still connected and activated after these commands

.. code-block:: python 

    mysam.connect_rx_positioner() #connect and home the positioner
    mysam.move_to_mounting_position() #move to an easy position to mount the antenna
  

#. Use the four m3 screws to attach the Antenna to the Meca500

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

#. Ensure the working directory is set to `<working-directory>/synthetic_aperture/raw` (see step 5)
    - Some editors/IDE's (e.g. spyder) show this in a top bar of the screen
    - The current directory can be found from a python CLI by typing `import os; os.getcwd()`
#. Type the following code and hit enter to begin the sweep
    - This step assumes the robot has previously been connected and initialized (activated and homed)
    - This also assumes the `mysam` object has already been created

.. code-block::

    mysam.csv_sweep('./','./positions.csv',template_path='template.pnagrabber');disconnect_rx_positioner()


.. note:: If a csv file is being tested, the flag `run_vna=False` can be added to the `mysam.csv_sweep()` call to prevent the VNA from running
.. note:: The robot can also be put into simulation mode where all commands are sent and the web interface shows the robot moving, but the robot does not physically move. For more information on this reference the code documentation.

9. Unmount the Antennas
++++++++++++++++++++++++++++++++++++++++++++++++++

#. Create `mysam` object if it does not exist
#. Connect to positioner (refer to 'Mount the Antennas' section)

10. Collect and Save data
++++++++++++++++++++++++++++++++++++++++++++++++++

#. copy data from `<working-directory>/synthetic_aperture/raw` to `<working-directory>/synthetic_aperture/`
#. Perform post-calibration in `<working-directory>/cal/calibration_post` (refer to 'Perform 2 Port VNA Calibration' section)

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

