"""
Created on Mon Apr 23 11:02:53 2018
music algorithm for samurai data
@author: ajw5
"""
from samurai.analysis.support.SamuraiPostProcess import SamuraiSyntheticApertureAlgorithm
from samurai.analysis.support.SamuraiPostProcess import to_azel,get_k
from samurai.analysis.support.SamuraiPostProcess import CalculatedSyntheticAperture
from samurai.analysis.support.SamuraiPostProcess import Antenna
import numpy as np #import constants


class SamuraiMusic(SamuraiSyntheticApertureAlgorithm):
    '''
    @brief samurai synthetic aperture using music
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
        super(SamuraiMusic,self).__init__(metafile_path,**arg_options)
        
        
    def music_base(self,az_u,el_v,freq_list='all',coord='azel',**arg_options):
        '''
        @brief base of the music algorithm
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
        mycsa = CalculatedSyntheticAperture(azimuth,elevation)
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
#            lam = sp_consts.c/freq
#            k = 2.*np.pi/lam
            k = get_k(freq)
            steering_vectors = np.exp(1j*k*psv_vecs)

            # sum(value_at_position*steering_vector) for each angle
            # now calculate the values at each angle
            beamformed_vals = np.dot(s21_current*self.weights,steering_vectors/antenna_values)/self.weights.sum()
            
            #now pack into our CSA (CaluclateSynbteticAperture)
            mycsa.add_frequency_data(np.reshape(beamformed_vals,azimuth.shape),freq)
            #csa_list.append(CalculatedSyntheticAperture(azimuth,elevation,np.reshape(beamformed_vals,azimuth.shape)))
        
        ant_vals = CalculatedSyntheticAperture(azimuth,elevation,np.reshape(antenna_values[1,:],azimuth.shape))

        return mycsa,ant_vals
    
    
    