
#%% Basic experiment information for main page

#format with (**metafile_kwargs)
meas_str = '''
Experiment Information
^^^^^^^^^^^^^^^^^^^^^^^^^

{experiment}

*{notes}*


VNA Sweep Settings
^^^^^^^^^^^^^^^^^^^^^

{vna_info}


'''

#%% Image for main page (setup.png)

#format with (image_location)
image_format_str = '''

Setup Image
^^^^^^^^^^^^^^^^^^

.. image:: {0}


'''

#%% String for extra info from metafiles

#format with ('- :ref:`<data_dir_name_1>\n- :ref:`<data_dir_name_2>,...)
extra_info_link_str = '''

Extra Information
^^^^^^^^^^^^^^^^^^^^

Extra plots and information on each of the specific sweeps take during the measurement and their data can be found at the link below.

{0}

'''


#%% This is the template for the extra page with information on each of the metafiles

#format with (data_dir_name,enumerated value,**plot_path_dict,**metafile_kwargs)
extra_info_page_str = ('''
                       
:orphan:

.. _data_{0}_extra_info_{1}:

#####################################################################################
Additional Information for :code:`{name}`
#####################################################################################

Experiment Information
----------------------------

{experiment}

*{notes}*


VNA Sweep Settings
--------------------------

{vna_info}

----

Aperture Positions (mm)
---------------------------

.. raw:: html
   :file: {aperture}
   
:download:`Download Data<{aperture_data}>`

----

Measurement at first position
----------------------------------

.. raw:: html
    :file: {fd_meas}
    
:download:`Download Data<{fd_meas_data}>`
    
----

Time Domain Result
-----------------------------

.. raw:: html
    :file: {td_meas}
    
:download:`Download Data<{td_meas_data}>`
    
----

Azimuth cut at 0 Degrees Elevation
--------------------------------------

.. raw:: html
    :file: {az_cut}
    
:download:`Download Data<{az_cut_data}>`

----

Beamformed 3D Data Plot at highest frequency
----------------------------------------------------

.. raw:: html
    :file: {bf_3d}
    
:download:`Download Data<{bf_3d_data}>`

----

Externally Measured Positions
---------------------------------------------

{ext_pos_str}
    
    
----
    
Plotting the data from the plots above
-------------------------------------------

Each of the above plots has a link to download a JSON file containing all of the plot data and formatting.
The data can be Plotted (for 2D plots) with the following commands. Each of these instructions 
are also contained in the 'how_to' section of each of the JSON files.

Python (using Plot.ly)
++++++++++++++++++++++++++++

.. code-block:: python

    # Import libraries and data
    import plotly.graph_objs as go
    from samurai.base.SamuraiDict import SamuraiDict
    fig_dict = SamuraiDict()
    fig_dict.load('path/to/data/file.json')
    
    # Getting the x,y data from the first trace
    x_data = fig_dict['data'][0]['x']
    y_data = fig_dict['data'][0]['y']
    #z_data = fig_dict['data'][0]['y'] #if its a 3d plot
    
    # Plot the data from the JSON file with plotly
    # This works for all types of plots 
    fig = go.Figure(fig_dict)
    fig.show()
    
    
MATLAB
+++++++++++++++++++++

.. code-block:: matlab

    % load and parse the json file
    fid = fopen('path/to/data/file.json');
    raw = fread(fid,inf);
    str = char(raw');
    fclose(fid);
    fig_struct = jsondecode(str);
    
    % import the x,y data (and z if its available) from the first trace
    x_data = fig_struct.data(1).x;
    y_data = fig_struct.data(1).y;
    #z_data = fig_struct.data(1).z; %if its a 3D plot
    
    % Plot the data (for 2D plots)
    fig = plot(x_data,y_data);

''')

# format with (ext_pos='path/to/plot.html',ext_pos_data='path/to/data.json')
ext_pos_str = ('''
.. raw:: html
    :file: {ext_pos}

:download:`Download Data<{ext_pos_data}>`

''')


#%% How to string for plot data

#how to parameter for figure json data
fig_how_to = {
'python':'''
# Import libraries and data
import plotly.graph_objs as go
from samurai.base.SamuraiDict import SamuraiDict
fig_dict = SamuraiDict()
fig_dict.load('path/to/data/file.json')

# Getting the x,y data from the first trace
x_data = fig_dict['data'][0]['x']
y_data = fig_dict['data'][0]['y']
#z_data = fig_dict['data'][0]['y'] #if its a 3d plot

# Plot the data from the JSON file with plotly
# This works for all types of plots 
fig = go.Figure(fig_dict)
fig.show()
''',
'matlab':'''
% load and parse the json file
fid = fopen('path/to/data/file.json');
raw = fread(fid,inf);
str = char(raw');
fclose(fid);
fig_struct = jsondecode(str);

% import the x,y data (and z if its available) from the first trace
x_data = fig_struct.data(1).x;
y_data = fig_struct.data(1).y;
#z_data = fig_struct.data(1).z; %if its a 3D plot

% Plot the data (for 2D plots)
fig = plot(x_data,y_data);
'''
}





