# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,WnpEditor,SnpError

#from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
import os
import re

class MUFResult(SnpEditor):
    '''
    @brief a class to deal with MUF results (and easily get uncertainties, monte_carlos, and whatnot)
        self is the nominal value. Other values will be contained to generate uncerts
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


if __name__=='__main__':
    meas_path = 'test.meas'
    res = MUFResult(meas_path)
    
        