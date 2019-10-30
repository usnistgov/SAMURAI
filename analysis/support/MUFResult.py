# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.base.TouchstoneEditor import TouchstoneEditor,TouchstoneError, SnpEditor
from samurai.base.TouchstoneEditor import TouchstoneParam
from samurai.analysis.support.MUF.MUFModuleController import MUFModuleController, MUFItemList, MUFItem
from samurai.base.SamuraiPlotter import SamuraiPlotter

import shutil

#from xml.dom.minidom import parse, parseString
import numpy as np
#import xml.etree.ElementTree as ET
from lxml import etree as ET
import os
import re

class MUFResult(MUFModuleController):
    '''
    @brief a class to deal with MUF results (and easily get uncertainties, monte_carlos, and whatnot)
        self is the nominal value. Other values will be contained to generate uncerts
    @TODO add serial reading implementation for quick grabbing of path lists for large files
    
    Example
    -------
        >>> meas_path = './test.meas' #path to *.meas file
        >>> mymeas = MUFResult(meas_path) #initialize the class
        >>> mymeas.calculate_monte_carlo_statistics() 
    '''
        
    def __init__(self,meas_path,**arg_options):
        '''
        @brief load up and initialize the *.meas file
        @param[in] meas_path - path to the *.meas file to load. 
            This can be passed as None if self.create_meas() is going to be run.
            if a *.snp or *.wnp file are provided, it will be loaded and a *.meas 
            file will be created with the loaded measurement as the nominal result
        @param[in/OPT] arg_options - keyword arguments as follows:
            None yet!
            all arguments also passed to MUFModuleController constructor
        '''
        super().__init__(None,except_no_menu=False,**arg_options)
        #uncertainty statistics
        self.monte_carlo = None
        self.perturbed = None
        self.nominal = None
        self.options['ci_percentage'] = 95
        self.options['plotter'] = None
        self.options['plot_options'] = {'plot_program':'matplotlib'}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
        #make sure were getting a .meas, if not get the correct data
        menu_path = meas_path

        self.load(menu_path,**arg_options)
      
    ##########################################################################
    ### XML and other properties for easy access
    ##########################################################################
    @property
    def nominal_value_path(self):
        '''@brief property to return the path of the nominal value'''
        return self._xml_nominal[0][1].attrib['Text'] if self.nominal.count else None
    
    @property
    def _xml_nominal(self):
        '''@brief link to nominal xml path value'''
        return self.controls.find('MeasSParams')
    
    @property
    def _xml_monte_carlo(self):
        '''@brief link to monte_carlo xml path value'''
        return self.controls.find('MonteCarloPerturbedSParams')
    
    @property
    def _xml_perturbed(self):
        '''@brief link to monte_carlo xml path value'''
        return self.controls.find('PerturbedSParams')
    
    @property
    def plotter(self):
        '''@brief alias for getting plotter'''
        return self.options['plotter']
    
    @plotter.setter
    def plotter(self,val):
        self.options['plotter'] = val
    
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
        '''
        @brief calculate statistics for monte carlo and perturbed data
        '''
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
        '''
        @brief create a *.meas file xml setup. This will be an empty measurement
        '''
        self._create_meas() #create the skeleton        
        
    def _create_meas(self):
        import getpass
        import datetime
        '''
        @brief create a skeleton (main nodes) for a *.meas file
        This includes everything except the menustripheader
        '''
        #root node
        root_elem = ET.Element('CorrectedMeasurement')
        root_elem.set('FileName','./')
        root_elem.set('UserName',getpass.getuser())
        root_elem.set('CreationTime',str(datetime.datetime.now()))
        self._setroot(root_elem)
        #create controls element
        self._controls = ET.SubElement(self.getroot(),'Controls')  
        #now create our nominal
        ET.SubElement(self._controls,'MeasSParams')
        self._xml_nominal.set('ControlType',"CustomFormControls.FLV_FixedDetailsList")
        self._xml_nominal.set('FullName',"Me_SplitContainer2__GroupBox2_Panel3_MeasSParams")
        self._xml_nominal.set('Count',str(0))
        self.nominal = MUFNominalValue(self._xml_nominal,**self.options)
        #and monte carlo
        ET.SubElement(self._controls,'MonteCarloPerturbedSParams')
        self._xml_monte_carlo.set('ControlType',"CustomFormControls.FLV_VariableDetailsList")
        self._xml_monte_carlo.set('FullName',"Me_SplitContainer2__GroupBox3_Panel2_MonteCarloPerturbedSParams")
        self._xml_monte_carlo.set('Count',str(0))
        self.monte_carlo = MUFStatistic(self._xml_monte_carlo,**self.options)
        #and monte carlo
        ET.SubElement(self._controls,'PerturbedSParams')
        self._xml_perturbed.set('ControlType',"CustomFormControls.FLV_VariableDetailsListMeas")
        self._xml_perturbed.set('FullName',"Me_SplitContainer2__GroupBox1_Panel1_PerturbedSParams")
        self._xml_perturbed.set('Count',str(0))
        self.monte_carlo = MUFStatistic(self._xml_perturbed,**self.options)
        
    def set_nominal_path(self,nom_path):
        '''
        @brief add a nominal path to the xml *.meas file
        @param[in] nom_path - nominal path
        '''
        self.nominal[0][0] = get_name_from_path(nom_path)
        self.nominal[0][1] = nom_path
        
    def set_monte_carlo_paths(self,mc_path_list):
        '''
        @brief overwrite our monte carlo paths
        '''
        if len(mc_path_list) != len(self.monte_carlo.muf_items):
            raise Exception("Input List must match the length of the number of items")
        for i,item in enumerate(self.monte_carlo.muf_items):
            cur_path = mc_path_list[i]
            item[0] = get_name_from_path(cur_path)
            item[1] = cur_path
            
    def get_monte_carlo_paths(self):
        '''
        @brief get a list of our monte carlo paths
        '''
        path_list = []
        for i,item in enumerate(self.monte_carlo.muf_items):
            path_list.append(item[1])
        
    def set_perturbed_paths(self,pt_path_list):
        '''
        @brief overwrite perturbed paths
        '''
        if len(pt_path_list) != len(self.perturbed.muf_items):
            raise Exception("Input List must match the length of the number of items")
        for i,item in enumerate(self.perturbed.muf_items):
            cur_path = pt_path_list[i]
            item[0] = get_name_from_path(cur_path)
            item[1] = cur_path
      
    def add_meas_item_list(self,item_list,path_list):
        '''
        @brief add a measurement list from items and place it in a parent element (e.g self._xml_monte_carlo)
        '''
        for i,path in enumerate(path_list):
            name = get_name_from_path(path)
            item_list.add_item([name,path]) #add the item to the MUFItemList
        
    ##########################################################################
    ### extra io functions
    ##########################################################################
    def plot(self,key,stat_list=[]):
        '''
        @brief plot data given a specific key for the Touchstone Data
        @param[in] key - key (e.g. 21) of the Touchstone data to plot
        @param[in] stat_list - name of statistics to plot (e.g. 'monte_carlo','perturbed')
        '''
        fig = self.plotter.figure()
        for stat_str in stat_list:
            stat = getattr(self,stat_str) #get the statistic object
            stat.plot(key)
        self.nominal.plot(key)
        self.plotter.legend()
        return fig
    
    def _load_nominal(self):
        '''
        @brief load the nominal path value into self.nominal
        '''
        self.nominal.load_data()
        
    def _load_statistics(self):
        '''
        @brief load in all of the data for all of our statistics
        '''
        self.monte_carlo.load_data()
        self.perturbed.load_data()
    
    def _load_xml(self,meas_path):
        '''
        @brief  parse our file into a dom struct
        @param[in] meas_path - path to *.meas file
        @note this also loads self.nominal,self.monte_carlo,
            and self.perturbed
        '''
        super().load(meas_path)  #load xml
        self.nominal = MUFNominalValue(self._xml_nominal,**self.options) # parse nominal
        self.monte_carlo = MUFStatistic(self._xml_monte_carlo,**self.options) #parse mc
        self.perturbed = MUFStatistic(self._xml_perturbed,**self.options) #parse perturbed
        
    def load(self,meas_path,**kwargs):
        '''
        @brief load our meas file and its corresponding data
        @param[in] meas_path - path to *.meas file to load in
        @param[in/OPT] kwargs - keyword arguments as follows:
            load_nominal - load our nominal value file in a subfolder of meas_path (default True)
            load_stats - load our statistics to a subfolder of meas_path (default False)
        '''
        options = {}
        options['load_nominal'] = True
        options['load_stats'] = False
        for k,v in kwargs.items():
            options[k] = v
        #make a *.meas if a wnp or snp file was provided
        if meas_path is not None:
            _,ext = os.path.splitext(meas_path) #get our extension
            if '.meas' not in ext: #if its not a *.meas create our skeleton
                self._create_meas()
                self.set_nominal_path(meas_path)
            else:
                self._load_xml(meas_path)
        else:
            self.create_meas()
        #load our nominal and statistics if specified
        if options['load_nominal']:
            self._load_nominal()
        if options['load_stats']:
            self._load_statistics()
            
    def write_xml(self,out_path):
        '''
        @brief write out our current xml file and corresponding measurements
        @param[in] out_path - path to writ ethe file out to 
        '''
        super().write(out_path)
        
    def _write_nominal(self,out_dir,out_name='nominal'):
        '''
        @brief write out our nominal data
        @param[in] out_dir - directory to write out to
        @param[in/OPT] out_name - name to write out (default 'nominal')
        '''
        out_file = os.path.join(out_dir,out_name)
        if self.nominal[0].data is None: #then copy the file
            fname = os.path.splitext(out_file)[0] #in case an extension is provided remove it
            nom_path = self.nominal_value_path
            fname+=os.path.splitext(nom_path)[-1]
            fname = shutil.copy(nom_path,fname)
        else:
            fname = self.nominal[0].data.write(out_file)
        fname = os.path.abspath(fname)
        self.set_nominal_path(fname)
            
        
    def _write_statistic(self,stat_class,format_out_path):
        '''
        @brief write out our statistics data
        @param[in] stat_class - instance of MUFStatistic to write
        @param[in] out_dir - directory to write out to
        @param[in] format_out_path - formattable output path (e.g. path/to/dir/mc_{}.snp)
        @return list of written file paths (absolute paths)
        '''
        out_list = []
        if stat_class.data is None: #then copy
            files =  stat_class.file_paths
            for i,file in enumerate(files):
                fname = os.path.splitext(format_out_path.format(i))[0]
                fname+=os.path.splitext(file)[-1]
                fname_out = shutil.copy(file,fname)
                fname_out = os.path.abspath(fname_out)
                out_list.append(fname_out) #add to our list
        else:
            for i,dat in enumerate(stat_class.data): #loop through all of our data
                fname = os.path.splitext(format_out_path.format(i))[0]
                fname_out = dat.write(fname)
                fname_out = os.path.abspath(fname_out)
                out_list.append(fname_out)
        return out_list
    
    def _write_statistics(self,out_dir):
        '''
        @brief write out monte carlo and perturbed data
        '''
        mc_dir = os.path.join(out_dir,'MonteCarlo')
        if not os.path.exists(mc_dir):
            os.makedirs(mc_dir)
        mc_paths = self._write_statistic(self.monte_carlo,os.path.join(mc_dir,'monte_carlo_{}'))
        self.set_monte_carlo_paths(mc_paths)
        pt_dir = os.path.join(out_dir,'Perturbed')
        if not os.path.exists(pt_dir):
            os.makedirs(pt_dir)
        pt_paths = self._write_statistic(self.perturbed,os.path.join(mc_dir,'monte_carlo_{}'))
        self.set_perturbed_paths(pt_paths)
        
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
        for k,v in kwargs.items():
            options[k] = v
        #load our nominal and statistics if specified
        if options['write_nominal']:
            self._write_nominal(out_dir)
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
            write_stats - write out our statistics to a subfolder of meas_path (default True)
        '''
        out_dir = os.path.splitext(out_path)[0]
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        #write out the data first so we update the paths
        self._write_data(out_dir,**kwargs)
        self.write_xml(out_path)
        
class MUFStatistic(MUFItemList):
    '''
    @brief a class to generically calculate and hold statistics that the MUF does
         This will calculate and store the following statistics:
             -upper and lower n percent (default 95) confidence interval
             -nominal solution +- standard uncertainty (standard deviation)
             -nominal estimate (for monte carlos, sensitivity will just be nominal)
        Each of these uncertainties will be stored
    '''
    def __init__(self,xml_element,**arg_options):
        '''
        @brief constructor for the class. 
        @param[in] xml_element - parent element for MUF statistic xml
        @param[in/OPT] arg_options - keyword arguemnts as follows
                ci_percentage - confidence interval percentage (default is 95)
        '''
        super().__init__(xml_element)
        self.options = {}
        self.options['ci_percentage'] = 95
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
        #properties
        self.confidence_interval = {}
        self.standard_uncertainty = {}
        
    ###################################################
    ### IO Operations
    ################################################### 
    def plot(self,key,label=''):
        '''
        @brief plot statistics for a given key value 
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        '''
        rv_list = []
        rv_list.append(self.estimate.S[key].plot(DisplayName=label+' estimate'))
        rv_list.append(self.confidence_interval['+'].S[key].plot(DisplayName=label+' ci+ '+str(self.options['ci_percentage'])+'%'))
        rv_list.append(self.confidence_interval['-'].S[key].plot(DisplayName=label+' ci- '+str(self.options['ci_percentage'])+'%'))
        rv_list.append(self.standard_uncertainty['+'].S[key].plot(DisplayName=label+' std uncert +'))
        rv_list.append(self.standard_uncertainty['-'].S[key].plot(DisplayName=label+' std uncert -'))
        return rv_list
    
    def add_item(self,item):
        '''@brief extend super().add_item to allow adding Touchstone params'''
        if isinstance(item,TouchstoneEditor):#then make a MUFItem and set the value as the data
            mi = MUFItem(['name','path'])
            mi.data = item
            item = mi
        super().add_item(item)
        
    def load_data(self):
        '''@brief load in all of the data from each of the files'''
        for it in self.muf_items:
            it.load_data(TouchstoneEditor,**self.options)
    
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
        '''
        @brief get the frequency list from the estimate value
        '''
        return self.estimate.freq_list
    
    
class MUFNominalValue(MUFStatistic):
    '''
    @brief class to hold nominal value
    '''
    def __init__(self,xml_element,**arg_options):
        '''
        @brief constructor
        @param[in] xml_element - parent element for MUF statistic xml
        @param[in/OPT] arg_options - keyword arguemnts as follows
                plotter - SamuraiPlotter object to use
        '''
        super().__init__(xml_element,**arg_options)
        self.options = {}
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
            
    def plot(self,key,label='nominal',**arg_options):
        '''
        @brief plot our nominal value using the current plotter
        @param[in] key - measurement key to get stats for (e.g. 11,12,21,22,etc...)
        @param[in/OPT] label - extra label to add to the measurement
        @param[in/OPT] **arg_options - options passed to plot
        '''
        rv = self._muf_items[0].S[key].plot(DisplayName=label,**arg_options)
        return rv
    
    def __getattr__(self,attr):
        '''
        @brief pass any attribute calls to the first MUFItem
        '''
        try:
            return getattr(self._muf_items[0],attr)
        except:
            raise AttributeError(attr)


###################################################
### Some useful functions
###################################################  
def complex2magphase(data):
    '''
    @brief take a ndarray and change it to mag phase
    '''
    return np.abs(data),np.angle(data)

def magphase2complex(mag,phase):
    '''
    @brief turn magnitude phase data into complex data
    '''
    real = mag*np.cos(phase)
    imag = mag*np.sin(phase)
    return real+1j*imag

def get_name_from_path(path):
    '''
    @brief extract a name from a path (no extension or directory)
    '''
    return os.path.splitext(os.path.split(path)[-1])[0]

def moving_average(data,n=5):
    '''
    @brief calculate a moving average
    @param[in] data - data to calculate the moving average on
    @param[in/OPT] n - number of samples to average (default 5)
    @return averaged data. If complex average in mag/phase not real/imag. This will be of the same size as input
    @cite https://stackoverflow.com/questions/14313510/how-to-calculate-moving-average-using-numpy/54628145
    '''
    if np.iscomplexobj(data):
        #then split to mag phase
        mag,phase = complex2magphase(data)
        ave_mag   = moving_average(mag  ,n)
        ave_phase = moving_average(phase,n)
        return magphase2complex(ave_mag,ave_phase)
    else:
        ret = np.cumsum(data)
        ret[n:] = ret[n:] - ret[:-n]
        ret[n - 1:] /= n
        ret[:n] = data[:n]
        ret[-n:] = data[-n:]
        return ret

if __name__=='__main__':
    
    import unittest
    
    class MUFResultTest(unittest.TestCase):
    
        def test_load_xml(self):
            '''
            @brief in this test we will load a xml file with uncertainties and try
                to access the path lists of each of the uncertainty lists and the nominal result
            '''
            meas_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\7-8-2019\meas_cal_template.meas"
            res = MUFResult(meas_path)
            nvp = res.nominal_value_path #try getting our nominal value
            
        def test_create_from_empty(self):
            '''
            @brief in this test we create an empty .meas file and add our paths to it
                which is then written out
            '''
            pass
    
    #from samurai.base.SamuraiPlotter import SamuraiPlotter
    meas_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\7-8-2019\meas_cal_template.meas"
    #meas_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\7-8-2019\pdp_post_Results\meas_cal_template\PDPamplitude\meas_cal_template_PDPamplitude.meas"
    res = MUFResult(meas_path)
    #res2 = MUFResult(meas_path)
    #mil = MUFStatistic(res2._xml_monte_carlo)
    #mil.file_paths
    #MUFItem(res2._xml_monte_carlo.getchildren()[-1])
    #res2.calculate_statistics()
    
    #res = MUFResult(None)
    #val = TouchstoneEditor(meas_path)
    #res.nominal.add_item(val)
    #pvals = []
   # res.init_statistics()
   # res.monte_carlo.data = []
    #for i in range(5):
    #    rand_vals = ((np.random.rand(len(val))*2)-1)/10
   #     pvals.append(val*rand_vals)
    #res.monte_carlo.add_items(pvals)
    #res.write('test/meas_test.meas',write_nominal=True,write_statistics=True)
    #res3 = MUFResult('test.s2p')
    #os.chdir('test/write_test')
    #res.write('test/write_test/test.meas')
    #res2.write('test/write_test/test2.meas')
    #res3.write('test/write_test/test3.meas')
    
    
    #res = MUFResult(meas_path,plot_options={'plot_engine':['matplotlib']})
    #res.S[21].plot()
    #print("Calculating Statistics")
    #res.calculate_statistics()
    #sp = res.options['plotter']
    #res.monte_carlo.plot(21)
    #sp.legend()
    #sp.figure()
    #res.perturbed.plot(21)
    #sp.legend()
   
    
    #res_m = MUFResult('test.meas')
    #res_s = MUFResult('test.s2p')
    #res_w = MUFResult('test.w2p')
        
    
    
    
    
    
    
    