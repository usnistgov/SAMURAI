

.. warning:: This method of measurement is deprecated and may contain innacuracies. It is currently kept for reference and some useful example sections, but may be removed in future iterations.

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

 
.. note:: FOR NEW COMPUTERS ONLY - the code must be cloned from the :git_repo:`/` and the directory containing the cloned `samurai` directory must be added the systems `PYTHONPATH`.

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

.. code-block:: python

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

