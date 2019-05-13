# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:58:12 2019

@author: aweis
"""

import matlab.engine
import six

class MatlabPlotter:
    '''
    @brief class for plotting figures using matlab engine
        This class will start a matlab engine when initiated and close it when
        deleted
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief initialize the class and start our MATLAB engine
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose - be verbose in our plotting (default False)
        '''
        self.options = {}
        self.options['verbose'] = False
        for key,val in six.iteritems(arg_options):
            self.options[key]=val
        if self.options['verbose']: print("Starting MATLAB Engine")
        self.engine = matlab.engine.start_matlab()
    
    def surf(X,Y,Z):
        '''
        @brief surface plot in MATLAB
        @param[in] X - np.array of X values
        @param[in] Y - np.array of Y values
        @param[in] Z - np.array of Z values
        @return matlab plot object
        '''
        