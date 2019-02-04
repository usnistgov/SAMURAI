# -*- coding: utf-8 -*-
"""
Created on Mon May 14 08:34:24 2018

This script edits our metafile and moves our data and new copy of metafile to outDir
This assumes our data has been calibrated with the MUF and DUTs are within that output directory form the MUF

@author: ajw5
"""

from collections import OrderedDict
import json
import os
from shutil import copyfile
import numpy as np

import sys
snpEdPath = 'Q://public//Quimby//Students//Alec//Useful_Code//'
sys.path.append(snpEdPath)
from snpEditor import s2pEditor as s2p


class metaFileController():
    
    def __init__(self,metafile='',wdir='./',suppress_empty_warning=0):
        #self.root = tk.Tk();
        #self.root.withdraw();
        #load in our json file
        self.load(metafile,wdir,suppress_empty_warning)
        
       
    #load file
    def load(self,metafile,wdir='./',suppress_empty_warning=0):
        
        metaPath = os.path.join(wdir,metafile)
        
        #if(prompt):
        #    metaPath = tkFileDialog.askopenfilename(initialdir='../../',title='Select Metadata File',filetypes=(('Synthetic Aperture MetaFile','*.json'),));

        #create an empty class if no metafile was defined
        if not metafile:
            if not suppress_empty_warning:
                print("No metafile specified - Creating empty file")
            self.metafile = 'metafile.json'
            self.metadir  = os.path.abspath('./')
            self.jsonData = OrderedDict()
        else:
            #here we assume the working directory is the location of our metafile
            [metadir,metafile]= os.path.split(metaPath)
            self.metafile = metafile
            self.metadir     = metadir
            with open(metaPath,'r') as jsonFile:
                self.jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
            
    def get_wdir(self):
        return self.jsonData['working_directory'].strip()
        
    #update working directory to current location
    def set_wdir(self,wdir=''):
        if(wdir!=''):
            self.metadir = wdir
        wdir = os.path.abspath(self.metadir)
        self.saved=0
        # Update the name and working directory
        self.jsonData.update({'working_directory':wdir})
        self.jsonData.update({'metafile_path':self.metafile})
        
    def get_timestamp_data(self,measNum=0):
        ts = self.jsonData['measurements'][measNum]['timestamp']
        [ts_date, ts_time] = filter(None,ts.split())
        [ts_year,ts_month,ts_day] = ts_date.split('-')
        return ts, ts_month, ts_day, ts_year, ts_time
    
    def get_meas(self,measNum=-1):
        if not hasattr(measNum,'__iter__'):#first change to list if its a single input
                measNum = [measNum]
        if(measNum[0]<0):
            #load all
            return self.jsonData['measurements']
        else:
            return [self.jsonData['measurements'][num] for num in measNum]
        
    def get_meas_path(self,measNum=-1):
        if(measNum<0):
            #load all
            wdir = self.get_wdir()
            measPathList = [os.path.join(wdir,meas['filename'].strip()) for meas in self.jsonData['measurements']]
            return measPathList
        else:
            return os.path.join(self.get_wdir(),self.jsonData['measurements'][measNum])
        
    def set_meas(self,measurements,measNum=-1):
        self.saved = 0
        if(measNum<0):
            #write whole list
            self.jsonData['measurements']=measurements
        else:
            self.jsonData['measurements'][measNum] = measurements
        
    def write(self,outPath='default'):
        self.saved = 1
        if(outPath=='default'):
            outPath = os.path.join(self.metadir,self.metafile)
        with open(outPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4) 
            
    #now functions for dealing with the data
    def load_all_meas(self):
        self.s2pData = []
        self.numLoadedMeas = 0
        measurements = self.jsonData['measurements']
        for meas in measurements:
            self.s2pData.append(s2p(meas['filename'].strip()))
            self.numLoadedMeas+=1
            
    def get_filename_list(self,abs_path=False):
        fnames = []
        measurements = self.jsonData['measurements']
        for meas in measurements:
            cur_fname = meas['filename'].strip()
            if(abs_path):
                #then add the wdir
                cur_fname = os.path.join(self.get_wdir(),cur_fname)
            fnames.append(cur_fname)
        return fnames
    
    #write filenames, default to whole list
    #assumes with respect to working directory
    def set_filename(self,fnames,meas_num=-1):
        if(meas_num<0):
            num_meas = len(self.jsonData['measurements']) #get the number of measurements
            if(num_meas!=len(fnames)):
                print("ERROR: Filename list length does not match number of measurements in metafile")
                return -1
            for i in range(num_meas):
                self.jsonData['measurements'][i]['filename'] = fnames[i] #set the filename from the list
        else: #its a meas index then
            self.jsonData['measurements'][meas_num]['filename'] = fnames #should just be one name here
        return 0
    
    def set_calibration_file(self,calfile,measNum=-1,set_calibrated_flg=True):
        self.saved = 0
        if(measNum<0):
            measurements = self.jsonData['measurements']
            for meas in measurements:
                meas['calibration_file'] = calfile
                if(set_calibrated_flg):
                    meas.update({'calibrated':True})
            self.jsonData['measurements'] = measurements
            
    def add_calibrated_filename(self,dutDir,measNum=-1,set_calibrated_flg=True):
        self.saved = 0
        if(measNum<0):
            measurements = self.jsonData['measurements']
            for meas in measurements:
                #assume muf format with DUTs all in single folder and s2ps in subfolders
                s2pDir = meas['filename'].split('.')[0].strip()+'_Support'
                cal_fname = meas['filename'].split('.')[0].strip()+'_0.s2p'
                cal_path = os.path.join(dutDir,s2pDir,cal_fname)
                cal_rel  = os.path.relpath(cal_path,self.get_wdir())
                meas.update({'calibrated_filename': cal_rel})
                
                if(set_calibrated_flg):
                    meas.update({'calibrated':True})
                    
            self.jsonData['measurements'] = measurements
            
    def get_header_dict(self):
        #just get the header out of the data (everytrhing but the mesaurements)
        non_header_keys = ['measurements']
        myheaderdict = {k: v for k,v in self.jsonData.items() if k not in non_header_keys}
        return myheaderdict
    
    def rename(self,new_name):
        self.metafile = new_name
        
    def get_metafile_name_no_extension(self):
        return self.metafile.split('.')[-2]
        
            

      
#update to current directory
def update_wdir(metaFile='metafile.json'):
    mymfc = metaFileController(metaFile)
    mymfc.set_wdir() #set current directory as working directory
    mymfc.write()
    

#import copy
def split_metafile(metafile_path,meas_split,label='split'):
    '''
    @brief - This function provides the ability to split a metafile. The allows a single
    measurement to be split into multiple (in the case of taking multiple 
    apertures in a single measurement).
    
    @param[in]  metafile_path - path for metafile to split
    @param[in]  meas_split    - list of lists telling what measurements in which new metafiles
    @param[in]  label         - label added to end of metafile followed by '_#'
    '''
    mymfc = metaFileController(metafile_path)
    mymfc_header = mymfc.get_header_dict()
    mymfc_mf_name = mymfc.get_metafile_name_no_extension()
    num_splits = np.size(meas_split,0)
    for i in range(num_splits):
        # Open blank metafile, then add header and our measurements
        split_mfc = metaFileController(suppress_empty_warning=1) 
        split_mfc.jsonData.update(mymfc_header)
        meas_nums = meas_split[i]
        split_mfc.jsonData['total_measurements'] = len(meas_nums)
        split_mfc.jsonData['completed_measurements'] = len(meas_nums)
        meas_dict_list = mymfc.get_meas(meas_nums)
        split_mfc.jsonData.update({'measurements':meas_dict_list})
        # Now we can change the name and write out.
        mf_name   = mymfc_mf_name+'_'+label+'_'+str(i)+'.json'
        split_mfc.rename(mf_name)
        split_mfc.set_wdir()
        split_mfc.write()
        
# Evenly split into N apertures
def evenly_split_metafile(metafile_path,num_splits,label='split'):
    '''
    @brief - evenly split .json metafile into num_splits different files. 
        split files are named in the following form <name>_<label>_#.json.
        Files will be written to same diretory as json file
    @param[in] - metafile_path - .json file with metafile information
    @param[in] - num_splits - number of even splits to make
    @param[in] - label - label to append to filename when written out
    '''
    
    # First we get the number of measurements per split.
    mymfc = metaFileController(metafile_path)
    num_meas = mymfc.jsonData['total_measurements']
    num_meas_per_split = num_meas/num_splits
    # Now we will generate the split lists for splitting.
    meas_split_boundaries = [[i*num_meas_per_split,(i+1)*num_meas_per_split] 
                                for i in range(num_splits)] #generate start and stops of each split
    for start,stop in meas_split_boundaries: #make sure we have an even split
        if not start.is_integer() or not stop.is_integer():
            print("ERROR: Split boundaries are not an integer. Please ensure that the number of measurements are evenly divisible by the 'num_splits'.[%f,%f]" %(start,stop))
            return -1
    meas_split = [range(int(start),int(stop)) for start,stop in meas_split_boundaries]
    split_metafile(metafile_path,meas_split)
    
        
        
            
            
