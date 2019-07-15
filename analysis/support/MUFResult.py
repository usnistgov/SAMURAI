# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,SnpError
from samurai.analysis.support.snpEditor import WnpParam
from samurai.analysis.support.SamuraiPlotter import SamuraiPlotter

#from xml.dom.minidom import parse, parseString
import numpy as np
#import xml.etree.ElementTree as ET
from lxml import etree as ET
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
        @param[in] meas_path - path to the *.meas file to load. 
            This can be passed as None if self.create_meas() is going to be run
        @param[in/OPT] arg_options - keyword arguments as follows:
            None yet!
            all arguments also passed to SnpEditor constructor
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
        #make sure were getting a .meas, if not get the correct data
        if meas_path is not None:
            _,ext = os.path.splitext(meas_path) #get our extension
            if '.meas' not in ext:
                nom_path = meas_path
            else:        
                self.load_xml(meas_path)
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
        
        #otherwise lets create a new MUFResult
        else:
            pass #just make sure to run MUFResult.create_meas on the instance in this case
        
        #uncertainty statistics
        self.monte_carlo = None
        self.perturbed = None
        
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
        mc_el_list = self._xml_monte_carlo.findall('Item')
        path_list = [subitems[1].get('Text') for subitems in mc_el_list]
        return path_list
    
    def get_monte_carlo_path(self,meas_num=None):
        '''
        @brief get a specific set of monte carlo paths
        @param[in] meas_num - which measurement or measurements to get (default to all)
        @return a list of paths (if meas_num is a list) or a single path if only 1 measurement defined
        '''
        mc_el_list = self._xml_monte_carlo.findall('Item')
        if meas_num is None: #we get all of them
            meas_num = range(len(mc_el_list))
        if not hasattr(meas_num,'__iter__'):
            meas_num = [meas_num] #make sure we have a iterable list
        path_list = [mc_el_list[i][1].get('Text') for i in meas_num]
        if len(path_list)==1:
            path_list = path_list[0] #return not a list if just 1 value
        return path_list
    
    def get_perturbed_path_list(self):
        '''
        @brief get a list of paths of perterturbed data
        @return list of paths to perturbed data
        '''
        pert_list = self._xml_perturbed.findall('Item')
        path_list = [subitems[1].get('Text') for subitems in pert_list]
        return path_list
    
    def get_perturbed_path(self,meas_num=None):
        '''
        @brief get a specific set of monte carlo paths
        @param[in] meas_num - which measurement or measurements to get (default to all)
        @return a list of paths (if meas_num is a list) or a single path if only 1 measurement defined
        '''
        pert_el_list = self._xml_perturbed.findall('Item')
        if not meas_num: #we get all of them
            meas_num = range(len(pert_el_list))
        if not hasattr(meas_num,'__iter__'):
            meas_num = [meas_num] #make sure we have a iterable list
        path_list = [pert_el_list[i][1].get('Text') for i in meas_num]
        if len(path_list)==1:
            path_list = path_list[0] #return not a list if just 1 value
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
    def nominal(self):
        '''
        @brief alias to access the nominal data by an attribute name
        '''
        return self
    
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
        #the element tree
        self._etree = ET.ElementTree()
        #root node
        self._root = ET.Element('CorrectedMeasurement')
        self._root.set('FileName','./')
        self._root.set('UserName',getpass.getuser())
        self._root.set('CreationTime',str(datetime.datetime.now()))
        self._etree._setroot(self._root)
        #create controls element
        self._controls = ET.SubElement(self._root,'Controls')  
        #now create our nominal
        self._xml_nominal = ET.SubElement(self._controls,'MeasSParams')
        self._xml_nominal.set('ControlType',"CustomFormControls.FLV_FixedDetailsList")
        self._xml_nominal.set('FullName',"Me_SplitContainer2__GroupBox2_Panel3_MeasSParams")
        self._xml_nominal.set('Count',str(0))
        #and monte carlo
        self._xml_monte_carlo = ET.SubElement(self._controls,'MonteCarloPerturbedSParams')
        self._xml_monte_carlo.set('ControlType',"CustomFormControls.FLV_VariableDetailsList")
        self._xml_monte_carlo.set('FullName',"Me_SplitContainer2__GroupBox3_Panel2_MonteCarloPerturbedSParams")
        self._xml_monte_carlo.set('Count',str(0))
        #and monte carlo
        self._xml_perturbed = ET.SubElement(self._controls,'PerturbedSParams')
        self._xml_perturbed.set('ControlType',"CustomFormControls.FLV_VariableDetailsListMeas")
        self._xml_perturbed.set('FullName',"Me_SplitContainer2__GroupBox1_Panel1_PerturbedSParams")
        self._xml_perturbed.set('Count',str(0))
        
    def _add_nominal_path(self,nom_path):
        '''
        @brief add a nominal path to the xml *.meas file
        @param[in] nom_path - nominal path
        '''
        self._add_meas_item_list([nom_path],self._xml_nominal)
      
    def _add_meas_item_list(self,path_list,parent_element):
        '''
        @brief add a measurement list from items and place it in a parent element (e.g self._xml_monte_carlo)
        '''
        for i,path in enumerate(path_list):
            item = self._create_meas_item(path,i)
            parent_element.append(item)
        parent_element.set('Count',str(len(path_list)))
    
    def _create_meas_item(self,path,index,name=None):
        '''
        @brief create an element for an item (a measurement in a .meas file)
        @param[in] path - path to the measurement
        @param[in] index - index of the item in the set
        @param[in/OPT] name - name of the item. If none use the name of the file
        '''
        if name is None:
            name = os.path.splitext(os.path.split(path)[-1])[0] #get the file name
        item = ET.Element('Item')
        item.set('Index',str(index))
        item.set('Text',name)
        #now add our subitems
        subitem_text = [name,path]
        for i,t in enumerate(subitem_text):
            si = ET.SubElement(item,'SubItem')
            si.set('Text',t)
            si.set('Index',str(i))
        #now set the number of subitems
        item.set('Count',str(len(item)))
        return item
    
    ##########################################################################
    ### extra io functions
    ##########################################################################
    
                
    def load_xml(self,meas_path):
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
        self._xml_nominal  = self._controls.find('MeasSParams')
        self._xml_monte_carlo = self._controls.find('MonteCarloPerturbedSParams')
        self._xml_perturbed = self._controls.find('PerturbedSParams')
        
    def write_xml(self,out_path):
        '''
        @brief write out our current xml file
        @param[in] out_path - path to writ ethe file out to 
        '''
        self._etree.write(out_path,pretty_print=True)
  
        
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
        if len(self.file_paths) > 2: #make sure we have enough to make a statistic
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
    '''
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
    '''
    #res_m = MUFResult('test.meas')
    #res_s = MUFResult('test.s2p')
    res_w = MUFResult('test.w2p')
        
    
    
    
    
    
    
    