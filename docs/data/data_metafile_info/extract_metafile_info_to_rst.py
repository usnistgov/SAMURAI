# -*- coding: utf-8 -*-
"""
@date Wed Feb 12 08:43:02 2020

@brief Extract information on each measurement from the metafile, then put it
int a *.rst file. This should also try and get pictures from each day and add them
to the *.rst file

@author: ajw5
"""

import os

from samurai.analysis.support.MetaFileController import MetaFileController

data_root = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated'

mf_name = 'metafile.json'
pic_path = 'external_data/pictures/setup.png' #with respect to metafile dir

mf_dir_list_2019 = ['7-8-2019'] #this should be only be a single folder (no dir1/dir2 only dir1) for nameing ease in docs
mf_dir_list_2019 = [os.path.join('2019',mfd) for mfd in mf_dir_list_2019]

mf_dir_list  = mf_dir_list_2019
mf_dir_list = [os.path.join(data_root,mfd) for mfd in mf_dir_list] #add root dir

for mfd in mf_dir_list:
    mf_path = os.path.join(mfd,mf_name)
    print("Extracting info for {}".format(mf_path))
    setup_pic_path = os.path.join(mfd,pic_path)
    mfc = MetaFileController(mf_path)
    

