
.. _running-samurai:

Running from script
-------------------------

This section shows how to run from a premade python script. This requires the lowest amount of user input and is therefore the recommended method of control.

1. Create a new SAMURAI measurement directory
++++++++++++++++++++++++++++++++++++++++++++++++

#. Make a copy of :code:`meas_template` in the desired working directory.

.. note:: For measurements taken directly to the network drive use the directory :code:`C:\SAMURAI\local_data`. This will save all of the data locally to the SAMURAI computer to prevent failure due to intermittent network drive connections.

#. Rename the copy to the current date in the format :code:`mm-dd-yyyy`

    - From here on, this newly created directory will be referred to as :code:`<working-directory>`

#. Copy and paste the correct comma separated value (CSV) file containing the positions into :code:`<working-directory>/synthetic_aperture/raw`

    - Some commonly used templates are contained in :code:`<working-directory>/synthetic_aperture/raw/position_templates` directory.
    - Once the desired CSV file has been copied, rename it :code:`positions.csv`

.. note:: If the \*.csv file has never been used before:
		It is recommended to run a test sweep and watch the robot move to ensure nothing will get damaged. 
		This can be performed by adding the optional argument :code:`run_vna=False` to the mysam.csv_sweep() command in the :code:`<working_directory>/synthetic_aperture/raw/run_script.py`
		file. Although make sure to remove this command or set :code:`run_vna=True` when performing a measurement with the VNA.

.. note:: The layout for the :code:`meas_template` directory should look like:

			 - /	
				- cal/
					- calibration_post/
					- calibration_pre/
				- channel_test/
					- channel_test.py
				- external_data/
					- pictures/
					- positions/
					- temp/
				- synthetic_aperture/
					- raw/
						- position_templates/
						- run_script.py
						- set_vna_params.py 


2. Perform 2 Port VNA Calibration
++++++++++++++++++++++++++++++++++++++++

Follow the steps outlined in :ref:`Samurai Calibration Procedure`


.. _Update the Script:

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

Run the newly updated :code:`run_script.py` using the directions listed in section 'Running Python Scripts'. This will save all data into the same directory as the run script.

Measurement Scripts
-------------------------

run_script.py
+++++++++++++++++++
This is the script for running and configuring the samurai system.

.. todo:: Add more information on the settings in this script

.. module:: samurai.acquisition.script_templates.run_script
.. data::   samurai.acquisition.script_templates.run_script

.. literalinclude:: /../samurai/acquisition/script_templates/run_script.py 
	:language: python 
	:linenos:


set_vna_params.py 
+++++++++++++++++++++

This script is useful for repeatably setting many parameters of the VNA.

.. module:: samurai.acquisition.script_templates.set_vna_params
.. data::   samurai.acquisition.script_templates.set_vna_params

.. literalinclude:: /../samurai/acquisition/script_templates/set_vna_params.py 
	:language: python 
	:linenos:

channel_test.py 
+++++++++++++++++
This is a script that will take a quick sweep and generate beamformed data of a channel at 40 GHz.

.. module:: samurai.acquisition.script_templates.channel_test
.. data::   samurai.acquisition.script_templates.channel_test

.. literalinclude:: /../samurai/acquisition/script_templates/channel_test.py 
	:language: python 
	:linenos:

