# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 14:43:26 2019
THIS IS FOR PRODUCING SYNTHETIC (FAKE) DATA FOR SAMURAI TESTS
@author: ajw5
"""
from samurai.analysis.support.SamuraiPostProcess import SamuraiSyntheticApertureAlgorithm
from samurai.analysis.support.SamuraiPostProcess import get_k_vectors, to_azel, get_k

import numpy as np
@deprecated("This has been added to the SamuraiSyntheticApertureAlgorithm class")
class SamuraiSyntheticData(SamuraiSyntheticApertureAlgorithm):
    '''
    @brief class to produce synthetic plane wave data for given positions
    '''
    
    def __init__(self,positions,freqs,az_u=None,el_v=None,coord='azel',**arg_options):
        '''
        @brief initialize our synthetic data
        @param[in] positions - positions of synthetic aperture points shape==(num_pos,3) (2nd axis is xyz) 
        @param[in] freqs - frequencies to generate the data at
        @param[in/OPT] az_u - azel (or uv) pairs of angles for plane waves
        @param[in/OPT] el_v - azel (or uv) pairs of angles for plane waves
        '''
        super(SamuraiSyntheticData,self).__init__()
        self.positions = np.array(positions)
        self.num_waves = 0 #number of plane waves
        
        if not hasattr(freqs,'__iter__'):
            freqs = [freqs]
        self.freq_list = freqs
        
        #now add zeros for s parameter data
        self.s_parameter_data = np.zeros((self.positions.shape[0],len(self.freq_list)))
        
        
    
    def add_plane_wave(self,az_u,el_v,amplitude=1,coord='azel'):
        '''
        @brief add a plane wave to the s parameter data
        @param[in] az_u - azel (or uv) pairs of angles for plane waves
        @param[in] el_v - azel (or uv) pairs of angles for plane waves
        @param[in] amplitude - amplitude of the wave (default 1)
        @param[in/OPT] coord - coordinate system to use (uv or azel) default azel
        '''
        #change to lists if needed
        if not hasattr(az_u,'__iter__'):
            az_u = [az_u]
        if not hasattr(el_v,'__iter__'):
            el_v = [el_v]
        [az,el] = to_azel(az_u,el_v,coord) #change to azel
        #check that the length is the same
        if len(az) != len(el):
            raise Exception("Input angle vectors must be the same length")
        #now get our k vector values
        for fi,freq in enumerate(self.freq_list):
            sv = self.get_steering_vectors(az,el,get_k(freq)) #get the steering vector
            sv_sum = sv.sum(axis=1)*amplitude #sum across freqs and get our amplitude
            self.s_parameter_data[:,fi]+=sv_sum
            
            
        
        
        
if __name__=='__main__':
    pos = np.zeros(1225,6)*0.115 #random data points between 0 and 0.115m
    pos[0:3] = np.random.rand(1225,6)*0.115
    ssd = SamuraiSyntheticData(pos,40e9)
        