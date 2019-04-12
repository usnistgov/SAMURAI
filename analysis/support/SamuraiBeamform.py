# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""
from samurai.analysis.support.SamuraiPostProcess import SamuraiPostProcess,CalculatedSyntheticAperture
import numpy as np #import constants
import math #for vectorize math functions
import scipy.constants as sp_consts #import constants for speed of light
import cmath #cmath for phase
from numba import vectorize

import six #backward compatability

#generic class for synthetic aperture algorithms
class SamuraiSyntheticApertureAlgorithm:
    '''
    @brief this is a generic class for samurai aglorithms.
    this should be completed and the rest of this restructured in the future
    This will allow a more generic things to work with such as importing measured vs. simed values
    '''
    def __init__(metafile_path=None,**arg_options):
        '''
        @brief initilaize the SamSynthApAlg class
        @param[in/OPT] metafile_path - metafile for real measurements (defaults to None)
        '''

class SamuraiBeamform(SamuraiPostProcess):
    '''
    @brief samurai synthetic aperture using beamforming
    '''
    def __init__(self,metafile_path,**arg_options):
        '''
        @brief initilization for class. We can load our metafile here or not
            This inherits from a generic SamuraiPostProcess class providing easy access to the data
        @param[in] metafile_path - metafile if we want to load one now
        @param[in/OPT] arg_options - keyword arguments as follows. Also passed to MetaFileController from which we inherit
                        No keyword args yet!
        '''
        super(SamuraiBeamform,self).__init__(metafile_path,**arg_options)
    
               
    def beamforming_farfield(self,theta_vals,phi_vals,freq_list='all'**arg_options):
        '''
        @brief calculate the beamforming assuming farfield for angles in spherical coordinates
            All locations will be pulled from the metafile positions
        @param[in] theta_vals - theta angles in elevation from xy plane
        @param[in] phi_vals   - phi angles in azimuth from x
        @param[in/OPT] freq_list  - list of frequencies to calculate for 'all' will do all frequencies
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
        @note theta and phi vals will be created into a meshgrid
        @return list of CalculatedSyntheticAperture objects
        '''
        #input options (these are defaults)
        self.options['verbose'] = False
        self.options['antenna_pattern'] = None
        self.options['measured_values'] = True
        for key,val in six.iteritems(arg_options):
            self.options[key] = val #set kwargs
        
        #list of calulcated synthetic apertures
        csa_list = []
        
        #get our s-parameter data 
        if(self.options['measured_values']): #load measured data
            if verbose: print("Loading S-parameter data")
            [s_freq_list,s21_vals] = self.load_s_params_to_memory(verbose=verbose,load_key=21)
            s_freq_list = s_freq_list*1e9 #change to ghz
            
        #set our frequency list
        if freq_list=='all': #make all frequcnies if 'all'
            freq_list = s_freq_list
        if not hasattr(freq_list,'__iter__'): #make a list if its not
            freq_list = [freq_list] 
        freq_list = np.array(freq_list)
        
        #get our position data
        if verbose: print("Reading measurement positions")
        pos = self.get_positions() #get all of our positions
        unit_mult = 0.001 #multiply to get in meters
        x_locs = np.reshape(pos[:,0],(-1,1))*unit_mult; x_locs = x_locs-x_locs.mean() #and unpack all the data
        y_locs = np.reshape(pos[:,1],(-1,1))*unit_mult; y_locs = y_locs-y_locs.mean() #this is all in mm to change to meters
        z_locs = np.reshape(pos[:,2],(-1,1))*unit_mult; z_locs = z_locs-z_locs.mean() #all values must be positive so subtract from lowest point
        az_angles = pos[:,5] #with current coordinates system azimuth=gamma
        
        #now lets create the meshgrid for our theta and phi values
        if verbose: print("Creating angular meshgrid")
        [THETA,PHI] = np.meshgrid(theta_vals,phi_vals)
        theta_mesh_rad = np.deg2rad(np.reshape(THETA,(1,-1))) #reshape to 1D array
        phi_mesh_rad   = np.deg2rad(np.reshape(PHI,(1,-1)))
        
        #now lets use this data to get our delta_r beamforming values
        #this delta_r will be a 2D array with the first dimension being for each position
        # the second dimeino will be each of the theta/phi pairs for the angles
        if verbose: print("Finding delta-r")
        x_r = x_locs*np.cos(theta_mesh_rad)*np.cos(phi_mesh_rad)
        y_r = y_locs*np.cos(theta_mesh_rad)*np.sin(phi_mesh_rad)
        z_r = z_locs*np.sin(theta_mesh_rad)
        #delta_r = np.sqrt(x_r**2+y_r**2+z_r**2) #we have no direction here...
        delta_r = x_r+y_r+z_r
        #delta_r = np.sqrt(y_r**2+z_r**2)
        
        #set our antenna values
        az_adj = -1*az_angles[:,np.newaxis]+np.reshape(PHI,(-1,))
        el_adj = np.zeros(az_adj.shape)
        if(antenna_pattern is not None):
            antenna_values = antenna_pattern.get_values(az_adj,el_adj)
        else:
            antenna_values = np.ones(delta_r.shape)
        
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
            steering_vectors = np.exp(-1j*k*delta_r)
        

            # sum(value_at_position*steering_vector) for each angle
            # now calculate the values at each angle
            beamformed_vals = np.dot(s21_current,steering_vectors/antenna_values)/len(s21_current)
            
            #now pack into our CSA (CaluclateSynbteticAperture)
            csa_list.append(CalculatedSyntheticAperture(THETA,PHI,np.reshape(beamformed_vals,THETA.shape)))
        
        ant_vals = CalculatedSyntheticAperture(THETA,PHI,np.reshape(antenna_values[1,:],THETA.shape))
        return csa_list,ant_vals
        #return csa_list,steering_vectors,s21_current,x_locs,y_locs,z_locs,delta_r
    
    def beamforming_farfield_uv(self,u_vals,v_vals,freq_list='all',verbose=False):
        '''
        @brief wrapper around typical beamforming to calculate in uv domain. Unfortunately this doesnt work right now because we have u**2+v**2>1
        @param[in] u_vals - vector of u locations (azimuth)
        @param[in] v_vals - vector of v locations (elevation)
        @param[in/OPT] freq_list - what frequencies to calculate for
        @param[in/OPT] verbose - do we wanna be verbose?
        @return list of CalculatedSyntheticAperture objects
        @TODO Ensure that the math behind this is correct (currently just used bens math)
        @TODO make the values for UV be between -1,1 with sqrt(u**2+v**2)<1
        '''
        #list of calulcated synthetic apertures
        csa_list = []
        
        #get our s-parameter data
        if verbose: print("Loading S-parameter data")
        [s_freq_list,s21_vals] = self.load_s_params_to_memory(verbose=verbose,load_key=21)
        s_freq_list = s_freq_list*1e9 #change to ghz
        #set our frequency list
        if freq_list=='all': #make all frequcnies if 'all'
            freq_list = s_freq_list
        if not hasattr(freq_list,'__iter__'): #make a list if its not
            freq_list = [freq_list] 
        freq_list = np.array(freq_list)
        
        #get our position data
        if verbose: print("Reading measurement positions")
        pos = self.get_positions() #get all of our positions
        unit_mult = 0.001 #multiply to get in meters
        x_locs = np.reshape(pos[:,0],(-1,1))*unit_mult; x_locs = x_locs-x_locs.mean() #and unpack all the data
        y_locs = np.reshape(pos[:,1],(-1,1))*unit_mult; y_locs = y_locs-y_locs.mean() #this is all in mm to change to meters
        z_locs = np.reshape(pos[:,2],(-1,1))*unit_mult; z_locs = z_locs-z_locs.mean() #all values must be positive so subtract from lowest point
        #theta_locs = pos[:,5] #angle of the antenna
        
        #now lets create the meshgrid for our theta and phi values
        if verbose: print("Creating UV meshgrid")
        [U,V] = np.meshgrid(u_vals,v_vals)
        u_mesh_rad = np.deg2rad(np.reshape(U,(1,-1))) #reshape to 1D array
        v_mesh_rad   = np.deg2rad(np.reshape(V,(1,-1)))
        
        #now lets use this data to get our delta_r beamforming values
        #this delta_r will be a 2D array with the first dimension being for each position
        # the second dimeino will be each of the theta/phi pairs for the angles
        if verbose: print("Finding delta-r")
        x_r = x_locs*np.sin(v_mesh_rad)    #this math taken from bens code
        y_r = y_locs*np.sin(u_mesh_rad)
        z_r = z_locs*np.sqrt(1-(np.sin(v_mesh_rad)**2+np.sin(u_mesh_rad)**2))
        #delta_r = np.sqrt(x_r**2+y_r**2+z_r**2) #we have no direction here...
        delta_r = x_r+y_r+z_r
        #delta_r = np.sqrt(y_r**2+z_r**2)
        
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
            steering_vectors = np.exp(-1j*k*delta_r)

            # sum(value_at_position*steering_vector) for each angle
            # now calculate the values at each angle
            beamformed_vals = np.dot(s21_current,steering_vectors)/len(s21_current)
            
            #now pack into our CSA (CaluclateSynbteticAperture)
            csa_list.append(CalculatedSyntheticAperture(U,V,np.reshape(beamformed_vals,U.shape)))
        
        return csa_list
        #return csa_list,steering_vectors,s21_current,x_locs,y_locs,z_locs,delta_r
        


if __name__=='__main__':
    test_path = r".\\data\\2-13-2019\\binary_aperture_planar\\metafile_binary.json"
    #test_path = r".\\data\\2-13-2019\\binary_aperture_cylindrical\\metafile_binary.json"
    mysp = SamuraiBeamform(test_path)
    #azel without antenna
    #mycsa_list = mysp.beamforming_farfield(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
    #azel with antenna
    test_ant_path = './test_ant_pattern.csv'
    myant = Antenna(test_ant_path,dimension=1,plane='az')
    myap = myant['pattern']
    mycsa_list,ant_vals = mysp.beamforming_farfield(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True,antenna_pattern=myap)
    #UV beamform
    #mycsa_list = mysp.beamforming_farfield_uv(np.arange(-1,1.001,0.01),np.arange(-1,1.001,0.01),40e9,verbose=True)
    mycsa = mycsa_list[0]
    mycsa.plot_3d()