# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:58:12 2019

@author: aweis
"""

import matlab.engine

class MatlabPlotter:
    '''
    @brief class for plotting figures using matlab engine
        This class will start a matlab engine when initiated and close it when
        deleted
    '''
    
    def __init__(self):
        '''
        @brief initialize the class and start our MATLAB engine
        @return phrase MATLAB engine started
        '''
        print("Starting MATLAB Engine")
        self.eng = matlab.engine.start_matlab()
        return "MATLAB Engine Started"
    
    def surf(X,Y,Z):
        '''
        @brief surface plot in MATLAB
        @param[in] X - np.array of X values
        @param[in] Y - np.array of Y values
        @param[in] Z - np.array of Z values
        @return matlab plot object
        '''
        