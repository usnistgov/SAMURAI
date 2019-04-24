# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""
from samurai.analysis.support.SamuraiPostProcess import SamuraiSyntheticApertureAlgorithm
from samurai.analysis.support.SamuraiPostProcess import to_azel
from samurai.analysis.support.SamuraiPostProcess import CalculatedSyntheticAperture
from samurai.analysis.support.SamuraiPostProcess import calculate_steering_vector
from samurai.analysis.support.SamuraiPostProcess import Antenna
import numpy as np #import constants
import math #for vectorize math functions
import scipy.constants as sp_consts #import constants for speed of light
import cmath #cmath for phase
from numba import vectorize

import six #backward compatability

class SamuraiBeamform(SamuraiSyntheticApertureAlgorithm):
    '''
    @brief samurai synthetic aperture using beamforming
    '''
    def __init__(self,metafile_path=None,**arg_options):
        '''
        @brief initilization for class. We can load our metafile here or not
            This inherits from a generic SamuraiPostProcess class providing easy access to the data
        @param[in] metafile_path - metafile if we want to load one now
        @param[in/OPT] arg_options - keyword arguments as follows. Also passed to inherited class so look at those options
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
            measured_values - are we using measurements, or simulated data (default True)
            load_key        - Key to load values from (e.g. 21,11,12,22) when using measured values (default 21)
        '''
        super(SamuraiBeamform,self).__init__(metafile_path,**arg_options)
    
    def beamforming_farfield_azel(self,az_vals,el_vals,freq_list='all',**arg_options):
        '''
        @brief calculate the beamforming assuming farfield for angles in azimuth elevation
            All locations will be pulled from the metafile positions
        @param[in] az_vals - azimuth angles in elevation from x axis
        @param[in] el_vals - elevation angles in azimuth from xy plane
        @note - az and el vals will be meshgridded (only provide cross sections)
        @param[in/OPT] freq_list  - list of frequencies to calculate for 'all' will do all frequencies
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
        @note theta and phi vals will be created into a meshgrid
        @return list of CalculatedSyntheticAperture objects
        '''
        #make the meshgrid
        [AZ,EL] = np.meshgrid(az_vals,el_vals)
        
        return self.beamforming_farfield(AZ,EL,freq_list=freq_list,coord='azel',**arg_options)
        
    def beamforming_farfield_uv(self,u_vals,v_vals,freq_list='all',**arg_options):
        '''
        @brief calculate the beamforming assuming farfield for angles in uv
            All locations will be pulled from the metafile positions
        @param[in] u_vals - u values
        @param[in] v_vals - v values
        @note - az and el vals will be meshgridded (only provide cross sections)
        @param[in/OPT] freq_list  - list of frequencies to calculate for 'all' will do all frequencies
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
        @note theta and phi vals will be created into a meshgrid
        @return list of CalculatedSyntheticAperture objects
        '''
        #make the meshgrid
        [U,V] = np.meshgrid(u_vals,v_vals)
        
        #get values that are less than 1
        l1vals = np.sqrt(U*V)<1
        U[l1vals] = np.nan
        V[l1vals] = np.nan
        
        return self.beamforming_farfield(U,V,freq_list=freq_list,coord='uv',**arg_options)
        
        
    def beamforming_farfield(self,az_u,el_v,freq_list='all',coord='azel',**arg_options):
        '''
        @brief calculate the beamforming assuming farfield for angles in spherical coordinates
            All locations will be pulled from the metafile positions
        @param[in] az_u - mesh of azimuth or U values corresponding to matching value in el_v
        @param[in] el_v - mesh of azimuth or U values corresponding to matching value in az_u
        @param[in] coord - which coordinate system we are using ('azel' or 'uv')
        @note if we are in u,v we will simply translate to azel
        @param[in/OPT] freq_list  - list of frequencies to calculate for 'all' will do all frequencies
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
            unit_mult - unit multiplier for positions
        @note theta and phi vals will be created into a meshgrid
        @return list of CalculatedSyntheticAperture objects
        '''
        #input options (these are defaults)
        options = {}
        options['verbose'] = self.options['verbose']
        options['antenna_pattern'] = self.options['antenna_pattern']
        for key,val in six.iteritems(arg_options):
            options[key] = val #set kwargs
        antenna_pattern = options['antenna_pattern']
        verbose = options['verbose']
        
        #validate our current data
        self.validate_data()
        
        #list of calulcated synthetic apertures
        csa_list = []
        
        s_freq_list = self.freq_list
        s21_vals = self.s_parameter_data
        
        #set our frequency list
        if freq_list=='all': #make all frequcnies if 'all'
            freq_list = s_freq_list
        if not hasattr(freq_list,'__iter__'): #make a list if its not
            freq_list = [freq_list] 
        freq_list = np.array(freq_list)
        
        #change our coordinates to azel
        [azimuth,elevation] = to_azel(az_u,el_v,coord)
        
        #get our position data
        if verbose: print("Reading measurement positions")
        pos = self.get_positions('m') #get all of our positions in meters
        az_angles = pos[:,5] #with current coordinates system azimuth=gamma
        
        #now lets use this data to get our delta_r beamforming values
        #this delta_r will be a 2D array with the first dimension being for each position
        # the second dimeino will be each of the theta/phi pairs for the angles
        if verbose: print("Finding Partial Steering Vectors vectors")
        psv_vecs =  self.get_partial_steering_vectors(azimuth,elevation) #k_vectors*position_vectors
        
        #set our antenna values
        az_adj = -1*az_angles[:,np.newaxis]+np.reshape(azimuth,(-1,))
        el_adj = np.zeros(az_adj.shape)
        if(antenna_pattern is not None):
            antenna_values = antenna_pattern.get_values(az_adj,el_adj)
        else:
            antenna_values = np.ones(psv_vecs.shape)
        
        #now lets loop through each of our frequencies in freq_list
        if verbose: print("Beginning beamforming for %d frequencies" %(len(freq_list)))
        for freq in freq_list:
            if verbose: print("    Calculating for %f Hz" %(freq))
            freq_idx = np.where(s_freq_list==freq)[0]
            if(freq_idx.size<1):
                print("    WARNING: Frequency %f Hz not found. Aborting." %(freq))
                continue # dont beamform on this frequency
            elif(freq_idx.size>1):
                print("    WARNING: More than one frequency %f Hz found. Aborting" %(freq))
                continue
            else:
                freq_idx = freq_idx[0]
            #if we make it here the frequency exists. now get our s params for the current frequency
            s21_current = s21_vals[:,freq_idx]
            #now we can calculate the beam phases for each of the angles at each position
            #here we add a
            lam = sp_consts.c/freq
            k = 2.*np.pi/lam
            steering_vectors = np.exp(-1j*k*psv_vecs)

            # sum(value_at_position*steering_vector) for each angle
            # now calculate the values at each angle
            beamformed_vals = np.dot(s21_current,steering_vectors/antenna_values)/len(s21_current)
            
            #now pack into our CSA (CaluclateSynbteticAperture)
            csa_list.append(CalculatedSyntheticAperture(azimuth,elevation,np.reshape(beamformed_vals,azimuth.shape)))
        
        ant_vals = CalculatedSyntheticAperture(azimuth,elevation,np.reshape(antenna_values[1,:],azimuth.shape))
        return csa_list,ant_vals
        #return csa_list,steering_vectors,s21_current,x_locs,y_locs,z_locs,delta_r
    
#this is a test case for when this file itself is run (not importing the module)
if __name__=='__main__':
    #test case for simple beamforming
    '''
    test_path = r".\\data\\2-13-2019\\binary_aperture_planar\\metafile_binary.json"
    #test_path = r".\\data\\2-13-2019\\binary_aperture_cylindrical\\metafile_binary.json"
    mysp = SamuraiBeamform(test_path,verbose=True)
    #azel without antenna
    #mycsa_list = mysp.beamforming_farfield(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
    #azel with antenna
    test_ant_path = './data/test_ant_pattern.csv'
    myant = Antenna(test_ant_path,dimension=1,plane='az')
    myap = myant['pattern']
    #mycsa_list,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True,antenna_pattern=myap)
    mycsa_list,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
    #UV beamform
    #mycsa_list,ant_vals = mysp.beamforming_farfield_uv(np.arange(-1,1.001,0.01),np.arange(-1,1.001,0.01),40e9,verbose=True,antenna_pattern=myap)
    mycsa = mycsa_list[0]
    mycsa.plot_3d()
    '''
    #testing our synthetic data capabilities
    mysp = SamuraiBeamform(verbose=True)
    pos = np.zeros((1225,6))*0.115 #random data points between 0 and 0.115m
    pos[:,0:3] = np.random.rand(1225,3)*0.115
    mysp.all_positions = pos;
    mysp.freq_list = [40e9]
    mysp.add_plane_wave(0,0)
    mycsa_list,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
    mycsa = mycsa_list[0]
    mycsa.plot_3d()
    
    
    
    