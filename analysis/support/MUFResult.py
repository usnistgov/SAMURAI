# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,WnpEditor

from xml.dom.minidom import parse, parseString
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
        '''
        self.parse_dom(meas_path)
        nom_path = self.nominal_value_path
        #lets set the correct options for w/s params
        _,ext = os.path.splitext(nom_path):
        #use re to get wp or sp (remove all numbers and '_binary')
        rc = re.compile('\d+|_binary')
        ext_cut = rc.sub('',ext)
        if ext_cut is '.sp':
            self.param_type = 's'
            wave_list = ['S']
        elif ext_cut is '.wp':
            self.param_type = 'w'
            wave_list = ['A','B']
        super().__init__(nom_path,waves=wave_list) #init wave params or s params
            
    def parse_dom(self,meas_path):
        '''
        @brief  parse our file into a dom struct
        @param[in] meas_path - path to *.meas file
        '''
        self._dom_file_path = meas_path
        self._dom = parse(meas_path)
        
        
    @property
    def nominal_value_path(self):
        '''
        @brief property to return the path of the nominal value
        '''
        msp = self._dom.getElementsByTagName('MeasSParams').item(0)
        unpt = msp.getElementsByTagName('Item').item(0)
        unpt_name = unpt.getElementsByTagName('SubItem').item(1).getAttribute('Text')
        return unpt_name
        
        