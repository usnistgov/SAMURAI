# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:45:56 2019

@author: ajw5
"""

class MotiveInterface:
    '''
    @brief This is a class to interface with the NatNet server set up by Motive
        Motive is the software for optitrack cameras. This should allow us to easily
        access our live streaming values for our rigid bodies, and markers
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief intiialize the class
        @param[in/OPT] arg_options - keyword argument input as follows:
            None yet!
        '''