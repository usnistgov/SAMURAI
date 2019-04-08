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

import sys
import os

from samurai.analysis.support.snpEditor import s2pEditor as s2p
from samurai.analysis.support.metaFileController import metaFileController as mfc
from samurai.analysis.support.metaFileController import update_wdir
from samurai.analysis.support.PostProcPy import PostProcPy as pppy

from collections import OrderedDict
import json
import datetime
import os
from shutil import copyfile

class CalibrateSamurai:
    
##load in our metadata file
#with open(metaPath,'r') as jsonFile:
#    jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
    def __init__(self, metaFile,out_dir,in_cal_path,post_proc_template,gthru_file_path):
        '''
        @brief initialize the class
        @param[in] metaFile - path to metafile of measurement to calibrate
        @param[in] out_dir  - output directory to place the calibrated measurements
        @param[in] in_cal_path - solution file (.s4p or .meas) file to calibrate with 
        '''
        self.mfc = mfc(metaFile)
        self.metaFile = metaFile
        
        self.post_proc_template = post_proc_template
        
        self.times = self.mfc.get_timestamp_data()
      
        self.out_dir = out_dir
        #path to our .meas error box file
        self.in_cal_path = in_cal_path
        self.switch_terms_path = gthru_file_path
        #self.dateWdir = os.path.join(self.calWdir,self.dateWdir)
        #self.calOutDir = os.path.join(self.dateWdir,'calibrated_data_'+os.path.split(self.wdir)[1])
        #self.newWdir = os.path.join(self.wdir,self.calOutDir)
  
    #calibrate in post processor and save in output directory
    def populate_post_proc_and_calibrate_s2p(self,convert_to_s2p_flg):
        #ensure our metafile is updated to the current folder
        self.mfc.set_wdir()
        #get our list of values from the old folder both with and without absolute path
        fnames_abs = self.mfc.get_filename_list(True)
        #open our post proc object and rename to our new directory
        self.ppc = pppy(self.post_proc_template)
        out_name = os.path.split(self.post_proc_template)[1] #get the file name
        #now rename
        self.ppc.rename(os.path.join(self.out_dir,out_name))
        #now set cal path
        self.ppc.setCalPath(self.in_cal_path)
        self.ppc.setSwitchTerms(self.switch_terms_path)
        #and populate the duts
        self.ppc.setDUTFromList(fnames_abs)
        #now check our checkboxes to see what we want to do
        #self.ppc.convert_to_s2p(convert_to_s2p_flg);
        #then write and run
        print("Running Calibration in "+str(self.out_dir))
        self.ppc.write()
        self.ppc.run()
        print("Calibration Complete. Updating MetaFile and Moving Data...")
        #update metafile and move data
        self.update_metafile_and_move()

    #def populate_post_proc_and_calibrate_wnp(self,convert_to_s2p_flg):
        
        
        
    def update_metafile_and_move(self,convert_to_s2p_flg=0,wave_params_flg=0):
        
        self.move_calibrated_results()
        self.mfc.set_calibration_file(self.in_cal_path)
        #now rewrite a new metafile in new folder
        self.mfc.set_wdir(self.out_dir)
        self.mfc.write()

    #This will copy each of the calibrated measurements
    def move_calibrated_results(self,convert_to_s2p_flg=0,wave_params_flg=0):

        #we now assume given path already exists. This is easier to use
        #get our file names. These names will be the same in the calibration folder
        fnames = self.mfc.get_filename_list()
        #our calibration folder name
        cal_folder_name = os.path.split(self.post_proc_template)[1].split('.')[0]
        cal_folder_full = os.path.join(self.out_dir,cal_folder_name+'_post_Results') #full path to our calibration folder
        #we now we go into the subdirectories and copy the s2p file which is named based on the post processor template
       # if(wave_params_flg):
       #     ftype = '.w2p';
       # else:
       #     ftype = 's2p';
       # if(convert_to_s2p_flg): #if we converted we need to change to s2p and overwrite whatever was there
       #     ftype = '.s2p' 
        
        #snp_name = cal_folder_name+'_0'+ftype;
        fname_out_list = []
        #now lets copy
        for fname in fnames:
            meas_name_full = os.path.split(fname)[-1] #in case the measurements are in some subdirectory
            meas_name = meas_name_full.split('.')[0] #we remove extension here
            meas_ext  = meas_name_full.split('.')[1]
            snp_name =  cal_folder_name+'_0.'+meas_ext
            copy_src = os.path.join(cal_folder_full,meas_name,snp_name)
            meas = meas_name+'.'+meas_ext
            copy_dst = os.path.join(self.out_dir,meas)#now set our copy destination
            #now we actually copy
            copyfile(copy_src,copy_dst)
            #make list of output file names
            fname_out_list.append(meas)
        #now update the metafile entry
        #this assumes that all of the files have been read and written in order
        self.mfc.set_filename(fname_out_list) #set list to metafile
       


