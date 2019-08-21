# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.base.TouchstoneEditor import TouchstoneEditor,TouchstoneError
from samurai.base.TouchstoneEditor import TouchstoneParam
from samurai.analysis.support.MUF.MUFModuleController import MUFModuleController
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
        #uncertainty statistics
        self.monte_carlo = None
        self.perturbed = None
        self.nominal = None
        self.options = {}
        self.options = {}
        self.options['ci_percentage'] = 95
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
        #make sure were getting a .meas, if not get the correct data
        menu_path = meas_path

        super().__init__(None,except_no_menu=False,**arg_options)
        self.load(menu_path,**arg_options)
        
    def init_statistics(self,**arg_options):
        '''
        @brief intialize (create the classes) for our MUF statistics
        '''
        mc_paths = self.get_monte_carlo_path_list()
        self.monte_carlo = MUFStatistic(mc_paths,**arg_options)
        pt_paths = self.get_perturbed_path_list()
        self.perturbed = MUFStatistic(pt_paths,**arg_options)
        
    def calculate_statistics(self,**arg_options):
        '''
        @brief calculate statistics for monte carlo and perturbed data
        '''
        self.calculate_monte_carlo_statistics(**arg_options,plotter=self.options['plotter'])
        self.calculate_perturbed_statistics(**arg_options,plotter=self.options['plotter'])
        
    def calculate_monte_carlo_statistics(self,**arg_options):
        '''
        @brief calculate monte carlo statistics
        '''
        self.monte_carlo.calculate_statistics()
        
    def calculate_perturbed_statistics(self,**arg_options):
        '''
        @brief calculate perturbed data statistics
        '''
        self.perturbed.calculate_statistics()
        
    def get_monte_carlo_path_list(self):
        '''
        @brief get a list of paths to our monte carlo data
        @return list of paths to monte carlo data
        '''
        mc_el_list = self._xml_monte_carlo.findall('Item')
        path_list = [items[1].get('Text') for items in mc_el_list]
        return path_list
    
    def get_perturbed_path_list(self):
        '''
        @brief get a list of paths of perterturbed data
        @return list of paths to perturbed data
        '''
        pert_list = self._xml_perturbed.findall('Item')
        path_list = [items[1].get('Text') for items in pert_list]
        return path_list
        
    @property
    def nominal_value_path(self):
        '''
        @brief property to return the path of the nominal value
        @return the path to the *.meas nominal value
        '''
        nom_name = self._xml_nominal[0][1].get('Text')
        return nom_name
    
    @property
    def _xml_nominal(self):
        '''
        @brief link to nominal xml path value
        '''
        return self.controls.find('MeasSParams')
    
    @property
    def _xml_monte_carlo(self):
        '''
        @brief link to monte_carlo xml path value
        '''
        return self.controls.find('MonteCarloPerturbedSParams')
    
    @property
    def _xml_perturbed(self):
        '''
        @brief link to monte_carlo xml path value
        '''
        return self.controls.find('PerturbedSParams')
    
    @property
    def _xml_root(self):
        '''
        @brief link to root xml node
        '''
        return self.getroot()
    
    def __getattr__(self,attr):
        '''
        @brief pass any nonexistant attribute attempts to our nominal value class
        '''
        try:
            return getattr(self.nominal,attr)
        except:
            raise AttributeError('{} not in self or self.nominal'.format(attr))
            
    ##########################################################################
    ### Data editing functions. This will only operate on loaded data
    ##########################################################################
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
    def create_meas(self,nom_path,monte_carlo_path_list=[],perturbed_path_list=[]):
        '''
        @brief create a *.meas file xml setup
        @param[in] nom_path - path to nominal measurement
        @param[in/OPT] monte_carlo_path_list - list of monte carlo paths 
        @param[in/OPT] perturbed_path_list - list of perturbed snp paths
        '''
        self._create_meas() #create the skeleton
        self._add_nominal_path(nom_path) #nominal
        self._add_meas_item_list(monte_carlo_path_list,self._xml_monte_carlo) #mc
        self._add_meas_item_list(perturbed_path_list,self._xml_perturbed) #perturbed
        self.__init__(nom_path)
        
        
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
        self._controls = ET.SubElement(self._xml_root,'Controls')  
        #now create our nominal
        ET.SubElement(self._controls,'MeasSParams')
        self._xml_nominal.set('ControlType',"CustomFormControls.FLV_FixedDetailsList")
        self._xml_nominal.set('FullName',"Me_SplitContainer2__GroupBox2_Panel3_MeasSParams")
        self._xml_nominal.set('Count',str(0))
        #and monte carlo
        ET.SubElement(self._controls,'MonteCarloPerturbedSParams')
        self._xml_monte_carlo.set('ControlType',"CustomFormControls.FLV_VariableDetailsList")
        self._xml_monte_carlo.set('FullName',"Me_SplitContainer2__GroupBox3_Panel2_MonteCarloPerturbedSParams")
        self._xml_monte_carlo.set('Count',str(0))
        #and monte carlo
        ET.SubElement(self._controls,'PerturbedSParams')
        self._xml_perturbed.set('ControlType',"CustomFormControls.FLV_VariableDetailsListMeas")
        self._xml_perturbed.set('FullName',"Me_SplitContainer2__GroupBox1_Panel1_PerturbedSParams")
        self._xml_perturbed.set('Count',str(0))
        
    def set_nominal_path(self,nom_path):
        '''
        @brief add a nominal path to the xml *.meas file
        @param[in] nom_path - nominal path
        '''
        self._set_paths(self._xml_nominal,[nom_path])
        
    def set_monte_carlo_paths(self,mc_path_list):
        '''
        @brief overwrite our monte carlo paths
        '''
        self._set_paths(self._xml_monte_carlo,mc_path_list)
        
    def set_perturbed_paths(self,pt_path_list):
        '''
        @brief overwrite perturbed paths
        '''
        self._set_paths(self._xml_perturbed,pt_path_list)
        
    def _set_paths(self,parent_element,path_list,subelem_idx=1):
        '''
        @brief function to set all paths from a list. This assumes the path is in subelement 1 (index from 0)
        '''
        for i,child in enumerate(list(parent_element)):
            list(child)[subelem_idx].attrib['Text'] = path_list[i]
      
    def _add_meas_item_list(self,parent_element,path_list):
        '''
        @brief add a measurement list from items and place it in a parent element (e.g self._xml_monte_carlo)
        '''
        item_list = []
        for i,path in enumerate(path_list):
            item_list.append(self._create_meas_item(path))
        self.add_items(parent_element,item_list)
        
    def _create_meas_item(self,path,name=None):
        '''
        @brief create an element for an item (a measurement in a .meas file)
        @param[in] path - path to the measurement
        @param[in/OPT] name - name of the item. If none use the name of the file
        '''
        if name is None:
            name = self._get_name_from_path(path)
        subitem_text = [name,path]
        return self.create_item(name,subitem_text)
        
    ##########################################################################
    ### extra io functions
    ##########################################################################
    
    
    
    def _load_data(self,meas_path):
        '''
        @brief load some data and return a loaded touchstoneEditor object
        '''
        return TouchstoneEditor(meas_path)
    
    def _load_nominal(self):
        '''
        @brief load the nominal path value into self.nominal
        '''
        nom_data = self._load_data(self.nominal_value_path)
        self.nominal = nom_data
        
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
        '''
        super().load(meas_path)
        
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
                menu_path = None
            else:
                self._load_xml(meas_path)
        else:
            raise Exception('Please Provide a *.meas path or a snp/wnp path')
        #load our nominal and statistics if specified
        if options['load_nominal']:
            self._load_nominal()
        if options['load_stats']:
            self.init_statistics()
            self._load_statistics()
            
    def _write_xml(self,out_path):
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
        if self.nominal is None: #then copy the file
            fname = os.path.splitext(out_file)[0] #in case an extension is provided remove it
            nom_path = self.nominal_value_path
            fname+=os.path.splitext(nom_path)[-1]
            fname = shutil.copy(nom_path,fname)
        else:
            fname = self.nominal.write(out_file)
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
        self._write_xml(out_path)
        
import scipy.stats as st
class MUFStatistic:
    '''
    @brief a class to generically calculate and hold statistics that the MUF does
         This will calculate and store the following statistics:
             -upper and lower n percent (default 95) confidence interval
             -nominal solution +- standard uncertainty (standard deviation)
             -nominal estimate (for monte carlos, sensitivity will just be nominal)
        Each of these uncertainties will be stored
    '''
    def __init__(self,stat_paths,**arg_options):
        '''
        @brief constructor for the class. 
        @param[in] stat_paths - list of paths to statistics measurements (should be snp or wnp (can be binary))
        @param[in/OPT] arg_options - keyword arguemnts as follows
                ci_percentage - confidence interval percentage (default is 95)
        '''
        self.options = {}
        self.options['ci_percentage'] = 95
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
        self.file_paths = stat_paths
        #properties
        self.confidence_interval = {}
        self.standard_uncertainty = {}
        self.data = None
            
    def calculate_statistics(self):
        '''
        @brief calculate and store all statistics. If self.data has been loaded use that
            Otherwise just momentarily load the data
        '''
        if len(self.file_paths) > 2: #make sure we have enough to make a statistic
            if self.data is None:
                snp_list = self._load_stat_files_to_list()
            else:
                snp_list = self.data
            data_dict = self._extract_data_dict(snp_list)
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
        @return estimate,ci_+,ci_-,std_+,std_- (WnpParams)
        '''
        est = self.estimate.S[key]
        cip = self.confidence_interval['+'].S[key]
        cim = self.confidence_interval['-'].S[key]
        stp = self.standard_uncertainty['+'].S[key]
        stm = self.standard_uncertainty['-'].S[key]
        return est,cip,cim,stp,stm
    
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
        
    def _load_stat_files_to_list(self):
        '''
        @brief load the files in self.file_paths to a WnpEditor list
        @return list of SnpEditor objects for the files in stat_paths
        '''
        tnp_list = []
        for path in self.file_paths:
            tnp_list.append(TouchstoneEditor(path))
        return tnp_list
    
    def load_data(self):
        '''
        @brief load our statistics files to self.stat_files. These will be WnpEditor types
        '''
        self.data = self._load_stat_files_to_list()
        
    def write_data(self,format_out_path):
        '''
        @brief write the data to a provided output path with a formattable string for numbering
        @param[in] format_out_path - formattable output path (e.g. path/to/data/monte_carlo_{}.snp/wnp)
        '''
        for i,d in enumerate(self.data):
            d.write(format_out_path.format(i))
            
    
    def _calculate_estimate(self,data_dict):
        '''
        @brief calculate the estimate from the input values (mean of the values)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor object with the estimate (mean) of the stats_path values
        '''
        #create a blank snp file to fill
        num_ports = round(np.sqrt(len(data_dict)-1)) #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        snp_out = SnpEditor([num_ports,freq_list],plotter=self.options['plotter'])
        for k in snp_out.wave_dict_keys:
            data = data_dict[k] #get the data
            m,p = self._complex2magphase(data)
            m_mean = m.mean(0); p_mean = p.mean(0)
            data_mean = self._magphase2complex(m_mean,p_mean)
            snp_out.S[k].update(freq_list,data_mean)
        return snp_out
            
    
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
        snp_out_p = SnpEditor([num_ports,freq_list],plotter=self.options['plotter'])
        snp_out_m = SnpEditor([num_ports,freq_list],plotter=self.options['plotter'])
        #find percentage and index like in the MUF
        percentage = 0.5*(1-self.options['ci_percentage']/100)
        lo_index = int(percentage*data_dict[11].shape[0])
        if lo_index<=0: lo_index=1
        hi_index = data_dict[11].shape[0]-lo_index
        for k in snp_out_p.wave_dict_keys:
            data = data_dict[k] #get the data
            #done in the same way as the MUF
            m,p = self._complex2magphase(data)
            m.sort(0); p.sort(0)
            m_hi = m[hi_index,:]; m_lo = m[lo_index]
            p_hi = p[hi_index,:]; p_lo = p[lo_index]
            hi_complex = self._magphase2complex(m_hi,p_hi)
            lo_complex = self._magphase2complex(m_lo,p_lo)
            snp_out_p.S[k].update(freq_list,hi_complex)
            snp_out_m.S[k].update(freq_list,lo_complex)
        return snp_out_p,snp_out_m
    
    def _calculate_standard_uncertainty(self,data_dict):
        '''
        @brief calculate standard uncertainty (standard deviation)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor objects for upper(+),lower(-) uncerts
        '''
        #create a blank snp file to fill
        num_ports = round(np.sqrt(len(data_dict)-1)) #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        snp_out_p = SnpEditor([num_ports,freq_list],plotter=self.options['plotter'])
        snp_out_m = SnpEditor([num_ports,freq_list],plotter=self.options['plotter'])
        for k in snp_out_p.wave_dict_keys:
            data = data_dict[k] #get the data
            m,p = self._complex2magphase(data)
            m_mean = m.mean(0); p_mean = p.mean(0)
            m_std  = m.std(0) ; p_std  = p.std(0) #mean and stdev of mag/phase
            m_plus = m_mean+m_std; m_minus = m_mean-m_std
            p_plus = p_mean+p_std; p_minus = p_mean-p_std
            data_plus   = self._magphase2complex(m_plus ,p_plus )
            data_minus  = self._magphase2complex(m_minus,p_minus)
            snp_out_p.S[k].update(freq_list,data_plus)
            snp_out_m.S[k].update(freq_list,data_minus)
        return snp_out_p,snp_out_m
    
    
    def _extract_data_dict(self,snp_list):
        '''
        @brief extract data from our snp_list into a dictionary with snp_list[0].wave_dict_key keys
                and values of (n,m) 2D numpy arrays where n is len(snp_list) and m is len(snp_list[0].freq_list)
        @return a dictionary as described in the brief
        '''
        data_dict = {}
        data_dict['freq_list'] = snp_list[0].freq_list
        for k in snp_list[0].wave_dict_keys:
            data_dict[k] = np.array([snp.S[k].raw for snp in snp_list])
        return data_dict
    
    def _complex2magphase(self,data):
        '''
        @brief take a ndarray and change it to mag phase
        '''
        return np.abs(data),np.angle(data)
    
    def _magphase2complex(self,mag,phase):
        '''
        @brief turn magnitude phase data into complex data
        '''
        real = mag*np.cos(phase)
        imag = mag*np.sin(phase)
        return real+1j*imag
            
    @property
    def freq_list(self):
        '''
        @brief get the frequency list from the estimate value
        '''
        return self.estimate.freq_list

if __name__=='__main__':
    
    from samurai.analysis.support.SamuraiPlotter import SamuraiPlotter
    meas_path = 'test.meas'
    #res = MUFResult(meas_path,load_stats=True)
    res2 = MUFResult(meas_path)
    res3 = MUFResult('test.s2p')
    #os.chdir('test/write_test')
    #res.write('test/write_test/test.meas')
    res2.write('test/write_test/test2.meas')
    res3.write('test/write_test/test3.meas')
    '''
    res = MUFResult(meas_path,plot_options={'plot_engine':['matplotlib']})
    res.S[11].plot()
    print("Calculating Statistics")
    res.calculate_statistics()
    sp = res.options['plotter']
    res.monte_carlo.plot(11)
    sp.legend()
    sp.figure()
    res.perturbed.plot(11)
    sp.legend()
    '''
    
    #res_m = MUFResult('test.meas')
    #res_s = MUFResult('test.s2p')
    #res_w = MUFResult('test.w2p')
        
    
    
    
    
    
    
    