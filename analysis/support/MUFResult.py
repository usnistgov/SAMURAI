# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,SnpError
from samurai.analysis.support.snpEditor import WnpParam

#from xml.dom.minidom import parse, parseString
import numpy as np
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
        self.options = {}
        self.options = {}
        self.options['ci_percentage'] = 95
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
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
        super().__init__(nom_path,**self.options) #init wave params or s params
        
        #uncertainty statistics
        self.monte_carlo = None
        self.perturbed = None
            
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
        self._perturbed = self._controls.find('PerturbedSParams')
        
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
        mc_paths = self.get_monte_carlo_path_list()
        self.monte_carlo = MUFStatistic(mc_paths,**arg_options)
        self.monte_carlo.calculate_statistics()
        
    def calculate_perturbed_statistics(self,**arg_options):
        '''
        @brief calculate perturbed data statistics
        '''
        pt_paths = self.get_perturbed_path_list()
        self.perturbed = MUFStatistic(pt_paths,**arg_options)
        self.perturbed.calculate_statistics()
        
    def get_monte_carlo_path_list(self):
        '''
        @brief get a list of paths to our monte carlo data
        @return list of paths to monte carlo data
        '''
        mc_el_list = self._monte_carlo.findall('Item')
        path_list = [subitems[1].get('Text') for subitems in mc_el_list]
        return path_list
    
    def get_perturbed_path_list(self):
        '''
        @brief get a list of paths of perterturbed data
        @return list of paths to perturbed data
        '''
        pert_list = self._perturbed.findall('Item')
        path_list = [subitems[1].get('Text') for subitems in pert_list]
        return path_list
        
    @property
    def nominal_value_path(self):
        '''
        @brief property to return the path of the nominal value
        @return the path to the *.meas nominal value
        '''
        nom_name = self._nominal[0][1].get('Text')
        return nom_name
    
    
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
        rv_list.append(self.standard_uncertainty['-'].S[key].plot(DisplayName=label+' std uncert '))
        return rv_list
        
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
    res = MUFResult(meas_path,plot_options={'plot_order':['matplotlib']})
    #res.S[11].plot()
    print("Calculating Statistics")
    res.calculate_statistics()
    sp = res.options['plotter']
    res.monte_carlo.plot(11)
    sp.legend()
    sp.figure()
    res.perturbed.plot(11)
    sp.legend()
    #stats_path = 
        
    
    
    
    
    
    
    