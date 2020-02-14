# -*- coding: utf-8 -*-
"""
@date Wed Feb 12 08:43:02 2020

@brief Extract information on each measurement from the metafile, then put it
int a *.rst file. This should also try and get pictures from each day and add them
to the *.rst file

@author: ajw5
"""

import os
import shutil

from samurai.analysis.support.MetaFileController import MetaFileController


#%% Strings for different parts of the rst file

#format with (experiment,notes,vna_info)
meas_str = '''
Experiment Information
^^^^^^^^^^^^^^^^^^^^^^^^^

{0}

*{1}*


VNA Sweep Settings
^^^^^^^^^^^^^^^^^^^^^

{2}


'''

#format with (image_location)
image_format_str = '''

Setup Image
^^^^^^^^^^^^^^^^^^

.. image:: {}


'''

#format with (data_dir_name)
extra_info_link_str = '''

Extra Information
^^^^^^^^^^^^^^^^^^^^

Extra plots and information on the measurement and its data can be found at the link below.

- :ref:`data_{}_extra_info`

'''

#format with (data_dir_name)
extra_info_page_str = '''

.. _data_{}_extra_info:

#############################################################
Additional Information for :code:`{}`
#############################################################

Aperture Positions
---------------------------

.. image:: {}


Beamformed 3D Data Plot at highest frequency
----------------------------------------------------

.. image:: {}

'''

#format with ('\n   data_extra_1\n   data_extra_2'...)
extra_info_toctree_str = '''
    
.. toctree::
    :hidden:
{}

'''

#%% constant settings
data_root = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated'

mf_name = 'metafile.json'
image_template_path = 'external_data/pictures/setup.png' #with respect to metafile dir
local_image_dir = 'images/'

mf_dir_list = []

#%% 2019 Data
#this should be only be a single folder (no dir1/dir2 only dir1) for nameing ease in docs. copy split sweep full metafile into root
#optical table
mf_dir_list_2019  = []
#mf_dir_list_2019 += ['1-3-2019','2-1-2019','2-4-2019','2-6-2019','2-7-2019','2-13-2019']
#mf_dir_list_2019 += ['2-14-2019','2-20-2019','3-1-2019','3-4-2019','3-20-2019']
#mf_dir_list_2019 += ['6-17-2019','6-19-2019','7-8-2019','7-8-2019_cable_test']
# Conference Room
#mf_dir_list_2019+= ['5-17-2019','5-24-2019','5-31-2019']
# CUP Data
#mf_dir_list_2019+= ['8-7-2019','8-8-2019','8-9-2019','8-12-2019','8-13-2019','8-16-2019']
mf_dir_list_2019 += ['7-8-2019']

mf_dir_list_2019 = [os.path.join('2019',mfd) for mfd in mf_dir_list_2019]

#COMMENT THIS LINE BELOW OUT TO NOT GENERATE 2019 THINGS
mf_dir_list  += mf_dir_list_2019

#%% 2020 Data

mf_dir_list = [os.path.join(data_root,mfd) for mfd in mf_dir_list] #add root dir

out_dir = './' #output directory of files

#%% now loop through each file
for mfd in mf_dir_list:
    mf_path = os.path.join(mfd,mf_name)
    print("Extracting info for {}".format(mf_path))
    mfc = MetaFileController(mf_path)
    
    #%% lets get the information on the measurement
    experiment = mfc['experiment']
    notes = mfc['notes']
    vna_info_str = mfc['vna_info'].get_rst_str()
    
    data_name = os.path.split(mfd)[1]
    
    #and add it to the rst file
    rst_str = meas_str.format(experiment,notes,vna_info_str)

    #%% add the image if available
    image_path = os.path.join(mfd,image_template_path)

    
    #copy the image from the network drive to local
    image_local_path = os.path.join(local_image_dir,data_name+'.png')
    image_path = shutil.copy(image_path,image_local_path)
    #the image path in the rst file must be relative to sphinx root because we
    #are using the include directive on this auto generated file.
    rst_image_path = os.path.join('/data/data_metafile_info/',image_path)

    if True: #add the image on if it exists
        image_str = image_format_str.format(rst_image_path.replace(os.sep,'/'))
        rst_str+=image_str


    #%% extra information with plots and whatnot
    

        
    #%% Now lets create and add a plot of the aperture
    ap_fig = mfc.plot_aperture()
    
        
        
    #%% now save out
    out_file_path = os.path.join(out_dir,data_name+'.auto.rst')
    with open(out_file_path,'w+') as f:
        f.write(rst_str)
    

    
    