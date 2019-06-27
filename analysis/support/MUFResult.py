# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,SnpError
from samurai.analysis.support.snpEditor import WnpParam

#from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
import os
import re

class MUFResult(SnpEditor):
    '''
    @brief a class to deal with MUF results (and easily get uncertainties, monte_carlos, and whatnot)
        self is the nominal value. Other values will be contained to generate uncerts
    
    Example
    -------
        >>> meas_path = './test.meas' #path to *.meas file
        >>> mymeas = MUFResult(meas_path) #initialize the class
        >>> mymeas.calculate_monte_carlo_statistics() 
    '''
    def __init__(self,meas_path,**arg_options):
        '''
        @brief load up and initialize the *.meas file
        @param[in] meas_path - path to the *.meas file to load
        @param[in/OPT] arg_options - keyword arguments as follows:
            None yet!
            all arguments also passed to SnpEditor constructor
        @todo ADD case for if we do not get a *.meas but get a snp or wnp file
        '''
        self.parse_xml(meas_path)
        nom_path = self.nominal_value_path
        #lets set the correct options for w/s params
        _,ext = os.path.splitext(nom_path)
        #use re to get wp or sp (remove all numbers and '_binary')
        rc = re.compile('\d+|_binary')
        ext_cut = rc.sub('',ext)
        if ext_cut == '.sp':
            self.param_type = 's'
            waves = ['S']
            arg_options['waves'] = waves
        elif ext_cut == '.wp':
            self.param_type = 'w'
            waves = ['A','B']
            arg_options['waves'] = waves
        else:
            raise SnpError("Nominal file extension not recognized")
        super().__init__(nom_path,**arg_options) #init wave params or s params
            
    def parse_xml(self,meas_path):
        '''
        @brief  parse our file into a dom struct
        @param[in] meas_path - path to *.meas file
        @note this also extracts the following etree elements
            _root - root of the tree
            _controls - *.meas 'Controls' element
            _nominal  - *.meas 'Controls->MeasSParams' element
            _monte_carlo - *.meas 'Controls->MonteCarloPerturbedSParams' element
        '''
        self._xml_file_path = meas_path
        self._etree = ET.parse(meas_path)
        self._root = self._etree.getroot()
        self._controls = self._root.find('Controls') #*.meas controls
        self._nominal  = self._controls.find('MeasSParams')
        self._monte_carlo = self._controls.find('MonteCarloPerturbedSParams')
     
    def get_monte_carlo_path_list(self):
        '''
        @brief get a list of paths to our monte carlo data
        @return list of paths to monte carlo data
        '''
        pass
        
    @property
    def nominal_value_path(self):
        '''
        @brief property to return the path of the nominal value
        '''
        unpt_name = self._nominal[0][1].get('Text')
        return unpt_name
    
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
        for k,v in arg_options.items():
            self.options[k] = v
        self.file_paths = stat_paths
            
    def calculate_statistics(self):
        '''
        @brief calculate and store all statistics
        '''
        snp_list = self._load_stat_files_to_list()
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
        
    def _load_stat_files_to_list(self):
        '''
        @brief load the files in self.file_paths to a WnpEditor list
        @return list of SnpEditor objects for the files in stat_paths
        '''
        snp_list = []
        for path in self.file_paths:
            snp_list.append(SnpEditor(path))
        return snp_list
    
    def _calculate_estimate(self,data_dict):
        '''
        @brief calculate the estimate from the input values (mean of the values)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor object with the estimate (mean) of the stats_path values
        '''
        #create a blank snp file to fill
        num_ports = len(data_dict)-1 #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        snp_out = SnpEditor([num_ports,freq_list])
        for k in snp_out.wave_dict_keys:
            data = data_dict[k] #get the data
            data = data.mean(0) #take the mean
            snp_out.S[k].update(freq_list,data)
        return snp_out
            
    
    def _calculate_confidence_interval(self,data_dict):
        '''
        @brief calculate the n% confidence interval where n is self.options['ci_percentage']
            this will calculate both the upper and lower intervals
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor objects for upper(+),lower(-) intervals
        '''
        #create a blank snp file to fill
        num_ports = len(data_dict)-1 #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        snp_out = SnpEditor([num_ports,freq_list])
        for k in snp_out.wave_dict_keys:
            data = data_dict[k] #get the data
            data = data.std(0) #take the mean
            snp_out.S[k].update(freq_list,data)
        return snp_out
    
    def _calculate_standard_uncertainty(self,data_dict):
        '''
        @brief calculate standard uncertainty (standard deviation)
        @param[in] data_dict - dictionary of data and frequencies for imported snp files
        @return WnpEditor objects for upper(+),lower(-) uncerts
        '''
        #create a blank snp file to fill
        num_ports = len(data_dict)-1 #-1 to ignore the freq_list entry
        freq_list = data_dict['freq_list']
        snp_out = SnpEditor([num_ports,freq_list])
        for k in snp_out.wave_dict_keys:
            data = data_dict[k] #get the data
            data = data.std(0) #take the mean
            snp_out.S[k].update(freq_list,data)
        return snp_out
    
    
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
                

if __name__=='__main__':
    meas_path = 'test.meas'
    res = MUFResult(meas_path)
    res.S[11].plot()
    stats_path = 
        
    
    
    
    
    
    
    