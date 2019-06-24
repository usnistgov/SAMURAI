# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 16:02:04 2019

@author: ajw5
"""

from samurai.analysis.support.snpEditor import SnpEditor,WnpEditor

class MUFResult(:
    '''
    @brief a class to deal with MUF results (and easily get uncertainties, monte_carlos, and whatnot)
    '''
    def __init__(self,meas_path):
        '''
        @brief load up and initialize the *.meas file
        @param[in] meas_path - path to the *.meas file to load