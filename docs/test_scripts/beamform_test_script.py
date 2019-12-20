# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 10:37:12 2019

@author: ajw5
"""

#%% run beamforming with our beamform class
#import numpy
import numpy as np

#import the beamforming class
from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform

#provide a path to the metafile 
metafile_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\CUP_measurements\8-12-2019\aperture_vertical\metafile_split_0.json"

#create our beamforming class
my_samurai_beamform = SamuraiBeamform(metafile_path,verbose=True)

#add a hamming window to reduce sidelobes
my_samurai_beamform.set_cosine_sum_window_by_name('hamming')

#perform beamforming
calc_synthetic_aperture = my_samurai_beamform.beamforming_farfield_azel(
                                np.arange(-90,90,1),np.arange(-90,90,1),freq_list=[40e9])

#plot our data in 3D
myplot = calc_synthetic_aperture.plot_3d()

'''
#%% load the data
#import the controller class
from samurai.analysis.support.MetaFileController import MetaFileController
   
#provide a path to the metafile 
metafile_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\CUP_measurements\8-12-2019\aperture_vertical\metafile_split_0.json"

#load the metafile into an object
mymetafile = MetaFileController(metafile_path)

#load the S parameter data from the metafile 
data = mymetafile.load_data(verbose=True)

#extract S21 to block of data
block_data = np.array([d.S[21] for d in data])
'''