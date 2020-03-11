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

#import sys
import os

#from samurai.analysis.support.snpEditor import s2pEditor as s2p
from samurai.analysis.support.MetaFileController import MetaFileController as mfc
from samurai.analysis.support.MetaFileController import set_metafile_meas_relative
#from samurai.analysis.support.metaFileController import update_wdir
from samurai.analysis.support.MUF.PostProcPy import PostProcPy as pppy
from samurai.base.generic import deprecated
from samurai.analysis.support.MetaFileController import copy_touchstone_from_muf

#from collections import OrderedDict
#import json
#import datetime
#import os
from shutil import copy

#default paths
default_pp_cal_template     = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates/cal_template.post')
default_pp_cal_template_wnp = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates/cal_template_wave_param.post')
#this default is for s2p_files not w2p calibration (theyre different)

class CalibrateSamurai:
    
##load in our metadata file
#with open(metaPath,'r') as jsonFile:
#    jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
    def __init__(self, metaFile,out_dir,in_cal_path,gthru_file_path='',post_proc_template_override=None,**kwargs):
        '''
        @brief initialize the class
        @param[in] metaFile - path to metafile of measurement to calibrate
        @param[in] out_dir  - output directory to place the calibrated measurements
        @param[in] in_cal_path - solution file (.s4p or .meas) file to calibrate with 
        @param[in/OPT] kwargs - keyword arguments for the class options. these are also forwarded to PostProcPy
        '''
        #options dictionaruy
        self.options = {}
        for k,v in kwargs.items():
            self.options[k] = v #set input options

        self.mfc = mfc(metaFile)
        self.metaFile = metaFile
        
        #get the type of file (snp or wnp)
        first_meas_name = self.mfc.get_filename(0) 
        meas_ext = os.path.splitext(first_meas_name)[-1] #get our measurement extension
        #at this point we will have .s#p,.s#p_binary, .w#p, or .w#p_binary
        if(meas_ext[1]=='w'):
            self.options['wave_params_flg'] = True
            self.post_proc_template = default_pp_cal_template_wnp
        elif(meas_ext[1]=='s'):
            self.options['wave_params_flg'] = False
            self.post_proc_template = default_pp_cal_template
        else:
            raise IOError("bad extension please check the file extensions start with .s or .w") #<@todo replace with real exception
        if post_proc_template_override:
            self.post_proc_template = post_proc_template_override
        
        
        self.times = self.mfc.timestamps
      
        self.out_dir = out_dir
        #path to our .meas error box file
        self.in_cal_path = in_cal_path
        self.switch_terms_path = gthru_file_path #only used for s parameters
  
    #calibrate in post processor and save in output directory
    def populate_post_proc_and_calibrate(self):
        #ensure our metafile is updated to the current folder it is in
        self.mfc.wdir = os.path.dirname(self.metaFile)
        #get our list of values from the old folder both with and without absolute path
        fnames_abs = self.mfc.get_filename_list(True)
        #open our post proc object and rename to our new directory
        print(self.post_proc_template)
        self.ppc = pppy(self.post_proc_template,**self.options)
        out_name = os.path.split(self.post_proc_template)[1] #get the file name
        #now rename
        self.ppc.rename(os.path.join(self.out_dir,out_name))
        #now set cal path
        self.ppc.setCalPath(self.in_cal_path)
        if not (self.options['wave_params_flg']): #only set switch terms for wave params
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
        mf_out_path = self.update_metafile_and_move() 
        set_metafile_meas_relative(mf_out_path)
        return mf_out_path
        
    def update_metafile_and_move(self):
        
        print("Moving calibrated results")
        new_mf_path = self.move_calibrated_results() #this now also updates and writes the metafile
        print("Metafile at {}".format(new_mf_path))
        print("Copying results to touchstone")
        self.move_calibrated_nominal_results_touchstone(new_mf_path)
        #self.mfc.set_calibration_file(self.in_cal_path)
        #now rewrite a new metafile in new folder
        #self.mfc.set_wdir(self.out_dir)
        #self.mfc.write()
        return new_mf_path

    def _update_metafile(self,filename_list,subdir):
        '''
        @brief update our metafile for use with *.meas MUF outputs
        @param[in] filename_list - list of filenames to update to
        @param[in] subdir - subdirectory passed from self.move_calibrated_results
        @return path to written metafile
        '''
        mf_out_path = os.path.join(self.out_dir,subdir,'metafile.json')
        self.mfc.set_calibration_file(self.in_cal_path)
        self.mfc.wdir = './'
        self.mfc.set_filename(filename_list) #set list to metafile
        return self.mfc.write(mf_out_path) #write out
    
    def move_calibrated_results(self,subdir='.'):
        '''
        @brief move our calibrated *.meas files
        @param[in/OPT] subdir - subdirectory to put them in (default to no subdir)
        '''
        fnames = self.mfc.filenames #get the original file names
        #our calibration folder name
        cal_menu_name = os.path.splitext(os.path.split(self.post_proc_template)[-1])[0] #get the name of our file (this is added to output names of *.meas files)
        cal_folder_path = os.path.join(self.out_dir,cal_menu_name+'_post_Results') #full path to our calibration folder
        
        #make the subdir if it doesnt exist
        if not os.path.exists(os.path.join(self.out_dir,subdir)):
            os.mkdir(os.path.join(self.out_dir,subdir))

        fname_out_list = []            
        #now loop through each name to copy the files
        for fname in fnames:
            meas_name = os.path.split(fname)[-1] #in case the measurements are in some subdirectory
            meas_name,meas_ext = os.path.splitext(meas_name)
            #we will always have *.meas here
            meas_name += '_'+cal_menu_name+'.meas'
            copy_src = os.path.join(cal_folder_path,meas_name)
            copy_dst = os.path.join(self.out_dir,subdir)#now set our copy destination
            #now we actually copy
            meas_out_name = copy(copy_src,copy_dst)
            #make list of output file names
            fname_out_list.append(os.path.split(meas_out_name)[-1])
        #now update the metafile entry
        #this assumes that all of the files have been read and written in order
        return self._update_metafile(fname_out_list,subdir)
    
    def move_calibrated_nominal_results_touchstone(self,metafile_path):
        '''
        @brief move our calibrated snp or wnp files to a provided subdirectory
            This will pull the nominal results from the *.meas files in the newly updated metafile
        '''
        copy_touchstone_from_muf(metafile_path)
        '''
        #we now assume given path already exists. This is easier to use
        #get our file names. These names will be the same in the calibration folder
        fnames = self.mfc.get_filename_list()
        #our calibration folder name
        cal_folder_name = os.path.split(self.post_proc_template)[1].split('.')[0]
        cal_folder_full = os.path.join(self.out_dir,cal_folder_name+'_post_Results') #full path to our calibration folder
        
        fname_out_list = []
        #now lets copy
        if not os.path.exists(os.path.join(self.out_dir,subdir)):
            os.mkdir(os.path.join(self.out_dir,subdir))
        for fname in fnames:
            meas_name_full = os.path.split(fname)[-1] #in case the measurements are in some subdirectory
            meas_name = meas_name_full.split('.')[0] #we remove extension here
            meas_ext  = meas_name_full.split('.')[1]
            #adjust for wave parameters and binary
            meas_ext = meas_ext.split('_')[0] #remove _binary
            if self.options['wave_params_flg']: #then make s param
                meas_ext = 's'+meas_ext.strip('w').strip('p')+'p'
            snp_name =  cal_folder_name+'_0.'+meas_ext
            copy_src = os.path.join(cal_folder_full,meas_name,snp_name)
            meas = meas_name+'.'+meas_ext
            copy_dst = os.path.join(self.out_dir,subdir,meas)#now set our copy destination
            #now we actually copy
            copyfile(copy_src,copy_dst)
            #make list of output file names
            fname_out_list.append(meas)
        #now update the metafile entry
        #this assumes that all of the files have been read and written in order
        self.mfc.set_filename(fname_out_list) #set list to metafile
        self._update_metafile(subdir)
        '''

if __name__=='__main__':
    '''
    mf_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\antennas\Measurements\6-25-2019\synthetic_aperture\metafile.json"
    out_dir = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\antennas\Measurements\calibrated\6-25-TEST'
    in_cal_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\antennas\Measurements\6-25-2019\cal\calibration_pre\cal_pre_vnauncert_Results\Solution.meas"
    '''
    mf_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-27-2018\processed\synthetic_aperture\metaFile.json"
    out_dir = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\uncertainty_testing\8-27-2018'
    in_cal_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-27-2018\processed\cal\lsna_calibration_vnauncert_Results\Solution.meas"
    
    mycs = CalibrateSamurai(mf_path,out_dir,in_cal_path,post_proc_template_override=default_pp_cal_template)
    
    #now move calibrated results
    mycs.update_metafile_and_move()





