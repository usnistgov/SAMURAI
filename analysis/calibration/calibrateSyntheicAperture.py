# -*- coding: utf-8 -*-
"""
Created on Mon May 14 08:34:24 2018

This script edits our metafile and moves our data and new copy of metafile to outDir
This assumes our data has been calibrated with the MUF and DUTs are within that output directory form the MUF

Before running 
 - calibrate all data with muf
 - Ensure calibrated data folder is in same folder as measurements

@author: ajw5
"""

from collections import OrderedDict
import json
import datetime
import os
from shutil import copyfile
try: #try 2.7
    import Tkinter as tk
except ImportError:
    import tkinter as tk
try:
    import tkFileDialog
except ImportError:
    import tkinter.filedialog as tkFileDialog

#metaPath = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/5-18-2018_LOS/processed/meas/syntheticAperture/metaFile.json';
#calDir = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/5-18-2018_LOS/processed/meas/syntheticAperture/preCal_vnauncert_Results/';
#outDir = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/5-18-2018_LOS/processed/meas/syntheticAperture/calibratedData/';

#wdir = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/5-18-2018_LOS/processed/meas/syntheticAperture_Elevation/'
#wdir = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements//processed/meas/syntheticAperture_Elevation/'

#have user select metafile
root = tk.Tk();
root.withdraw();
metaPath = tkFileDialog.askopenfilename(initialdir='../../',title='Select Metadata File',filetypes=(('Synthetic Aperture MetaFile','*.json'),));
#assume directory of metaFile is working dir
[wdir, metafile] = os.path.split(metaPath)

#calibration relative to metafile
calDir   = os.path.join(wdir,'./preCal_vnauncert_Results/')

##load in our metadata file
with open(metaPath,'r') as jsonFile:
    jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
    
##get the date
timestamp = jsonData['measurements'][1]['timestamp']
dmy = timestamp.split()[0].split('-')
dateWdir = dmy[1]+'-'+dmy[2]+'-'+dmy[0]
    
#new working directory of our calibrated data
calWdir = '../../../../calibrated' #THIS IS WHERE THE CALIBRATION WILL BE PLACED!!!
dateWdir = os.path.join(calWdir,dateWdir)
calOutDir = os.path.join(dateWdir,'calibrated_data_'+os.path.split(wdir)[1])
newWdir = os.path.join(wdir,calOutDir)
    
    
#make directory
if not os.path.exists(dateWdir):
    os.makedirs(dateWdir);

#make directory
if not os.path.exists(newWdir):
    os.makedirs(newWdir);
    #move calibrated results




#set our new working directory
jsonData['working_directory'] = os.path.abspath(newWdir);

#load our measurements from the metadata
measurements = jsonData['measurements'];
    
#for each measurement
for meas in measurements:
    
   #copy file to outDir, update metadata
   #get our measurement filename
   curPath = meas['filename']
   curPath.replace('raw','processed'); #change to processed directory JUST IN CASE Shouldnt be needed anymore
   #fname = curPath.split('//')[-1]
   #fname = fname.split('/')[-1]
   curPath = curPath.strip();
   [_,fname] = os.path.split(curPath);
   #fname = fname.strip();
   fnameNoEnd = fname.split('.')[0]
   
   #our output path for our copied measurement
   fpathOut = newWdir+'/'+fname
   
   #copy to our output directory
   calibratedPath = os.path.abspath(calDir+'./DUTs/'+fnameNoEnd+'_Support/'+fnameNoEnd+'_0.s2p')
   copyfile(calibratedPath,fpathOut)
   
   meas['calibration_file'] = os.path.relpath(os.path.abspath(calDir+'./Solutions/Solution_0.s4p'),newWdir);
   
   #now name our files correctly
   meas['filename'] = os.path.relpath(fpathOut,newWdir);
   meas.update({'calibrated':True})

#write updated measurement stuff to json data
jsonData['measurements']=measurements
#write back out our metadata file into outdir
outMetaPath = newWdir+'./metaFile.json';
with open(outMetaPath,'w+') as jsonFile:
    json.dump(jsonData,jsonFile,indent=4);     


