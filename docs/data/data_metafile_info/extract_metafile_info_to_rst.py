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


#%% constant settings
data_root = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated'

mf_name = 'metafile.json'
image_template_path = 'external_data/pictures/setup.png' #with respect to metafile dir
local_image_dir = 'images/'

mf_dir_list_2019 = ['7-8-2019'] #this should be only be a single folder (no dir1/dir2 only dir1) for nameing ease in docs
mf_dir_list_2019 = [os.path.join('2019',mfd) for mfd in mf_dir_list_2019]

mf_dir_list  = mf_dir_list_2019
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
    meas_str = '''
Experiment Information
^^^^^^^^^^^^^^^^^^^^^^^^^

{0}

*{1}*


VNA Sweep Settings
^^^^^^^^^^^^^^^^^^^^^

{2}


'''.format(experiment,notes,vna_info_str)

    #%% add the image if available
    image_path = os.path.join(mfd,image_template_path)

    image_format_str = '''

Setup Image
^^^^^^^^^^^^^^^^^^

.. image:: {}


'''
    #copy the image from the network drive to local
    image_local_path = os.path.join(local_image_dir,data_name+'.png')
    image_path = shutil.copy(image_path,image_local_path)

    if True: #add the image on if it exists
        image_str = image_format_str.format(image_path.replace(os.sep,'/'))
        meas_str+=image_str
        
    #%% now save out
    out_file_path = os.path.join(out_dir,data_name+'.auto.rst')
    with open(out_file_path,'w+') as f:
        f.write(meas_str)
    

    
    