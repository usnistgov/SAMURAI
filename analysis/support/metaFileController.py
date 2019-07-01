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
from shutil import copyfile,copy
import numpy as np

from samurai.analysis.support.snpEditor import SnpEditor as snp
from samurai.analysis.support.generic import deprecated
from samurai.analysis.support.SamuraiPlotter import SamuraiPlotter
from samurai.acquisition.support.samurai_apertureBuilder import v1_to_v2_convert #import v1 to v2 conversion matrix
from samurai.acquisition.support.samurai_optitrack import MotiveInterface
from samurai.analysis.support.SamuraiCalculatedSyntheticAperture import CalculatedSyntheticAperture


class MetaFileController(OrderedDict):
    

    def __init__(self,metafile_path,suppress_empty_warning=0):
        '''
        @brief initialize our class to control our metafile and the data within it
        @param[in] metafile_path - path to the metafile to load (if it doesnt exist it will be created)
        @param[in/OPT] supress_empty_warning - dont give a warning if the file loaded doesnt exist or is empty
        '''
        OrderedDict.__init__(self) #initialize ordereddict
        self.load(metafile_path,suppress_empty_warning)
        self.plotter = SamuraiPlotter()
        
        self.unit_conversion_dict = { #dictionary to get to meters
                'mm': 0.001,
                'cm': 0.01,
                'm' : 1,
                'in': 0.0254
                }
        
       
    ###########################################################################
    ### File IO methods
    ###########################################################################
    def load(self,metafile_path,suppress_empty_warning=0):
        '''
        @brief load a json metafile
        @param[in] metafile_path - path to the metafile to load
        @param[in] suppress_empty_warning - if true suprress the warning that an empty file was created
        '''        
        #if(prompt):
        #    metaPath = tkFileDialog.askopenfilename(initialdir='../../',title='Select Metadata File',filetypes=(('Synthetic Aperture MetaFile','*.json'),));

        #create an empty class if no metafile was defined
        if not os.path.exists(metafile_path):
            raise FileNotFoundError("File '{}' not found".format(os.path.abspath(metafile_path)))
        else:
            #here we assume the working directory is the location of our metafile
            [wdir,metafile]= os.path.split(metafile_path)
            self.metafile = metafile
            self.wdir     = wdir
            with open(metafile_path,'r') as jsonFile:
                #self = json.load(jsonFile, object_pairs_hook=OrderedDict)
                self.update(json.load(jsonFile, object_pairs_hook=OrderedDict))
            self.update_format() #update if the format is bad
                
    def write(self,outPath='default'):
        '''
        @brief write out edited metafile
        @param[in/OPT] outPath - path where to write out file. If not specified, use the previous filename
        @return the path to the written file
        '''
        self.saved = 1
        if(outPath=='default'):
            outPath = os.path.join(self.wdir,self.metafile)
        with open(outPath,'w+') as jsonFile:
            json.dump(self,jsonFile,indent=4) 
        return outPath
            
    #now functions for dealing with the data
    @deprecated("Use MetaFileController.load_data() method")
    def load_all_meas(self):
        '''
        @brief load s2p files into this class DEPRECATED
        @DEPRECATED use load_data method
        '''
        self.s2pData = []
        self.numLoadedMeas = 0
        measurements = self['measurements']
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
        measurements = self['measurements']
        if verbose: print("Loading Measurement %5d" %(0),end='')
        for meas in measurements:
            snpData.append(snp(os.path.join(wdir,meas['filename'].strip()),read_header=read_header))
            numLoadedMeas+=1
            if verbose: 
                if not numLoadedMeas%10: 
                    print("%s %5d" %('\b'*6,numLoadedMeas),end='')
        if verbose: print("\nLoading Complete")
        return snpData,numLoadedMeas
    
    def update_format(self):
        '''
        @brief Update our metafile format to the most recent. This takes care
            of things such as old positioner reference frames and old maturo
            positioner data
        '''
        if self["positioner"]=='maturo':
            #then finangle the positions to match the meca
            for i,m in enumerate(self.get_meas()): #loop through all measurements
                pos = np.array(m['position'])
                pos_mm = pos*10 #cm to mm
                m['units'] = 'mm'
                m['position'] = [pos_mm[3],pos_mm[0],0,0,0,0]
                self.set_meas(m,i)
        else:
            if(self['metafile_version']<2): #if pre v2, we need to convert
                for i,m in enumerate(self.get_meas()): #loop through all measurements
                    pos = m['position']
                    pos = np.matmul(pos,v1_to_v2_convert)
                    m['position'] = pos
                    self.set_meas(m,i)
                 #convert version 1 to version 2
            elif(self['metafile_version']<3): #we are currently on v2
                pass
            
    
    ###########################################################################
    ### Position operations
    ###########################################################################
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
    def positions(self):
        '''
        @brief getter property for positions
        @return numpy array of our positions
        '''
        return self.get_positions()
    
    def get_external_positions(self,label=None,meas_num=-1):
        '''
        @brief get externally measured positions. 
            If label is specified, a list of positional data for the data point
            or rigid body with that label will be returned. This return value
            will be a list of dictionaries with the entries various entries providing info on the measurements
        @param[in/OPT] meas_num - which measurement position to load (-1 for all)
        @param[in/OPT] label - what marker label to pull out (if none, get all)
        '''
        ext_meas_key = 'external_position_measurements'
        if meas_num<0:
            if not label:
                rv = [d[ext_meas_key] for d in self['measurements']]
            else:
                rv = [d[ext_meas_key][label] for d in self['measurements']]
        else:
            if not hasattr(meas_num,'__iter__'):
                meas_num=[meas_num] #make sure its a list (so we can support lists of indices)
            if not label:
                rv = [self['measurements'][i][ext_meas_key] for i in meas_num]
            else:
                rv = [self['measurements'][i][ext_meas_key][label] for i in meas_num]
            if len(rv)==1:
                rv = rv[0] #if we have only 1 value dont return a list
        return rv
            
        
    @property
    def external_positions(self):
        '''
        @brief getter for external positions
        '''
        return self.get_external_positions()
    
    def get_external_positions_labels(self):
        '''
        @brief get the labels of all of the external positions (use the first measurement)
        '''
        ext_pos = self.get_external_positions(meas_num=0)
        return ext_pos.keys()
    
    def get_external_positions_mean(self,label,meas_type='position',meas_num=-1):
        '''
        @brief get mean from our external positions
        @param[in] label - label of the marker or rigid body to get the mean of
        @param[in/OPT] meas_type - the type of measurement we want the mean of
            -for rigid bodies, this should be 'position' or 'rotation'.
            -for single markers this should be 'position' or 'residual'
        @return numpy array of [X,Y,Z] mean values (or alpha,beta,gamma or scalar for residual)
        '''
        return self._get_external_positions_value('mean',label,meas_type,meas_num)
    
    def get_external_positions_std(self,label,meas_type='position',meas_num=-1):
        '''
        @brief get standard deviation from our external positions
        @param[in] label - label of the marker or rigid body to get the stdev of
        @param[in/OPT] meas_type - the type of measurement we want the stdev of
            -for rigid bodies, this should be 'position' or 'rotation'.
            -for single markers this should be 'position' or 'residual'
        @return numpy array of [X,Y,Z] stdev values (or alpha,beta,gamma or scalar for residual)
        '''
        return self._get_external_positions_value('standard_deviation',label,meas_type,meas_num)
    
    def get_external_positions_cov(self,label,meas_type='position',meas_num=-1):
        '''
        @brief get covariance matrix from our external positions
        @param[in] label - label of the marker or rigid body to get the covariance matrix of
        @param[in/OPT] meas_type - the type of measurement we want the covariance matrix of
            -for rigid bodies, this should be 'position' or 'rotation'.
            -for single markers this should be 'position' or 'residual'
        @return numpy array of covariance matrices value (or alpha,beta,gamma or scalar for residual)
        '''
        return self._get_external_positions_value('covariance_matrix',label,meas_type,meas_num)
    
    def get_external_positions_units(self):
        '''
        @brief return the units our external positions are in
            pre v2.01 we assume mm. otherwise get the units from the first measurement
        '''
        if self.version<=2:
            return 'mm'
        else:
            pos = self.get_external_positions(meas_num=0)
            units = pos[pos.keys()[0]]['units']
            return units
        
    def update_external_measurement(self,label,measurement):
        '''
        @brief update (or add) an external measurement to our metafile
        @param[in] measurement - measurement to add. (typically a dictionary)
        '''
        ext_meas_key = 'external_position_measurements'
        for m in self['measurements']:
            m[ext_meas_key].update({label:measurement})
        
        
    def add_external_marker(self,label,data,res_data=None,units='mm',**arg_options):
        '''
        @brief manually add an external position marker
        @param[in] data - the externally measured values
        @param[in/OPT] res_data - data for the residual (just 1 number)
        @param[in/OPT] units - units of the input data
        @param[in/OPT] arg_options - keyword arguments as follows:
            sample_wait_time - time between samples
            id - id of the tag 
        '''
        pos_meas = {}
        pos_meas['id'] = None
        pos_meas['sample_wait_time'] = None
        for k,v in arg_options.items():
            pos_meas[k] = v
            
        meas_units = self.get_external_positions_units() #external measurement units        
        pos_meas['units'] = meas_units
        unit_mult = self.unit_conversion_dict[units]/self.unit_conversion_dict[meas_units]
        data = np.array(data)*unit_mult #ensure its a numpy array
        if data.ndim<2: #then extend to 2 dimensions
            data = data[np.newaxis,:]
        pos_meas['num_samples'] = data.shape[0]
        data_stats = MotiveInterface.calculate_statistics(data)
        if res_data is not None:
            res_stats = MotiveInterface.calculate_statistics(res_data)
        else:
            res_stats = None
        if self.version<=2:  
            pos_meas['position_mm'] = data_stats
            pos_meas['residual_mm'] = res_stats
        else:
            pos_meas['position'] = data_stats
            pos_meas['residual'] = res_stats
        self.update_external_measurement(label,pos_meas)
        
    def add_external_marker_from_file(self,file_path): 
        '''
        @brief add marker data from an external .json file
        @param[in] file_path - path to the file to import positions from
            This file should be a dictionary of positional markers
        '''
        with open(file_path) as fp:
            data = json.load(fp) #load the json data
        for k,v in data.items(): #for each marker
            self.update_external_measurement(k,v) #update measurements
        
    def _get_external_positions_value(self,value,label,meas_type,meas_num):
        '''
        @brief get value from our external positions
        @param[in] value - this can be 'standard_deviation','covariance_matrix','mean'
        @param[in] label - label of the marker or rigid body to get the value of
        @param[in] meas_type - the type of measurement we want the value of
            -for rigid bodies, this should be 'position' or 'rotation'.
                This returns a list of [X,Y,Z] (or alpha,beta,gamma values)
            -for single markers this should be 'position' or 'residual'
                which will return a [X,Y,Z] values or a single value
        @param[in] meas_num - which measurement ot get (<0 value returns all)
        @return numpy array of [X,Y,Z] values
        '''
        ext_meas_key = 'external_position_measurements'
        if self.version<=2: #remove _mm for pre 2.01 metafiles
            if meas_type in ['position','residual']:
                meas_type+='_mm'
        if(meas_num<0):
            loc_list = [d[ext_meas_key][label][meas_type][value] for d in self['measurements']]
            return np.array(loc_list)
        else:
            return self['measurements'][ext_meas_key][meas_num][label][meas_type][value]
        
    def plot_external_positions(self,label_names=None,ax=None):
        '''
        @brief plot all of our external positions.
            This most likely will only work with MatlabPlotter for quite a while...
        @param[in/OPT] label_names - a list of label names to plot. If none, all labels will be plotted
        @param[in/OPT] ax - axis to plot on. if not available a new figure will be created
        @return handle to the figure
        '''
        if label_names is None:
            label_names = self.get_external_positions_labels()
        elif type(label_names)!=list or type(label_names)!=tuple:
            label_names = [label_names] #check in case we got a single value
        if ax is None:
            fig = self.plotter.figure(); self.plotter.hold('on',nargout=0); ax = self.plotter.gca()
        for l in label_names:   
            pos = self.get_external_positions_mean(l)
            self.plotter.scatter3(ax,*tuple(pos.transpose()),DisplayName=l)
        self.plotter.legend(interpreter=None,nargout=0)
        return fig
        
    
    ###########################################################################
    ### Getters and setters for various things
    ###########################################################################
    @property
    def version(self):
        '''
        @brief getter for version
        @return the metafile version
        '''
        return self['metafile_version']
    
    @property
    def wdir(self):
        '''
        @brief property to return working directory
        @return the working directory
        '''
        return self['working_directory'].strip()
    
    @wdir.setter
    def wdir(self,path):
        '''
        @brief set the wdir property
        '''
        self.set_wdir(path)
        
    #update working directory to current location
    def set_wdir(self,wdir=None):
        '''
        @brief set the working directory
        @param[in/OPT] wdir - the new working directory to set. if '' use the directory the file was opened from
        '''
        if(wdir==''):
            wdir = self.wdir
        wdir = os.path.abspath(wdir)
        self.saved=0
        # Update the name and working directory
        self.update({'working_directory':wdir})
        self.update({'metafile_path':self.metafile})
        
    def get_timestamp_data(self,measNum=0):
        ts = self['measurements'][measNum]['timestamp']
        [ts_date, ts_time] = filter(None,ts.split())
        [ts_year,ts_month,ts_day] = ts_date.split('-')
        return ts, ts_month, ts_day, ts_year, ts_time
    
    @property
    def measurements(self):
        '''
        @brief property to quickly access measurements
        '''
        return self['measurements']
    
    def get_meas(self,measNum=-1):
        '''
        @brief get measurement info from the metafile
        @param[in/OPT] measNum - which measurement number to get. -1 will return a list of all of them
        '''
        if not hasattr(measNum,'__iter__'):#first change to list if its a single input
                measNum = [measNum]
        if(measNum[0]<0):
            #load all
            return self['measurements']
        else:
            return [self['measurements'][num] for num in measNum]
        
    @deprecated("Please use self.get_filename_list() or self.filenames")
    def get_meas_path(self,measNum=-1):
        '''
        @brief get the measurement path
        @param[in/OPT] measNum - which measurement to get. -1 will return a list of all of them
        '''
        if(measNum<0):
            #load all
            wdir = self.wdir
            measPathList = [os.path.join(wdir,meas['filename'].strip()) for meas in self['measurements']]
            return measPathList
        else:
            return os.path.join(self.wdir,self['measurements'][measNum])
        
    def set_meas(self,measurements,measNum=-1):
        '''
        @brief set measurement data
        @param[in] measurement - dictionary of list of dictionaries describing th emeasurements
        @param[in/OPT] measNum - which measurement to change. if -1, set the whole 'measurement' list
        '''
        self.saved = 0
        if(measNum<0):
            #write whole list
            self['measurements']=measurements
        else:
            self['measurements'][measNum] = measurements

    @property
    def filenames(self):
        '''
        @brief property to get list of filenames with absolute paths
        '''
        return self.get_filename_list(abs_path=True)
    
    @filenames.setter
    def filenames(self,path_list):
        '''
        @brief set the filenames from a list
        '''
        self.set_filename(path_list)

    def get_filename_list(self,abs_path=False):
        '''
        @brief get a list of the filenames from the metafile
        @param[in/OPT] abs_path - whether or not to return an absolute path (default False)
        '''
        fnames = []
        measurements = self['measurements']
        for meas in measurements:
            cur_fname = meas['filename'].strip()
            if(abs_path):
                #then add the wdir
                cur_fname = os.path.join(self.wdir,cur_fname)
            fnames.append(cur_fname)
        return fnames

    def get_filename(self,meas_num,abs_path=False):
        '''
        @brief get a single filename metafile
        @param[in] meas_num - which measurement to get the filename of (index from 0)
        @param[in/OPT] abs_path - whether or not to return an absolute path (default False)
        '''
        meas = self['measurements'][meas_num]
        fname = meas['filename'].strip()
        if(abs_path):
            #then add the wdir
            fname = os.path.join(self.wdir,fname)
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
            num_meas = len(self['measurements']) #get the number of measurements
            if(num_meas!=len(fnames)):
                raise ValueError("Filename list length does not match number of measurements in metafile")
                return -1
            for i in range(num_meas):
                self['measurements'][i]['filename'] = os.path.relpath(fnames[i],self.wdir) #set the filename from the list
        else: #its a meas index then
            self['measurements'][meas_num]['filename'] = os.path.relpath(fnames,self.wdir) #should just be one name here
        return 0
    
    def set_calibration_file(self,calfile,measNum=-1,set_calibrated_flg=True):
        self.saved = 0
        if(measNum<0):
            measurements = self['measurements']
            for meas in measurements:
                meas['calibration_file'] = calfile
                if(set_calibrated_flg):
                    meas.update({'calibrated':True})
            self['measurements'] = measurements
            
    def add_calibrated_filename(self,dutDir,measNum=-1,set_calibrated_flg=True):
        self.saved = 0
        if(measNum<0):
            measurements = self['measurements']
            for meas in measurements:
                #assume muf format with DUTs all in single folder and s2ps in subfolders
                s2pDir = meas['filename'].split('.')[0].strip()+'_Support'
                cal_fname = meas['filename'].split('.')[0].strip()+'_0.s2p'
                cal_path = os.path.join(dutDir,s2pDir,cal_fname)
                cal_rel  = os.path.relpath(cal_path,self.wdir)
                meas.update({'calibrated_filename': cal_rel})
                
                if(set_calibrated_flg):
                    meas.update({'calibrated':True})
                    
            self['measurements'] = measurements
            
    def get_header_dict(self):
        #just get the header out of the data (everytrhing but the mesaurements)
        non_header_keys = ['measurements']
        myheaderdict = {k: v for k,v in self.items() if k not in non_header_keys}
        return myheaderdict
    
    def rename(self,new_name):
        self.metafile = new_name
        
    def get_metafile_name_no_extension(self):
        return self.metafile.split('.')[-2]
        
#alias
metaFileController = MetaFileController         

###########################################################################
### various useful functions
###########################################################################
from samurai.analysis.support.MUFResult import MUFResult

def copy_touchstone_from_muf(self,metafile,out_dir='./touchstone'):
    '''
    @brief take a metafile with *.meas data and copy the touchstone (*.snp/wnp) files
        to a new directory with a new metafile (for backward compatability with peter)
    @param[in] metafile - metafile containing the *.meas files
    @param[in/OPT] out_dir - output directory to save the new files to. Defaults to './touchstone'
    '''
    #open the metafile
    mf = MetaFileController(metafile)
    fnames = mf.filenames
    #make the dir if it doesnt exist
    if not os.path.exists(os.path.join(out_dir)):
        os.mkdir(os.path.join(out_dir))
    #now loop through our filenames and get the nominal paths
    nominal_paths = []
    print("Getting nominal values from *.meas files")
    for fname in fnames:
        mr = MUFResult(fname,no_load=True) #do not load the data, just parse the XML
        nominal_paths.append(mr.nominal_value_path) #get the nominal value
    #now copy all of our nominal paths to the output directory
    print("Copying Files: {:5}/{:5}".format(0,len(nominal_paths)),end='')
    out_file_paths = []
    for i,nom_path in enumerate(nominal_paths):
        out_file_paths.append(copy(nom_path,out_dir))
        if not i%10:
            print("\b"*11+"{:5}/{:5}".format(i,len(nominal_paths)))
    #now update our metafile with the new paths and working directory
    mf.set_wdir(out_dir)
    mf.filenames = out_file_paths
    mf.write()
    
        
        

#update to current directory
def update_wdir(metafile_path):
    '''
    @brief set the wdir to the current directory
    @param[in] metafile_path - path to the metafile
    '''
    mymfc = metaFileController(metafile_path)
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
        split_mfc.update(mymfc_header)
        meas_nums = meas_split[i]
        split_mfc['total_measurements'] = len(meas_nums)
        split_mfc['completed_measurements'] = len(meas_nums)
        meas_dict_list = mymfc.get_meas(meas_nums)
        split_mfc.update({'measurements':meas_dict_list})
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
    num_meas = mymfc['total_measurements']
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


#from shutil import copyfile

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
            
            
if __name__=='__main__':
    metafile_path = r'./metafile_v2.json'
    #maturo_metafile_path = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-27-2018\processed\synthetic_aperture\metaFile.json'
    mf = MetaFileController(metafile_path)
    #mmf = MetaFileController(maturo_metafile_path)
    #5-17-2019 data
    beam3_loc = [-0.001949,0.747873,-0.1964127] #in meters
    beam2_loc = [1.234315,0.864665,-0.2195737] #in meters
    mf.add_external_marker('beam-3',beam3_loc,units='m')
    mf.add_external_marker('beam-2',beam2_loc,units='m')
    mf.plot_external_positions()
    
    
    
    
    
    