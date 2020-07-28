# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5, bfj
"""

from samurai.base.TouchstoneEditor import TouchstoneEditor,TouchstoneError, SnpEditor,WaveformEditor
from samurai.base.TouchstoneEditor import TouchstoneParam, split_parameters, combine_parameters
from samurai.base.generic import complex2magphase, magphase2complex
from samurai.base.generic import get_name_from_path
from samurai.base.generic import ProgressCounter
from samurai.base.SamuraiDict import SamuraiDict
from samurai.base.MUF.MUFResult import MUFResult,mufPathFind
from samurai.base.MUF.MUFResult import calculate_confidence_interval,calculate_estimate,calculate_standard_uncertainty

import shutil
import getpass
import datetime
import operator

import numpy as np
import os
import re
import sys

#%% Conversion functions

####################################################
# conversion to/from MUFResult (shallow data copy)
####################################################
def SamuraiMeasurement2MUFResult(sam_meas):
    '''
    @brief Convert data into a MUFResult object from a SamuraiMeasurement (shallow copy of any loaded data)
    @param[in] sam_meas - SamuraiMeasuremnt Object to convert
    '''
    mr = MUFResult() #empty data structure
    for mt in sam_meas.meas_types: #go through each meas type
        mt_attr = getattr(sam_meas,mt) #get the measurements
        mr_mt_attr = getattr(mr,mt)
        for i,item in enumerate(mt_attr): #now copy the data
            mr_mt_attr.add_item(item['file_path'])
            mr_mt_attr[i].data = item.data #copy the data 
    return mr
            
   
def MUFResult2SamuraiMeasurement(mr_obj):
    '''
    @brief Convert a MUFResult object to a SamuraiMeasurement (shallow copy)
    @param[in] mr_obj - MUFResult object to convert
    '''
    sm = SamuraiMeasurement()
    sm.meas_path = mr_obj.meas_path
    for mt in mr_obj.meas_types: #go through each meas type
        mt_attr = getattr(mr_obj,mt) #get the measurements
        sm_mt_attr = getattr(sm,mt)
        for i,item in enumerate(mt_attr): #now copy the data
            sm_mt_attr.add_item(item.filepath)
            sm_mt_attr[i].data = item.data #copy the data 
    return sm

################################################################
# Convert abs paths to relative (with respect to the meas file)
################################################################
def set_meas_relative(meas_path,out_path=None):
    '''
    @brief change all paths in a \*.smeas file to relative paths and save.
        The paths will assume all paths are relative to the \*.meas file.
    @param[in] meas_path - path to \*.meas file
    @param[in/OPT] out_path - path to write out to. If not provided, overwrite the input
    @note This will overwrite the provided file if a new path is not provided
    @note This assumes that all Monte Carlo are in the same folder as are Perturbed
    @return return the updated MUFResult
    '''
    if out_path is None:
        out_path = meas_path
    #first open the xml file
    meas = SamuraiMeasurement(meas_path,load_nominal=False,load_statistics=False)
    meas_dir = os.path.dirname(meas_path)
    #change all the paths
    meas_types = meas.meas_types
    for mt in meas_types:
        meas_obj = getattr(meas,mt) #get the object
        fpaths = meas_obj.filepaths #get the paths 
        if fpaths: # if there are values
            meas_obj.clear_items() #remove the objects with the old paths
            new_path = mufPathFind(fpaths[0], meas_dir) #find first object with respect to the *.meas file
            new_rel_dir = os.path.dirname(os.path.relpath(new_path,meas_dir)) #get the relative path
            rel_paths = [os.path.join('.'+os.path.sep,new_rel_dir,os.path.basename(p)) for p in fpaths]
            meas_obj.add_items(rel_paths) #add the filepaths back
    return meas.write_json(out_path)

def set_meas_absolute(meas_path,out_path=None):
    '''
    @brief change all paths in a \*.smeas file to absolute paths and save.
        The paths will assume all paths are relative to the \*.meas file.
    @param[in] meas_path - path to \*.meas file
    @param[in/OPT] out_path - path to write out to. If not provided, overwrite the input
    @note This will overwrite the provided file if a new path is not provided
    @note This assumes that all Monte Carlo are in the same folder as are Perturbed
    @return return the updated MUFResult
    '''
    if out_path is None:
        out_path = meas_path
    #first open the xml file
    meas = SamuraiMeasurement(meas_path,load_nominal=False,load_statistics=False)
    meas_dir = os.path.dirname(meas_path)
    #change all the paths
    meas_types = meas.meas_types
    for mt in meas_types:
        meas_obj = getattr(meas,mt) #get the object
        fpaths = meas_obj.filepaths #get the paths 
        if fpaths: # if there are values
            for fi,fp in enumerate(fpaths):
                meas_obj[fi]['file_path'] = fp
    return meas.write_xml(out_path)

def combine_measurements(*args,**kwargs):
    '''
    @brief Combine all parameters of a mesaurement into a single measurement
    @param[in] args - paths or Measurement objects to combine (\*.meas or \*.smeas) 
    @param[in/OPT] kwargs - keyword arguments as follows:
        - fill_value - what value to fill undefined parameters (default 0+0j)
    @note This assumes each measurement has the same number of each parameter (e.g. 100 monte carlos)
    @note This currenlty assumes that ports are consecutive (e.g. 11,12,21,22 NOT 11,13,31,33)
    @note This only supports up to 10 ports
    '''
    options = {}
    options.update(kwargs)
    #first load in all our measurements
    meas_in = [SamuraiMeasurement(arg,load_nominal=True,load_statistics=True) for arg in args]
    #split a test case to figure out what we need
    meas_out = SamuraiMeasurement() #an empty measurement for output
    #now lets combine each of our input measurements
    for mt in meas_out.meas_types:
        mt_attr = getattr(meas_out,mt)
        for im in range(len(getattr(meas_in[0],mt))): #loop through each measurement in the inputs
            combined_val = combine_parameters(*tuple([getattr(msin,mt)[im].data for msin in meas_in]), fill_value=options.pop('fill_value',0+0j))    
            mt_attr.add_item(combined_val) #add it to our output measurement
    return meas_out

def split_measurement(meas_path,split):
    '''
    @brief split the data in a measurement into two different measurements.
    @note This must load in all data
    @note This utilizes TouchstoneEditor split_parameters
    @return Metafile instances equal to the split
    '''
    if isinstance(meas_path,SamuraiMeasurement): #allow passing an object
        meas = meas_path
    else:
        #first load the measurement and all its data
        meas = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
    #split a test case to figure out what we need
    test_out = split_parameters(meas.nominal[0].data,split)
    #now create editors equal to the number of test outputs
    meas_out = [SamuraiMeasurement() for i in range(len(test_out))]
    for mt in meas.meas_types: #now lets split everything
        mt_attr = getattr(meas,mt)
        for mval in mt_attr: #loop through each measurement in the type
            split_vals = split_parameters(mval.data,split)
            for i,sv in enumerate(split_vals): #now put back into new split values
                getattr(meas_out[i],mt).add_item(sv) #add the item
    return meas_out
                
    
#%% Operation Function (e.g. FFT) with uncerts
def calculate_time_domain(fd_w_uncert,key=21,window=None,verbose=False):
    '''
    @brief Calculate the fft of a frequency domain value with uncertainties
    @param[in] fd_w_uncert - frequency domain values with uncertainty (e.g. MUFResult instance)
    @param[in/OPT] key - what key (e.g. 21,11,12,22) to calculate fft  (default 21)
    @param[in/OPT] window - windowing to add to the fft calculation
    @param[in/OPT] verbose - whether or not to be verbose on calculations
    @return MUFResult class 
    '''
    td_w_uncert =SamuraiMeasurement()
    for mt in td_w_uncert.meas_types:
        if verbose: print("Calculating {}".format(mt))
        out_meas = getattr(td_w_uncert,mt) #get the measurement of interest
        in_meas  = getattr(fd_w_uncert,mt) #get the input meas of interest
        if verbose and len(in_meas)>1: pc = ProgressCounter(len(in_meas))
        for ii,item in enumerate(in_meas): # go through each item in the measurement
            item_data = item.data
            if item_data is None:
                raise IOError("Item {} of {} has no data. Probably not loaded".format(ii,mt))
            td_vals = item.data[(item.waves[0],key)].calculate_time_domain_data(window=window)
            tdw_vals = WaveformEditor(td_vals.index,td_vals.to_numpy()) # create from Series
            out_meas.add_item(tdw_vals)
            if verbose and len(in_meas)>1: pc.update()
        if verbose and len(in_meas)>1: pc.finalize()
    return td_w_uncert

# alias to ifft
ifft = calculate_time_domain

#%% Class for MUF Interoperability

class SamuraiMeasurement(SamuraiDict):
    '''
    @brief A class to deal with measurements with uncertianties. This is written to be capable 
        of interfacing with data from the MUF. should be drop in replacement for MUFResult class. 
        But more clear and better
    @example
        #Load in a *.meas file (or *.smeas for json) 
        meas_path = './test.meas' #path to *.meas file
        mymeas = SamuraiMeasurement(meas_path) #initialize the class
        mymeas.calculate_monte_carlo_statistics() 
    @example
        #Create a *.meas (or *.smeas for json) file from *.snp files
        mymeas = SamuraiMeasurement()
        mymeas.nominal.add_item('nominal.snp')
        mymeas.monte_carlo.add_item('monte_carlo_0.snp')
        mymeas.monte_carlo.add_item('monte_carlo_1.snp')
        mymeas.perturbed.add_item('perturbed_0.snp')
        mymeas.perturbed.add_item('perturbed_1.snp')
    '''
    meas_types = ['nominal','monte_carlo','perturbed'] #measurement property names
        
    def __init__(self,meas_path=None,**arg_options):
        '''
        @brief load up and initialize the *.meas file
        @param[in] meas_path - path to the *.meas file to load. 
            This can be passed as None if self.create_meas() is going to be run.
            if a *.snp or *.wnp file are provided, it will be loaded and a *.meas 
            file will be created with the loaded measurement as the nominal result
        @param[in/OPT] arg_options - keyword arguments as follows:
            - - all arguments passed to MUFResult.load() method
        '''
        super().__init__()
        #measurement path
        self.meas_path = None
        #options
        self.options = {}
        self.options['ci_percentage'] = 95
        for k,v in arg_options.items():
            self.options[k] = v
        #now load
        self.create_meas() #create the skeleton
        if isinstance(meas_path,str): #load the data
            self.load(meas_path,**arg_options) #pass our kwargs here to for loading if desired
        if isinstance(meas_path,SamuraiMeasurement):
            self = meas_path
      
    ##########################################################################
    ### Properties for easy access
    ##########################################################################
    @property
    def nominal_value_path(self):
        '''@brief property to return the path of the nominal value'''
        return self.nominal[0].file_path
    
    @property
    def nominal_post_value_path(self):
        '''@brief property to return the path of the nominal value'''
        return self.nominal[1].file_path
    
    def __getattr__(self,attr):
        '''@brief pass any nonexistant attribute attempts to our nominal data class'''
        try:
            return getattr(self.nominal[0].data,attr)
        except:
            raise AttributeError('{} not in self or self.nominal'.format(attr))
            
    ##########################################################################
    ### Data editing and statistics functions. only operates on loaded data
    ##########################################################################
        
    def calculate_statistics(self):
        '''@brief calculate statistics for monte carlo and perturbed data'''
        self.monte_carlo.calculate_statistics()
        self.perturbed.calculate_statistics()
        
    def run_touchstone_function(self,funct_name,*args,**kwargs):
        '''
        @brief run a function on all loaded touchstone files
        @param[in] funct_name - the name of the method to run. Should be in TouchstoneEditor
        @param[in/OPT] *args,**kwargs - arguments to pass to function
        @return list of names for what the data was operated on
        '''
        out_list = [] 
        if self.nominal is not None:
            funct = getattr(self.nominal,funct_name)
            funct(*args,**kwargs)
            out_list.append('nominal')
        stats_list = ['monte_carlo','perturbed']
        for stat_name in stats_list:
            stat = getattr(self,stat_name)
            if stat.data is not None:
                out_list.append(stat_name)
                for d in stat.data:
                    funct = getattr(d,funct_name)
                    funct(*args,**kwargs)
        return out_list
 
    ##########################################################################
    ### parts to create a new *.meas file from a *.snp or *.wnp
    ##########################################################################      
        
    def create_meas(self):
        '''@brief create a skeleton for a *.smeas (Samurai Meas) file'''
        self['file_path']= './'
        self['user_name'] = getpass.getuser()
        self['creation_time'] = str(datetime.datetime.now())
        #now create our nominal
        self['nominal'] = SamMeasStatistic(**self.options) #aliased to self.nominal
        #and monte carlo
        self['monte_carlo'] = SamMeasStatistic(**self.options) #aliased to self.monte_carlo
        #and perturbed
        self['perturbed'] = SamMeasStatistic(**self.options) #aliased to self.perturbed
    
    ##########################################################################
    ### extra io functions
    ##########################################################################
    
    def _load_nominal(self,verbose=False):
        '''@brief load the nominal path value into self.nominal'''
        if verbose: print("Loading Nominal")
        self.nominal.load_data(working_directory=self.working_directory,verbose=False)
        
    def _load_statistics(self,verbose=False):
        '''@brief load in all of the data for all of our statistics'''
        if verbose: print("Loading Monte Carlo:")
        self.monte_carlo.load_data(working_directory=self.working_directory,verbose=verbose)
        if verbose: print("Loading Perturbed:")
        self.perturbed.load_data(working_directory=self.working_directory,verbose=verbose)
    
    def _load_xml(self,meas_path,**kwargs):
        '''@brief Load an xml *.meas file'''
        mr = MUFResult(meas_path,load_nominal=False,load_statistics=False)
        sm = MUFResult2SamuraiMeasurement(mr)
        for k,v in sm.items(): #update the current object values
            self[k] = v 
            
    def _load_json(self,meas_path):
        '''@brief Load a json *.smeas file'''
        super().load(meas_path)
        for k,v in self.items():
            if k in self.meas_types:
                self[k] = SamMeasStatistic(v)
        
    def load(self,meas_path,**kwargs):
        '''
        @brief load our meas file and its corresponding data
        @param[in/OPT] meas_path - path to *.meas file to load in. This will overwrite self.meas_path
        @param[in/OPT] kwargs - keyword arguments as follows:
            load_nominal - load our data from the nominal solution(s) (default True)
            load_statistics - load our statistics (monte carlo and perturbed) (default False)
            verbose - be verbose when loading data (default False)
        '''
        options = {}
        options['load_nominal'] = True
        options['load_statistics'] = False
        options['verbose'] = False
        for k,v in kwargs.items():
            options[k] = v
        self.meas_path = meas_path
        #make a *.meas if a wnp or snp file was provided
        #if self.meas_path is not None and os.path.exists(self.meas_path):
        if not os.path.exists(meas_path): #check if the file exists
            raise FileNotFoundError('{} does not exist'.format(self.meas_path))
        _,ext = os.path.splitext(meas_path) #get our extension
        if '.meas'==ext: #load from xml
            self._load_xml(meas_path)
        elif '.smeas'==ext: #load from json
            self._load_json(meas_path)
        else: #if its not a meas file (e.g. touchstone) then create
            self.create_meas()
            self.nominal.add_item(meas_path)

        #load our nominal and statistics if specified
        if options['load_nominal']:
            self._load_nominal(verbose=options['verbose'])
        if options['load_statistics']:
            self._load_statistics(verbose=options['verbose'])
            
    def write_xml(self,out_path,**kwargs):
        '''
        @brief write out our current xml file and corresponding measurements
        @param[in] out_path - path to writ ethe file out to 
        @param[in/OPT] kwargs - keyword arguments as follows
            - relative - write out data with paths relative to the \*.meas file (default False)
        '''
        options = {}
        options['relative'] = False
        for k,v in kwargs.items():
            options[k] = v
        mr = SamuraiMeasurement2MUFResult(self)
        out_path = os.path.splitext(out_path)[0]+'.meas'
        return mr.write_xml(out_path,**options)
        
    def write_json(self,out_path,**kwargs):
        '''
        @brief write our current data to a json file (should be a *.smeas file)
        '''
        options = {}
        options['relative'] = False
        for k,v in kwargs.items():
            options[k] = v
        out_path = os.path.splitext(out_path)[0]+'.smeas'
        rv = super().write(out_path)
        if options['relative']: set_meas_relative(out_path)
        else: set_meas_absolute(out_path)
        return rv
        
    def _write_nominal(self,out_dir,out_name='nominal',**kwargs):
        '''
        @brief write out our nominal data
        @param[in] out_dir - directory to write out to
        @param[in/OPT] out_name - name to write out (default 'nominal')
        @param[in/OPT] kwargs - passed to self._write_statistic
        '''
        self._write_statistic(self.nominal, os.path.join(out_dir,out_name+'_{}'),**kwargs)
        
    def _write_statistic(self,stat_class,format_out_path,**kwargs):
        '''
        @brief write out our statistics data
        @param[in] stat_class - instance of MUFStatistic to write
        @param[in] out_dir - directory to write out to
        @param[in] format_out_path - formattable output path (e.g. path/to/dir/mc_{}.snp)
        @param[in/OPT] kwargs - keyword arguments passed to stat_class[i].data.write()
        @return list of written file paths (absolute paths)
        '''
        options = {'ftype':'binary'}
        options.update(kwargs)
        if format_out_path.count('{}')>1:
            raise Exception("Only one formattable part allowed. '{}' has {}".format(format_out_path,format_out_path.count('{}')))
        out_list = []
        if not hasattr(stat_class, 'data') or stat_class.data is None: #then copy
            files =  stat_class.file_paths
            for i,iFile in enumerate(files):
                fname = os.path.splitext(format_out_path.format(i))[0]
                fname+=os.path.splitext(iFile)[-1]
                fname_out = shutil.copy(iFile,fname)
                fname_out = os.path.abspath(fname_out)
                out_list.append(fname_out) #add to our list
        else:
            for i,dat in enumerate(stat_class.data): #loop through all of our data
                fname = os.path.splitext(format_out_path.format(i))[0]
                fname_out = dat.write(fname,**options)
                fname_out = os.path.abspath(fname_out)
                out_list.append(fname_out)
                
        for i,path in enumerate(out_list):
            stat_class[i]['name'] = get_name_from_path(path)
            stat_class[i]['file_path'] = path
            
        return out_list
    
    def _write_statistics(self,out_dir,**kwargs):
        '''@brief write out monte carlo and perturbed data'''
        #make the directories
        mc_dir = os.path.join(out_dir,'MonteCarlo')
        if not os.path.exists(mc_dir):
            os.makedirs(mc_dir)
        pt_dir = os.path.join(out_dir,'Perturbed')
        if not os.path.exists(pt_dir):
            os.makedirs(pt_dir)
        #write the data
        self._write_statistic(self.monte_carlo, os.path.join(mc_dir,'mc_{}'),**kwargs)
        self._write_statistic(self.perturbed, os.path.join(pt_dir,'pt_{}'),**kwargs)
        
    def _write_data(self,out_dir,**kwargs):
        '''
        @brief write out supporting data for the *.meas file (e.g. nominal/monte_carlo/perturbed *.snp files)
        @param[in] out_dir - what directory to write the data out to
        @param[in/OPT] kwargs - keyword arguments as follows:
            write_nominal - write out our nominal value file in a subfolder of meas_path (default True)
            write_stats - write out our statistics to a subfolder of meas_path (default True)
        @note if the data is not loaded in we will simply copy the files
        '''
        options = {}
        options['write_nominal'] = True
        options['write_stats'] = True
        options.update(kwargs)
        #load our nominal and statistics if specified
        if options.pop('write_nominal'):
            self._write_nominal(out_dir,**options)
        if options.pop('write_stats'):
            self._write_statistics(out_dir,**options)
        
    def write(self,out_path,**kwargs):
        '''
        @brief write out all information on the MUF Statistic. This will create a copy
            of the nominal value and all statistics snp/wnp files
        @param[in] out_path - path to write xml file to. 
            all other data will be stored in a similar structure to the MUF in here
        @param[in/OPT] kwargs - keyword arguments as follows:
            write_nominal - write out our nominal value file in a subfolder of meas_path (default True)
            write_stats - write out our statistics to a subfolder of meas_path (default True)
            verbose - be verbose when writing (default False)
            filetype - 'meas' or 'smeas' (default to os.path.splitext()[-1]) if the file doesnt have one
        '''
        options = {}
        options['filetype'] = os.path.splitext(out_path)[-1]
        options.update(kwargs)
        out_dir = os.path.splitext(out_path)[0]
        if kwargs.get('verbose',False): print("Writing to : {}".format(out_path))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        #default if there is no ending
        if not os.path.splitext(out_path)[-1]: #if theres no extension add one
            out_path+= '.{}'.format(options['filetype'])
        #write out the data first so we update the paths
        self._write_data(out_dir,**options)
        if '.meas' in out_path: #write an xml if we have a .meas file
            return self.write_xml(out_path)
        elif '.smeas' in out_path:
            return self.write_json(out_path) #otherwise write a json file
        else:
            raise Exception('Extension not recognized')
        
#################################################
# Some useful properties
#################################################
    
    #getters for our statistics
    @property
    def nominal(self): return self['nominal']
    @property
    def monte_carlo(self): return self['monte_carlo']
    @property
    def perturbed(self): return self['perturbed']
    #and their setters
    @nominal.setter
    def nominal(self,val): self['nominal'] = val
    @monte_carlo.setter
    def monte_carlo(self,val): self['monte_carlo'] = val
    @perturbed.setter
    def perturbed(self,val): self['perturbed'] = val

        
    @property
    def working_directory(self):
        '''@brief getter for the directory of the *.meas file'''
        return os.path.dirname(self.meas_path)
        
    
###############################################
# Math operations
###############################################
    def data_operation(self,funct,*args):
        '''
        @brief perform an operation on loaded data (e.g. self.nominal[0].data)
        @param[in] funct - function to be performed on self and obj
        @param[in] args - arguments to the function given by funct
        '''
        argsl = list(args)
        for mt in self.meas_types:
            mt_attr = getattr(self,mt) #get the attribute
            if isinstance(args[0],SamuraiMeasurement) or isinstance(args[0],MUFResult):
                argsl[0] = getattr(args[0],mt_attr)
            mt_attr.data_operation(funct,*tuple(argsl))
        return self
    
    def __add__(self,obj): return self.data_operation(operator.add,obj)
    def __sub__(self,obj): return self.data_operation(operator.sub,obj)
    def __mult__(self,obj): return self.data_operation(operator.mult,obj)
    def __truediv__(self,obj): return self.data_operation(operator.truediv,obj)
    
###############################################
# Plotting
###############################################
    
    
#%%    
class SamMeasStatistic(list):
    '''
    @brief a class to generically calculate and hold statistics that the MUF does
         This will calculate and store the following statistics:
             -upper and lower n percent (default 95) confidence interval
             -nominal solution +- standard uncertainty (standard deviation)
             -nominal estimate (for monte carlos, sensitivity will just be nominal)
        Each of these uncertainties will be stored
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief constructor for the class. 
        @param[in/OPT] arg_options - keyword arguemnts as follows
                ci_percentage - confidence interval percentage (default is 95)
        '''
        if len(args)==1: #assume its a list of SamMeasItems
            new_args = ([SamMeasItem(lv) for lv in args[0]],)
        else: new_args = args
        super().__init__(*new_args,**kwargs)
        self.options = {}
        self.options['ci_percentage'] = 95
        for k,v in kwargs.items():
            self.options[k] = v
        #properties
        self.confidence_interval = {}
        self.standard_uncertainty = {}
        
    ###################################################
    ### IO Operations
    ################################################### 
    
    def add_item(self,item):
        '''@brief extend super().add_item to allow adding Touchstone params'''
        if isinstance(item,str): #if its a path then add that
            mi = SamMeasItem({'name':get_name_from_path(item),'file_path':item})
            item = mi
        if isinstance(item,TouchstoneEditor):#then make a MUFItem and set the value as the data
            mi = SamMeasItem({'name':'NA','file_path':'NA'})
            mi.data = item
            item = mi
        super().append(item)
        
    def load_data(self,**kwargs):
        '''@brief load in all of the data from each of the files'''
        options = self.options
        for k,v in kwargs.items():
            options[k] = v
        if options.get('verbose',False): pc = ProgressCounter(len(self))
        for it in self:
            it.load_data(TouchstoneEditor,**options)
            if options.get('verbose',False): pc.update()
        if options.get('verbose',False): pc.finalize()
        
    def write_data(self,format_out_path):
        '''
        @brief write the data to a provided output path with a formattable string for numbering
        @param[in] format_out_path - formattable output path (e.g. path/to/data/monte_carlo_{}.snp/wnp)
        '''
        for i,item in enumerate(self):
            item.write(format_out_path.format(i))
            
    @property
    def data(self):
        '''@brief return list of all loaded data'''
        return [it.data for it in self]
            
    @property
    def filepaths(self):
        '''@brief get all of our file paths'''
        return [mi['file_path'] for mi in self]
    #alias
    file_paths=filepaths
    
    def is_empty(self):
        '''@brief check whether the statistic is empty or not'''
        return bool(self)

    ###################################################
    ### Statistics Operations
    ###################################################        
    def calculate_statistics(self):
        '''
        @brief calculate and store all statistics. If self.data has been loaded use that
            Otherwise load the data
        '''
        if len(self.file_paths) > 2: #make sure we have enough to make a statistic
            if not self.data or self.data[0] is None:
                self.load_data()
            tnp_list = self.data
            data = self.data
            #estimate
            self.estimate = calculate_estimate(data)
            #confidence interval
            ciu,cil = calculate_confidence_interval(data)
            self.confidence_interval['+'] = ciu
            self.confidence_interval['-'] = cil
            #and standard uncertainty
            suu,sul = calculate_standard_uncertainty(data)
            self.standard_uncertainty['+'] = suu
            self.standard_uncertainty['-'] = sul
        
    def get_statistics(self,key):
        '''
        @brief return statistics for a given key value 
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        @return estimate,ci_+,ci_-,std_+,std_- (TouchstoneParams)
        '''
        est = self.estimate.S[key]
        cip = self.confidence_interval['+'].S[key]
        cim = self.confidence_interval['-'].S[key]
        stp = self.standard_uncertainty['+'].S[key]
        stm = self.standard_uncertainty['-'].S[key]
        return est,cip,cim,stp,stm
    
    def get_statistics_dict(self,key):
        '''
        @brief return statistics for a given key in a dictionary format
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        @return dictionary with descriptive keys matched to the values
        '''
        est,cip,cim,stp,stm = self.get_statistics(key)
        rd = {'estimate':est}
        rd.update({'+ {} conf. int.'.format(self.options['ci_percentage']):cip})
        rd.update({'- {} conf. int.'.format(self.options['ci_percentage']):cim})
        rd.update({'+ std. uncert.':stp,'- std. uncert.':stm})
        return rd
    
    def get_statistics_from_frequency(self,key,freq):
        '''
        @brief return statistics for a given key at a given frequency (hz)
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        @param[in] freq - frequency (in Hz) to get the values at
        '''
        est = self.estimate.S[key].get_value_from_frequency(freq)
        cip = self.confidence_interval['+'].S[key].get_value_from_frequency(freq)
        cim = self.confidence_interval['-'].S[key].get_value_from_frequency(freq)
        stp = self.standard_uncertainty['+'].S[key].get_value_from_frequency(freq)
        stm = self.standard_uncertainty['-'].S[key].get_value_from_frequency(freq)
        return est,cip,cim,stp,stm        
            
    @property
    def freq_list(self):
        '''@brief get the frequency list from the first value'''
        return self[0].data.freq_list
    
    @property
    def file_paths(self):
        '''@brief get a list of the file paths'''
        return [item['file_path'] for item in self]
    filepaths = file_paths #alias
    
###############################################
# Function for math operations
###############################################
    
    def data_operation(self,funct,*args):
        '''
        @brief perform an operation on loaded data
        @param[in] funct - function to be performed. if its a string, assume its a method of self[i].data
        @param[in] args - arguments to the function
        '''
        argsl = list(args)
        for i,attr_val in enumerate(self):
            if isinstance(args[0],list):
                argsl[0] = args[0][i].data # assume its a SamMeasStatistic (or MUFStatistic)
            if argsl[0] is not None and attr_val is not None: #only if loaded
                if isinstance(funct,str):
                    getattr(self[i].data,funct)(*tuple(argsl))
                else:
                    self[i].data = funct(attr_val.data,obj_val)
        return self
    
#%%  
class SamMeasItem(SamuraiDict):
    '''
    @brief Class to hold info on an item in a samurai Measurement
        The point of this is to allow loading of data without being in the json file.
        It also adds some other extensions
    '''
    def __init__(self,*args,**kwargs):
        '''@brief Constructor definition. Same as for a dictionary'''
        super().__init__(*args,**kwargs)
        self.data = None #start with no data
        
    def load_data(self,load_funct,**kwargs):
        '''
        @brief load the data from the path subitem to self.data
        @param[in] load_funct - function to load the data given a file path (can also be a class constructor)
        @param[in] subitem_idx - which index the path is to load (typically its self[0])
        @param[in] kwargs - keyword arguements as follows
            - working_directory - root point for relative paths. Typically should be the menu file directory
            - | - The rest of the results will be passed to load_funct
        '''
        options = {}
        options['working_directory'] = ''
        for k,v in kwargs.items():
            options[k] = v
        fpath = self.get_filepath(working_directory=options['working_directory'])
        self.data = load_funct(fpath,**kwargs)
        
    def write(self,*args,**kwargs):
        '''@brief Call self.data.write(*args,**kwargs)'''
        self.data.write(*args,**kwargs)
        
    def get_filepath(self,**kwargs):
        '''
        @brief getter for filepath
        @param[in/OPT] kwargs - keyword arguements as follows:
            - working_directory - working directory for relative paths (default '')
        '''
        options = {}
        options['working_directory'] = ''
        for k,v in kwargs.items():
            options[k] = v
        return os.path.join(options['working_directory'],self['file_path'])
        
    def __getattr__(self,attr):
        '''@brief try the dict and data if the attribute doesnt exist'''
        try:
            return self[attr]
        except KeyError:
            return getattr(self.data,attr)

#%% Unittest class
import unittest
class TestSamuraiMeasurement(unittest.TestCase):
    
    wdir = os.path.dirname(__file__)
    unittest_dir = os.path.join(wdir,'./unittest_data')
    
    def test_load_xml(self):
        '''
        @brief in this test we will load a xml file with uncertainties and try
            to access the path lists of each of the uncertainty lists and the nominal result
        '''
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=False,load_statistics=False)
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=False)
        res = SamuraiMeasurement(meas_path,load_nominal=False,load_statistics=True)
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
        
    def test_create_from_snp(self):
        '''
        @brief this test will create a *.meas file for a given *.snp or *.wnp file
        '''
        snp_path = os.path.join(self.unittest_dir,'meas_test/nominal.s2p_binary')
        res = SamuraiMeasurement(snp_path)
        nvp = res.nominal_value_path #try getting our nominal value
        self.assertEqual(nvp,snp_path)
        
    def test_create_from_empty(self):
        '''
        @brief in this test we create an empty .meas file and add our paths to it
            which is then written out
        '''
        snp_path = os.path.join(self.unittest_dir,'meas_test/nominal.s2p_binary')
        res = SamuraiMeasurement()
        res.nominal.add_item(snp_path)
    
    def test_create_from_data(self):
        '''
        @brief here we will create a MUFResult just given data in TouchstoneEditor format
            This should build a template around data itself and will write out data
            using name in one of the write data methods
        '''
        res = SamuraiMeasurement()
        res.nominal.add_item(SnpEditor(os.path.join(self.unittest_dir,'meas_test/nominal.s2p_binary')))
        res.nominal.add_item(SnpEditor(os.path.join(self.unittest_dir,'meas_test/nominal_post.s2p_binary')))
        res.monte_carlo.add_item(SnpEditor(os.path.join(self.unittest_dir,'meas_test/MonteCarlo/mc_0.s2p_binary')))
        #make sure the data exists
        self.assertIsNotNone(res.nominal[0])
        self.assertIsNotNone(res.nominal[1])
        self.assertIsNotNone(res.monte_carlo[0].data)
        
    def test_calculate_statistics(self):
        '''
        @brief in this test we will load a xml file with uncertainties and try
            to access the path lists of each of the uncertainty lists and the nominal result
        '''
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
        res.calculate_statistics()
        
    def test_load_write_absolute(self):
        '''
        @brief in this test we will load a xml file with uncertainties and try
            to access the path lists of each of the uncertainty lists and the nominal result
        '''
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=False)
        res.write_json(os.path.join(self.wdir,'./test/test_meas.smeas'))
        res.write_xml(os.path.join(self.wdir,'./test/test_meas.meas'))
        #absolute read write test
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
        res.write(os.path.join(self.wdir,'./test/test_meas_all.smeas'),relative=False)
        res.write(os.path.join(self.wdir,'./test/test_meas_all.meas'),relative=False)
        resj = SamuraiMeasurement(os.path.join(self.wdir,'./test/test_meas_all.smeas'),load_nominal=True,load_statistics=True)
        resx = SamuraiMeasurement(os.path.join(self.wdir,'./test/test_meas_all.meas'),load_nominal=True,load_statistics=True)
        
    def test_load_write_relative(self):
        '''
        @brief in this test we will load a xml file with uncertainties and try
            to access the path lists of each of the uncertainty lists and the nominal result
        '''
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=False,load_statistics=False)
        res.write_json(os.path.join(self.wdir,'./test/test_meas.smeas'))
        res.write_xml(os.path.join(self.wdir,'./test/test_meas.meas'))
        #absolute read write test
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=True,load_statistics=True)
        res.write(os.path.join(self.wdir,'./test/test_meas_all_rel.smeas'),relative=True)
        res.write(os.path.join(self.wdir,'./test/test_meas_all_rel.meas'),relative=True)
        resj = SamuraiMeasurement(os.path.join(self.wdir,'./test/test_meas_all_rel.smeas'),load_nominal=True,load_statistics=True)
        resx = SamuraiMeasurement(os.path.join(self.wdir,'./test/test_meas_all_rel.meas'),load_nominal=True,load_statistics=True)
        
    def test_split_combine(self):
        '''
        @brief test splitting and combining the data of the measurement (e.g. s2p to s1p)
        '''
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        meas = SamuraiMeasurement(meas_path,load_statistics=True)
        meas_p1,meas_p2 = split_measurement(meas_path,2)
        #now lets verify the data is correct
        sn1,sn2 = split_parameters(meas.nominal[0].data,2) 
        self.assertEqual(sn1,meas_p1.nominal[0].data)
        self.assertEqual(sn2,meas_p2.nominal[0].data)
        sm1,sm2 = split_parameters(meas.monte_carlo[0].data,2) 
        self.assertEqual(sm1,meas_p1.monte_carlo[0].data)
        self.assertEqual(sm2,meas_p2.monte_carlo[0].data)
        #test combine
        meas_comb = combine_measurements(meas_p1,meas_p2)
        self.assertTrue(np.all(meas.nominal[0].data.S[11]==sn1.S[11]))
        self.assertTrue(np.all(meas.nominal[0].data.S[22]==sn2.S[11]))
        
class TestUncertaintyOperations(unittest.TestCase):
    '''@brief test operations on data with uncertainty'''
    
    wdir = os.path.dirname(__file__)
    unittest_dir = os.path.join(wdir,'./unittest_data')
    
    def test_calculate_time_domain(self):
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
        td_res = calculate_time_domain(res)

#%%
if __name__=='__main__':
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSamuraiMeasurement)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUncertaintyOperations)
    #unittest.TextTestRunner(verbosity=2).run(suite)
        
    wdir = os.path.dirname(__file__)
    unittest_dir = os.path.join(wdir,'./unittest_data')
    meas_path = os.path.join(unittest_dir,'meas_test.meas')
    res = SamuraiMeasurement(meas_path,load_nominal=False,load_statistics=False)
    resd = SamuraiMeasurement(meas_path,load_nominal=True,load_statistics=True)
    
    mymeas = SamuraiMeasurement(r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\2019\7-8-2019_uncert\aperture_vertical\meas(1224)_cal_template_100mc.meas",load_statistics=True,verbose=True)
    td = calculate_time_domain(mymeas)
    td.calculate_statistics()
    td_nom = td.nominal.data 
    td_mc_stats = td.monte_carlo.get_statistics_dict(21);
    
    
