# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:11:26 2019

@author: ajw5
"""

from MUFModuleController import MUFModuleController

DEFAULT_VNAUNCERT_EXE_PATH = r"C:\Program Files (x86)\NIST\Uncertainty Framework\VNAUncertainty.exe"

#'C:/Users/ajw5/Source/Repos/MUF/VNAUncertainty/bin/Debug/VNAUncertainty.exe'

class VNAUncertPy(MUFModuleController):
    '''
    @brief class to control the VNA uncertainty calculator
    '''
    