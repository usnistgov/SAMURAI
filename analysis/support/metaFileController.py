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

from samurai.analysis.support.snpEditor import SnpEditor as snp
from samurai.analysis.support.generic import deprecated


class MetaFileController(OrderedDict):
    
    def __init__(self,metafile_path,suppress_empty_warning=0):
        '''
        @brief initialize our class to control our metafile and the data within it
        @param[in] metafile_path - path to the metafile to load (if it doesnt exist it will be created)
        @param[in/OPT] supress_empty_warning - dont give a warning if the file loaded doesnt exist or is empty
        '''
        OrderedDict.__init__(self) #initialize ordereddict
        self.load(metafile_path,suppress_empty_warning)
        
       
    #load file
    def load(self,metafile_path,suppress_empty_warning=0):
        '''
        @brief load a json metafile
        @param[in] metafile_path - path to the metafile to load, create one if it doesnt exist
        @param[in] suppress_empty_warning - if true suprress the warning that an empty file was created
        '''
        metaPath = metafile_path
        
        #if(prompt):
        #    metaPath = tkFileDialog.askopenfilename(initialdir='../../',title='Select Metadata File',filetypes=(('Synthetic Aperture MetaFile','*.json'),));

        #create an empty class if no metafile was defined
        if not os.path.exists(metafile_path):
            if not suppress_empty_warning:
                print("No metafile specified - Creating empty file")
            [metadir,metafile]= os.path.split(metaPath)
            self.metafile = metafile
            self.metadir  = metadir
            #self.jsonData = OrderedDict()
        else:
            #here we assume the working directory is the location of our metafile
            [metadir,metafile]= os.path.split(metaPath)
            self.metafile = metafile
            self.metadir     = metadir
            with open(metaPath,'r') as jsonFile:
                #self.jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
                self.update(json.load(jsonFile, object_pairs_hook=OrderedDict))
                self.jsonData = self
    
    @property
    def wdir(self):
        '''
        @brief property to return working directory
        @return the working directory
        '''
        return self.get_wdir()
    
    @wdir.setter
    def wdir(self,path):
        '''
        @brief set the wdir property
        '''
        self.set_wdir(path)

    def get_wdir(self):
        '''
        @brief get the working directory
        '''
        return self.jsonData['working_directory'].strip()
        
    #update working directory to current location
    def set_wdir(self,wdir=''):
        '''
        @brief set the working directory
        @param[in/OPT] wdir - the new working directory to set. if '' use the directory the file was opened from
        '''
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
    
    @property
    def measurements(self):
        '''
        @brief property to quickly access measurements
        '''
        return self.jsonData['measurements']
    
    def get_meas(self,measNum=-1):
        '''
        @brief get measurement info from the metafile
        @param[in/OPT] measNum - which measurement number to get. -1 will return a list of all of them
        '''
        if not hasattr(measNum,'__iter__'):#first change to list if its a single input
                measNum = [measNum]
        if(measNum[0]<0):
            #load all
            return self.jsonData['measurements']
        else:
            return [self.jsonData['measurements'][num] for num in measNum]
        
    def get_meas_path(self,measNum=-1):
        '''
        @brief get the measurement path
        @param[in/OPT] measNum - which measurement to get. -1 will return a list of all of them
        '''
        if(measNum<0):
            #load all
            wdir = self.get_wdir()
            measPathList = [os.path.join(wdir,meas['filename'].strip()) for meas in self.jsonData['measurements']]
            return measPathList
        else:
            return os.path.join(self.get_wdir(),self.jsonData['measurements'][measNum])
        
    def set_meas(self,measurements,measNum=-1):
        '''
        @brief set measurement data
        @param[in] measurement - dictionary of list of dictionaries describing th emeasurements
        @param[in/OPT] measNum - which measurement to change. if -1, set the whole 'measurement' list
        '''
        self.saved = 0
        if(measNum<0):
            #write whole list
            self.jsonData['measurements']=measurements
        else:
            self.jsonData['measurements'][measNum] = measurements
        
    def write(self,outPath='default'):
        '''
        @brief write out edited metafile
        @param[in/OPT] outPath - path where to write out file. If not specified, use the previous filename
        '''
        self.saved = 1
        if(outPath=='default'):
            outPath = os.path.join(self.metadir,self.metafile)
        with open(outPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4) 
            
    #now functions for dealing with the data
    @deprecated("Use MetaFileController.load_data() method")
    def load_all_meas(self):
        '''
        @brief load s2p files into this class DEPRECATED
        @DEPRECATED use load_data method
        '''
        self.s2pData = []
        self.numLoadedMeas = 0
        measurements = self.jsonData['measurements']
        for meas in measurements:
            self.s2pData.append(snp(meas['filename'].strip()))
            self.numLoadedMeas+=1
            
    def load_data(self,verbose=False,read_header=True):
        '''
        @brief load up all measurements into list of snp or wnp files
        @param[in/OPT] verbose - whether or not to be verbose when loading
        @param[in/OPT] read_header - whether or not to skip reading the header. Should be faster with false
        @return list of snp or wnp classes
        '''
        snpData = []
        numLoadedMeas = 0
        wdir = self.wdir
        measurements = self.jsonData['measurements']
        if verbose: print("Loading Measurement %5d" %(0),end='')
        for meas in measurements:
            snpData.append(snp(os.path.join(wdir,meas['filename'].strip()),read_header=read_header))
            numLoadedMeas+=1
            if verbose: 
                if not numLoadedMeas%10: 
                    print("%s %5d" %('\b'*6,numLoadedMeas),end='')
        if verbose: print("\nLoading Complete")
        return snpData,numLoadedMeas
    
    def get_positions(self,meas_num=-1):
        '''
        @brief get all of the location vectors for each measurement
        @param[in/OPT] meas_num which measurement position to load (-1 for all)
        @return np array of measurement locations or a single set of location data
        '''
        if(meas_num<0):
            loc_list = []
            for meas in self.measurements:
                loc_list.append(meas['position'])
            return np.array(loc_list)
        else:
            return meas[meas_num]['position']

    @property
    def filenames(self):
        '''
        @brief property to get list of filenames with absolute paths
        '''
        return self.get_filename_list(abs_path=True)

    def get_filename_list(self,abs_path=False):
        '''
        @brief get a list of the filenames from the metafile
        @param[in/OPT] abs_path - whether or not to return an absolute path (default False)
        '''
        fnames = []
        measurements = self.jsonData['measurements']
        for meas in measurements:
            cur_fname = meas['filename'].strip()
            if(abs_path):
                #then add the wdir
                cur_fname = os.path.join(self.get_wdir(),cur_fname)
            fnames.append(cur_fname)
        return fnames

    def get_filename(self,meas_num,abs_path=False):
        '''
        @brief get a single filename metafile
        @param[in] meas_num - which measurement to get the filename of (index from 0)
        @param[in/OPT] abs_path - whether or not to return an absolute path (default False)
        '''
        meas = self.jsonData['measurements'][meas_num]
        fname = meas['filename'].strip()
        if(abs_path):
            #then add the wdir
            fname = os.path.join(self.get_wdir(),fname)
        return fname
    
    #write filenames, default to whole list
    #assumes with respect to working directory
    def set_filename(self,fnames,meas_num=-1):
        '''
        @brief set the filenames of measurements
        @param[in] fnames - name or list of names of the files
        @param[in/OPT] meas_num - which measurement to set. -1 for all
        '''
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
        
#alias
metaFileController = MetaFileController         

      
#update to current directory
def update_wdir(metaFile='metafile.json'):
    '''
    @brief set the wdir to the current directory
    '''
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
        split_mfc = metaFileController(metafile_path,suppress_empty_warning=1) 
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


from shutil import copyfile

def copy_s_param_measurement_to_binary(metafile_path,output_directory):
    '''
    @brief move a metafile and corresponding measurements from s2p to s2p_binary
    @param[in] metafile_path - path of the metafile to move 
    @param[in] output_directory - location to output the binary data to 
    @return name of the new metafile (will simply append '_binary')
    '''
    mfc = MetaFileController(metafile_path) #load the metafile

    #now load in and save out all of the measurements
    for i,f in enumerate(mfc.filenames):
        print("Moving : %s" %(f))
        s = snp(f) #load in the file
        [_,name] = os.path.split(f) #get the file name
        name = name+'_binary' #append _binary to extension
        s.write(os.path.join(output_directory,name)) #write the file out
        mfc.set_filename(name,i) #update the file name in the metafile
    mfc.set_wdir(output_directory) #set the working directory to the output directory
    new_name = 'metafile_binary.json'
    mfc.write(os.path.join(output_directory,new_name)) #write out the metafile
    return new_name
            
            
