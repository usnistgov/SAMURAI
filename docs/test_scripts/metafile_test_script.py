# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 09:30:46 2019
test our code about the metafile controller
@author: ajw5
"""

#%% loading the metafile
#import the controller class
from samurai.analysis.support.MetafileController import MetafileController
   
#provide a path to the metafile 
metafile_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\CUP_measurements\8-12-2019\aperture_vertical\metafile_split_0.json"

#load the metafile into an object
mymetafile = MetafileController(metafile_path)