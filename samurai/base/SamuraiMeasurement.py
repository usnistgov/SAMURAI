# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5, bfj
"""

from samurai.base.TouchstoneEditor import TouchstoneEditor,TouchstoneError, SnpEditor,WaveformEditor
from samurai.base.TouchstoneEditor import TouchstoneParam
from samurai.base.generic import complex2magphase, magphase2complex
from samurai.base.generic import get_name_from_path
from samurai.base.generic import ProgressCounter
from samurai.base.SamuraiDict import SamuraiDict

import shutil
import getpass
import datetime

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
        mt_attr = getattr(sam_meas,meas_type) #get the measurements
        mr_mt_attr = getattr(rv,meas_type)
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
    for mt in mr_obj.meas_types: #go through each meas type
        mt_attr = getattr(mr_obj,meas_type) #get the measurements
        sm_mt_attr = getattr(sm,meas_type)
        for i,item in enumerate(mt_attr): #now copy the data
            sm_mt_attr.add_item(item['file_path'])
            sm_mt_attr[i].data = item.data #copy the data 
    return mr

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
            rel_paths = [os.path.join('./',new_rel_dir,os.path.basename(p)) for p in fpaths]
            meas_obj.add_items(rel_paths) #add the filepaths back
    return meas.write_xml(out_path)
    
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
            td_vals = item.w1[key].calculate_time_domain_data(window=window)
            tdw_vals = WaveformEditor(*td_vals)
            out_meas.add_item(tdw_vals)
            if verbose and len(in_meas)>1: pc.update()
        if verbose and len(in_meas)>1: pc.finalize()
    return td_w_uncert

#%% Class for MUF Interoperability

class SamuraiMeasurement(SamuraiDict):
    '''
    @brief A class to deal with measurements with uncertianties. This is written to be capable 
        of interfacing with data from the MUF. should be drop in replacement for MUFResult class. 
        But more clear and better
    @example
        >>> meas_path = './test.meas' #path to *.meas file
        >>> mymeas = MUFResult(meas_path) #initialize the class
        >>> mymeas.calculate_monte_carlo_statistics() 
    '''
        
    def __init__(self,meas_path=None,**arg_options):
        '''
        @brief load up and initialize the *.meas file
        @param[in] meas_path - path to the *.meas file to load. 
            This can be passed as None if self.create_meas() is going to be run.
            if a *.snp or *.wnp file are provided, it will be loaded and a *.meas 
            file will be created with the loaded measurement as the nominal result
        @param[in/OPT] arg_options - keyword arguments as follows:
            - - all arguments passed to MUFResult.load() method
            - - all arguments also passed to MUFModuleController constructor
        '''
        super().__init__(**arg_options)
        #uncertainty statistics
        self.monte_carlo = None
        self.perturbed = None
        self.nominal = None
        #options
        self.options = {}
        self.options['ci_percentage'] = 95
        self.meas_types = None
        for k,v in arg_options.items():
            self.options[k] = v
        #now load
        if meas_path is not None: #load the data
            self.load(meas_path,**arg_options) #pass our kwargs here to for loading if desired
        else:
            self.create_meas() #create the skeleton
      
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
        return self.nominal_post[0].file_path
    
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
        self.meas_types = ['nominal','nominal_post','monte_carlo','perturbed'] #default measurement types
        self['file_path']= './'
        self['user_name'] = getpass.getuser()
        self['creation_time'] = str(datetime.datetime.now())
        #now create our nominal
        self['nominal_measurements'] = SamMeasNominalValue(**self.options) #aliased to self.nominal
        #now create our nominal for post cal
        self['nominal_post_measurements'] = SamMeasNominalValue(**self.options) #aliased to self.nominal_post
        #and monte carlo
        self['monte_carlo_measurements'] = SamMeasStatistic(**self.options) #aliased to self.monte_carlo
        #and perturbed
        self['perturbed_measurements'] = SamMeasStatistic(**self.options) #aliased to self.perturbed
    
    ##########################################################################
    ### extra io functions
    ##########################################################################
    
    def _load_nominal(self,verbose=False):
        '''@brief load the nominal path value into self.nominal'''
        if verbose: print("Loading Nominal")
        self.nominal.load_data(working_directory=self.working_directory,verbose=False)
        
    def _load_nominal_post(self,verbose=False):
        '''@brief load the nominal (post-calibrated) path value into self.nominal_post'''
        if verbose: print("Loading Nominal Post")
        self.nominal_post.load_data(working_directory=self.working_directory,verbose=False)
        
    def _load_statistics(self,verbose=False):
        '''@brief load in all of the data for all of our statistics'''
        if verbose: print("Loading Monte Carlo:")
        self.monte_carlo.load_data(working_directory=self.working_directory,verbose=verbose)
        if verbose: print("Loading Perturbed:")
        self.perturbed.load_data(working_directory=self.working_directory,verbose=verbose)
    
    def _load_xml(self,meas_path):
        '''@brief Load an xml *.meas file'''
        mr = MUFResult(meas_path,load_nominal=False,load_nominal_post=False,load_statistics=False)
        self.update(MUFResult2SamuraiMeasurement(mr))
        
    def load(self,meas_path,**kwargs):
        '''
        @brief load our meas file and its corresponding data
        @param[in/OPT] meas_path - path to *.meas file to load in. This will overwrite self.meas_path
        @param[in/OPT] kwargs - keyword arguments as follows:
            load_nominal - load our data from the pre-calibrated nominal solution (default True)
            load_nominal_post - load data from the post-calibrated nominal solution (default True)
            load_statistics - load our statistics (monte carlo and perturbed) (default False)
            verbose - be verbose when loading data (default False)
        '''
        options = {}
        options['load_nominal'] = True
        options['load_nominal_post'] = False
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
            super().load(meas_path)
        else: #if its not a meas file (e.g. touchstone) then create
            self.create_meas()
            self.nominal.add_item(meas_path)

        #load our nominal and statistics if specified
        if options['load_nominal']:
            self._load_nominal(verbose=options['verbose'])
        if options['load_nominal_post']:
            self._load_nominal_post(verbose=options['verbose'])
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
            option[k] = v
        mr = SamuraiMeasurement2MUFResult(self)
        out_path = os.path.splitext(out_path)[0]+'.meas'
        mr.write(out_path,**kwargs)
        
    def write_json(self,out_path,**kwargs):
        '''
        @brief write our current data to a json file (should be a *.smeas file)
        '''
        options = {}
        options['relative'] = False
        for k,v in kwargs.items():
            option[k] = v
        out_path = os.path.splitext(out_path)[0]+'.smeas'
        super().write(out_path)
        
    def _write_nominal(self,out_dir,out_name='nominal'):
        '''
        @brief write out our nominal data
        @param[in] out_dir - directory to write out to
        @param[in/OPT] out_name - name to write out (default 'nominal')
        '''
        self._write_statistic(self.nominal, os.path.join(out_dir,'{}'.format(out_name)))
            
    def _write_nominal_post(self,out_dir,out_name='nominal_post'):
        '''
        @brief write out our nominal data
        @param[in] out_dir - directory to write out to
        @param[in/OPT] out_name - name to write out (default 'nominal')
        '''
        self._write_statistic(self.nominal_post, os.path.join(out_dir,'{}'.format(out_name)))
        
    def _write_statistic(self,stat_class,format_out_path):
        '''
        @brief write out our statistics data
        @param[in] stat_class - instance of MUFStatistic to write
        @param[in] out_dir - directory to write out to
        @param[in] format_out_path - formattable output path (e.g. path/to/dir/mc_{}.snp)
        @return list of written file paths (absolute paths)
        '''
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
                fname_out = dat.write(fname,ftype='binary')
                fname_out = os.path.abspath(fname_out)
                out_list.append(fname_out)
                
        for i,path in enumerate(out_list):
            stat_class[i]['name'] = get_name_from_path(path)
            stat_class[i]['file_path'] = path
            
        return out_list
    
    def _write_statistics(self,out_dir):
        '''@brief write out monte carlo and perturbed data'''
        #make the directories
        mc_dir = os.path.join(out_dir,'MonteCarlo')
        if not os.path.exists(mc_dir):
            os.makedirs(mc_dir)
        pt_dir = os.path.join(out_dir,'Perturbed')
        if not os.path.exists(pt_dir):
            os.makedirs(pt_dir)
        #write the data
        self._write_statistic(self.monte_carlo, os.path.join(mc_dir,'mc_{}'))
        self._write_statistic(self.perturbed, os.path.join(pt_dir,'pt_{}'))
        
    def _write_data(self,out_dir,**kwargs):
        '''
        @brief write out supporting data for the *.meas file (e.g. nominal/monte_carlo/perturbed *.snp files)
        @param[in] out_dir - what directory to write the data out to
        @param[in/OPT] kwargs - keyword arguments as follows:
            write_nominal - write out our nominal value file in a subfolder of meas_path (default True)
            write_nominal_post - write out nominal from post-calibration (default True)
            write_stats - write out our statistics to a subfolder of meas_path (default True)
        @note if the data is not loaded in we will simply copy the files
        '''
        options = {}
        options['write_nominal'] = True
        options['write_nominal_post'] = True
        options['write_stats'] = True
        for k,v in kwargs.items():
            options[k] = v
        #load our nominal and statistics if specified
        if options['write_nominal']:
            self._write_nominal(out_dir)
        if options['write_nominal_post']:
            self._write_nominal_post(out_dir)
        if options['write_stats']:
            self._write_statistics(out_dir)
        
    def write(self,out_path,**kwargs):
        '''
        @brief write out all information on the MUF Statistic. This will create a copy
            of the nominal value and all statistics snp/wnp files
        @param[in] out_path - path to write xml file to. 
            all other data will be stored in a similar structure to the MUF in here
        @param[in/OPT] kwargs - keyword arguments as follows:
            write_nominal - write out our nominal value file in a subfolder of meas_path (default True)
            write_nominal_post - write out nominal from post-calibration (default True)
            write_stats - write out our statistics to a subfolder of meas_path (default True)
            verbose - be verbose when writing (default False)
        '''
        out_dir = os.path.splitext(out_path)[0]
        if kwargs.get('verbose',False): print("Writing to : {}".format(out_path))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        #write out the data first so we update the paths
        self._write_data(out_dir,**kwargs)
        self.write_xml(out_path)
        
    

        
    @property
    def working_directory(self):
        '''@brief getter for the directory of the *.meas file'''
        return os.path.dirname(self.meas_path)
        
    
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
    def __init__(self,**arg_options):
        '''
        @brief constructor for the class. 
        @param[in/OPT] arg_options - keyword arguemnts as follows
                ci_percentage - confidence interval percentage (default is 95)
        '''
        super().__init__()
        self.options = {}
        self.options['ci_percentage'] = 95
        for k,v in arg_options.items():
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
            mi = {'name':get_name_from_path(item),'path':item}
            item = mi
        if isinstance(item,TouchstoneEditor):#then make a MUFItem and set the value as the data
            mi = MUFItem(['name','path'])
            mi.data = item
            item = mi
        super().append(item)
        
    def load_data(self,**kwargs):
        '''@brief load in all of the data from each of the files'''
        options = self.options
        for k,v in kwargs.items():
            options[k] = v
        if options.get('verbose',False): pc = ProgressCounter(len(self.muf_items))
        for it in self.muf_items:
            it.load_data(TouchstoneEditor,**options)
            if options.get('verbose',False): pc.update()
        if options.get('verbose',False): pc.finalize()
    
    def _extract_data_dict(self,tnp_list):
        '''
        @brief extract data from our snp_list into a dictionary with snp_list[0].wave_dict_key keys
                and values of (n,m) 2D numpy arrays where n is len(snp_list) and m is len(snp_list[0].freq_list)
        @return a dictionary as described in the brief
        '''
        data_dict = {}
        data_dict['freq_list'] = tnp_list[0].freq_list
        data_dict['editor_type'] = type(tnp_list[0]) #assume all of same type
        data_dict['first_key'] = tnp_list[0].wave_dict_keys[0]
        for k in tnp_list[0].wave_dict_keys:
            data_dict[k] = np.array([tnp.S[k].raw for tnp in tnp_list])
        return data_dict
        
    def write_data(self,format_out_path):
        '''
        @brief write the data to a provided output path with a formattable string for numbering
        @param[in] format_out_path - formattable output path (e.g. path/to/data/monte_carlo_{}.snp/wnp)
        '''
        for i,item in enumerate(self.muf_items):
            item.write(format_out_path.format(i))
            
    @property
    def data(self):
        '''@brief return list of all loaded data'''
        return [it.data for it in self.muf_items]
            
    @property
    def filepaths(self):
        '''@brief get all of our file paths'''
        return [mi[1] for mi in self.muf_items]
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
            data_dict = self._extract_data_dict(tnp_list)
            #estimate
            self.estimate = self._calculate_estimate(data_dict)
            #confidence interval
            ciu,cil = self._calculate_confidence_interval(data_dict)
            self.confidence_interval['+'] = ciu
            self.confidence_interval['-'] = cil
            #and standard uncertainty
            suu,sul = self._calculate_standard_uncertainty(data_dict)
            self.standard_uncertainty['+'] = suu
            self.standard_uncertainty['-'] = sul
        
    def get_statistics(self,key):
        '''
        @brief return statistics for a given key value 
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        @return aestimate,ci_+,ci_-,std_+,std_- (WnpParams)
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
    
    def _calculate_estimate(self,data_dict):
        '''
        @brief calculate the estimate from the input values (mean of the values)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @param[in/OPT] editor_type
        @return WnpEditor object with the estimate (mean) of the stats_path values
        '''
        #create a blank snp file to fill
        num_ports = round(np.sqrt(len(data_dict)-1)) #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        MyEditor = data_dict['editor_type'] #get the type of editor
        tnp_out = MyEditor([num_ports,freq_list],plotter=self.options['plotter'])
        for k in tnp_out.wave_dict_keys:
            data = data_dict[k] #get the data
            m,p = self._complex2magphase(data)
            m_mean = m.mean(0); p_mean = p.mean(0)
            data_mean = self._magphase2complex(m_mean,p_mean)
            tnp_out.S[k].update(freq_list,data_mean)
        return tnp_out
            
    def _calculate_confidence_interval(self,data_dict):
        '''
        @brief calculate the n% confidence interval where n is self.options['ci_percentage']
            this will calculate both the upper and lower intervals
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor objects for upper(+),lower(-) intervals
        '''
        #create a blank snp file to fill
        num_ports = round(np.sqrt(len(data_dict)-1)) #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        MyEditor = data_dict['editor_type']
        tnp_out_p = MyEditor([num_ports,freq_list],plotter=self.options['plotter'])
        tnp_out_m = MyEditor([num_ports,freq_list],plotter=self.options['plotter'])
        #find percentage and index like in the MUF
        percentage = 0.5*(1-self.options['ci_percentage']/100)
        lo_index = int(percentage*data_dict[data_dict['first_key']].shape[0])
        if lo_index<=0: lo_index=1
        hi_index = data_dict[data_dict['first_key']].shape[0]-lo_index
        for k in tnp_out_p.wave_dict_keys:
            data = data_dict[k] #get the data
            #done in the same way as the MUF
            m,p = self._complex2magphase(data)
            m.sort(0); p.sort(0)
            m_hi = m[hi_index,:]; m_lo = m[lo_index]
            p_hi = p[hi_index,:]; p_lo = p[lo_index]
            hi_complex = self._magphase2complex(m_hi,p_hi)
            lo_complex = self._magphase2complex(m_lo,p_lo)
            tnp_out_p.S[k].update(freq_list,hi_complex)
            tnp_out_m.S[k].update(freq_list,lo_complex)
        return tnp_out_p,tnp_out_m
    
    def _calculate_standard_uncertainty(self,data_dict):
        '''
        @brief calculate standard uncertainty (standard deviation)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor objects for upper(+),lower(-) uncerts
        '''
        #create a blank snp file to fill
        num_ports = round(np.sqrt(len(data_dict)-1)) #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        MyEditor = data_dict['editor_type']
        tnp_out_p = MyEditor([num_ports,freq_list],plotter=self.options['plotter'])
        tnp_out_m = MyEditor([num_ports,freq_list],plotter=self.options['plotter'])
        for k in tnp_out_p.wave_dict_keys:
            data = data_dict[k] #get the data
            m,p = self._complex2magphase(data)
            m_mean = m.mean(0); p_mean = p.mean(0)
            m_std  = m.std(0) ; p_std  = p.std(0) #mean and stdev of mag/phase
            m_plus = m_mean+m_std; m_minus = m_mean-m_std
            p_plus = p_mean+p_std; p_minus = p_mean-p_std
            data_plus   = self._magphase2complex(m_plus ,p_plus )
            data_minus  = self._magphase2complex(m_minus,p_minus)
            tnp_out_p.S[k].update(freq_list,data_plus)
            tnp_out_m.S[k].update(freq_list,data_minus)
        return tnp_out_p,tnp_out_m
    
    def _complex2magphase(self,data):
        return complex2magphase(data)
    
    def _magphase2complex(self,mag,phase):
        return magphase2complex(mag,phase)
            
    @property
    def freq_list(self):
        '''@brief get the frequency list from the first value'''
        return self[0].data.freq_list
    
#%%  
class SamMeasItem(SamuraiDict):
    '''
    @brief Class to hold info on an item in a samurai Measurement
        The point of this is to allow loading of data without being in the json file.
        It also adds some other extensions
    '''
    def __init__(*args,**kwargs):
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
            - - The rest of the results will be passed to load_funct
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
        '''@brief try the dict if the attribute doesnt exist'''
        return self[attr]

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
        res = SamuraiMeasurement(meas_path,load_nominal=False,load_nominal_post=False,load_statistics=False)
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=False,load_statistics=False)
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=True,load_statistics=False)
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=True,load_statistics=True)
        
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
        res.nominal_post.add_item(SnpEditor(os.path.join(self.unittest_dir,'meas_test/nominal_post.s2p_binary')))
        res.monte_carlo.add_item(SnpEditor(os.path.join(self.unittest_dir,'meas_test/MonteCarlo/mc_0.s2p_binary')))
        #make sure the data exists
        self.assertIsNotNone(res.nominal.data)
        self.assertIsNotNone(res.nominal_post.data)
        self.assertIsNotNone(res.monte_carlo[0].data)
        
class TestUncertaintyOperations(unittest.TestCase):
    '''@brief test operations on data with uncertainty'''
    
    wdir = os.path.dirname(__file__)
    unittest_dir = os.path.join(wdir,'../unittest_data')
    
    def test_calculate_time_domain(self):
        meas_path = os.path.join(self.unittest_dir,'meas_test.meas')
        res = SamuraiMeasurement(meas_path,load_nominal=True,load_nominal_post=True,load_statistics=True)
        td_res = calculate_time_domain(res)

#%%
if __name__=='__main__':
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSamuraiMeasurement)
    unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUncertaintyOperations)
    unittest.TextTestRunner(verbosity=2).run(suite)
        
    wdir = os.path.dirname(__file__)
    unittest_dir = os.path.join(wdir,'../unittest_data')
    meas_path = os.path.join(unittest_dir,'meas_test.meas')
    res = SamuraiMeasurement(meas_path,load_nominal=False,load_nominal_post=False,load_statistics=False)
    
    
    
    
