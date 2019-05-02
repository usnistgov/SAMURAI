# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""

import numpy as np #import constants
#import math #for vectorize math functions
import scipy.constants as sp_consts #import constants for speed of light
import scipy.interpolate as interp
import cmath #cmath for phase
from numba import vectorize
import six
import json

from samurai.analysis.support.metaFileController import MetaFileController 
from samurai.analysis.support.generic import incomplete,deprecated,verified
from samurai.analysis.support.snpEditor import SnpEditor

@deprecated("Change to utilize SamuraiSyntheticApertureAlgorithm class")
class SamuraiPostProcess(MetaFileController):
    '''
    @brief this is a class to inherit from for processing samurai data
        This will implement generic things like loading metadata used for all
        post-processing techniques. It currently inherits from metafile controller
    @todo add positional masking capability (masking functions, polygon, and manual points)
    '''
    def __init__(self,metafile_path, **arg_options):
        '''
        @brief initilization for class. We can load our metafile here or not
        @param[in] metafile_path - metafile if we want to load one now
        @param[in/OPT] arg_options - keyword arguments as follows. Also passed to MetaFileController from which we inherit
                        No keyword args yet!
        '''
        self.loaded_flg = False #whether data has been loaded to memory or not
        super(SamuraiPostProcess,self).__init__(metafile_path,arg_options) # load in our metafile
    
    def load_s_params_to_memory(self,verbose=False,load_key=21):
        '''
        @brief load S-parameter data into memory if it has not already been loaded
        @param[in/OPT] verbose - whether or not to be verbose
        @param[in/OPT] load_key - dictionary key for ports to load (default s21)
        @note this function sets the loaded_flg to true
        '''
        #load from files if not done already
        if not self.loaded_flg: #then we load
            [s_data,_] = self.load_data(verbose=verbose)
            self.loaded_data = s_data #store all of the data for if we change (may want to adjust this later for memory conservation)
            self.loaded_flg = True
        #now get the values we are looking for
        s_vals = np.array([s.S[load_key].raw for s in self.loaded_data]) #turn the s parameters into an array
        freq_list = self.loaded_data[0].S[load_key].freq_list #get frequencies from first file (assume theyre all the same)
        return freq_list,s_vals

#generic class for synthetic aperture algorithms
class SamuraiSyntheticApertureAlgorithm:
    '''
    @brief this is a generic class for samurai aglorithms.
    this should be completed and the rest of this restructured in the future
    This will allow a more generic things to work with such as importing measured vs. simed values
    '''
    def __init__(self,metafile_path=None,**arg_options):
        '''
        @brief initilaize the SamSynthApAlg class
        @param[in/OPT] metafile_path - metafile for real measurements (defaults to None)
        @param[in/OPT] arg_options - keyword arguments as follows. Also passed to MetaFileController from which we inherit
            verbose         - whether or not to be verbose (default False)
            antenna_pattern - AntennaPattern Class parameter to include (default None)
            measured_values_flg - are we using measurements, or simulated data (default True)
            load_key        - Key to load values from (e.g. 21,11,12,22) when using measured values (default 21)
        '''
        #options for the class
        self.options = {}
        self.options['verbose']         = False
        self.options['antenna_pattern'] = None
        self.options['measured_values_flg'] = True
        self.options['load_key']        = 21
        self.options['units']           = 'mm' #units of our position measurements (may want to load from metafile)
        for key,val in six.iteritems(arg_options):
            self.options[key] = val #set kwargs

        #initialize so we know if weve loaded them or not
        self.all_s_parameter_data = None #must be 2D array with axis 0 as each measurement and axis 1 as each position
        self.freq_list = None
        self.all_weights = None #weighting for our antennas
        self.all_positions = None #must be in list of [x,y,z,alpha,beta,gamma] points like on robot
        self.metafile = None
        if(metafile_path): #if theres a metafile load it
            self.load_metafile(metafile_path)

    def load_metafile(self,metafile_path,freq_mult=1e9):
        '''
        @brief function to load in our metafile and S parameter data from it
        @param[in] metafile_path - path to the metafile to load measurement from
        @param[in/OPT] freq_mult - how much to multiply the freq by to get hz (e.g. 1e9 for GHz)
        '''
        self.metafile = MetaFileController(metafile_path)
        [s_data,_] = self.metafile.load_data(verbose=self.options['verbose'])
        #now get the values we are looking for
        self.all_s_parameter_data = np.array([s.S[self.options['load_key']].raw for s in s_data]) #turn the s parameters into an array
        self.freq_list = s_data[0].S[self.options['load_key']].freq_list #get frequencies from first file (assume theyre all the same)
        self.freq_list = self.freq_list*freq_mult
        self.all_positions = self.metafile.get_positions()

    def validate_data(self):
        '''
        @brief ensure we have loaded all of the data to run the algorithm
        '''
        if np.any(self.positions==None) or len(self.positions)<1:
            raise(Exception("Positional data not provided"))
        if np.any(self.s_parameter_data==None) or len(self.s_parameter_data)<1:
            raise(Exception("S Parameter data not provided"))
        if np.any(self.freq_list==None) or len(self.freq_list)<1:
            raise(Exception("Frequency list not provided"))
        if np.any(self.weights==None) or len(self.weights)<1:
            raise(Exception("Weights not set"))
            
    def get_positions(self,units='m'):
        '''
        @brief check our units options and get our positions in a given unit
        @param[in/OPT] units - what units to get our positions in (default meters)
        @return return our position in whatever units specified (default meters)
        '''
        to_meters_dict={ #dictionary to get to meters
                'mm': 0.001,
                'cm': 0.01,
                'm' : 1,
                'in': 0.0254
                }
        
        #multiply to get to meters and divide to get to desired units
        multiplier = to_meters_dict[self.options['units']]/to_meters_dict[units] 
        return self.positions*multiplier
    
    def get_steering_vectors(self,az_u,el_v,k,coord='azel',**arg_options):
        '''
        @brief get our steering vectors with wavenumber provided. calculates np.exp(1j*k*kvec)
            where kvec is i_hat+j_hat+k_hat
            It is better to not use this for large calculations. Instead caculate the k vectors and get steering vectors in the algorithm
            to prevent recalculating k vectors
        @param[in] az_u - azimuth or u values to get steering vectors for 
        @param[in] el_v - elevatio nor v values to get steering vectors for
        @note az_u and el_v will be a pair list like from meshgrid. Shape doesnt matter. They will be flattened
        @param[in/OPT] k - wavenumber to calculate with. If None, vectors 
        @param[in/OPT] coord - what coordinate system our input values are (azel or uv) (default azel)
        @param[in/OPT] arg_options - keyword argument options as follows
            - None Yet!
        @return the steering vectors for az_u and el_v at the provided k value, or without a k value.
            The first axis of the returned matrix is the position value 
            The second axis corresponds to the azel values
        '''
        psv = self.get_partial_steering_vectors(az_u,el_v,coord,**arg_options)
        if not k:
            k=1 #default to 1
        steering_vectors = np.exp(-1j*k*psv)
        return steering_vectors
    
    def get_partial_steering_vectors(self,az_u,el_v,coord='azel',**arg_options):
        '''
        @brief get our partial steering vectors vector to later calculate the steering vector
            calculates i_hat+j_hat+k_hat dot position 
            (i.e. k_vectors*pos_vecs) and multiplies by position vectors
            To get steering vectors use np.exp(-1j*k*psv_vecs)
        @param[in] az_u - azimuth or u values to get steering vectors for 
        @param[in] el_v - elevatio nor v values to get steering vectors for
        @note az_u and el_v will be a pair list like from meshgrid. Shape doesnt matter. They will be flattened
        @param[in/OPT] coord - what coordinate system our input values are (azel or uv) (default azel)
        @param[in/OPT] arg_options - keyword argument options as follows
            - None Yet!
        @return the calculated partial steering vectors vectors for az_u and el_v at the provided k value, or without a k value.
            The first axis of the returned matrix is the position value 
            The second axis corresponds to the azel values
        '''
        #[az,el] = self.to_azel(az_u,el_v,coord) #change to azel
        #az = np.deg2rad(az.reshape((-1))) #flatten arrays along the desired axis and change to radians
        #el = np.deg2rad(el.reshape((-1)))
        #get and center our positions
        pos = self.get_positions('m')[:,0:3] # positions 4,5,6 are rotations only get xyz
        pos -= pos.mean(axis=0) #center around mean values
        
        #now calculate our steering vector values
        k_vecs = get_k_vectors(az_u,el_v,coord,**arg_options)
        psv_vecs = np.dot(pos,k_vecs) #this will multiply sv_vals by our x,y,z values and sum the three
        return psv_vecs
    
    def add_plane_wave(self,az_u,el_v,amplitude_db=-50,coord='azel'):
        '''
        @brief add a plane wave to the s parameter data.
            If data doesnt exist then start from 0s
        @param[in] az_u - azel (or uv) pairs of angles for plane waves
        @param[in] el_v - azel (or uv) pairs of angles for plane waves
        @param[in] amplitude_db - amplitude of the wave in dB (default -50)
        @param[in/OPT] coord - coordinate system to use (uv or azel) default azel
        '''
        if np.any(self.freq_list==None) or len(self.freq_list)<1:
            raise Exception("Freqeuncy list not defined (use obj.freq_list=freq_list)")
        if np.any(self.all_positions==None) or len(self.all_positions)<1:
            raise Exception("Positions not defined (use obj.all_positions=positions)")
        if np.any(self.s_parameter_data==None) or len(self.s_parameter_data)<1:
            self.all_s_parameter_data = np.zeros((self.all_positions.shape[0],len(self.freq_list)),dtype='complex128')
        #change to list
        if not hasattr(az_u,'__iter__'):
            az_u = [az_u]
        if not hasattr(el_v,'__iter__'):
            el_v = [el_v]
        [az,el] = to_azel(az_u,el_v,coord) #change to azel
        #check that the length is the same
        if len(az) != len(el):
            raise Exception("Input angle vectors must be the same length")
        #get linear amplitude (assume 10^(db/20))
        amplitude = 10**(amplitude_db/20)
        #now get our k vector values
        for fi,freq in enumerate(self.freq_list):
            sv = self.get_steering_vectors(az,el,get_k(freq)) #get the steering vector
            sv_sum = sv.sum(axis=1)*amplitude #sum across freqs and get our amplitude
            self.all_s_parameter_data[:,fi]+=sv_sum
    
    
    ### Here we definine some standard weighting window types ###
    def get_max_positions(self):
        '''
        @brief return maximum x,y,z coordinate values unmasked positions
        @return [x,y,z] coordinate in units given as self.options['units']
        '''
        return self.positions[:,:3].max(axis=0)
    
    def get_min_positions(self):
        '''
        @brief return minimum x,y,z coordinate values
        @return [x,y,z] coordinate in units given as self.options['units']
        '''
        return self.positions[:,:3].min(axis=0)
    
    def get_rng_positions(self):
        '''
        @brief return range x,y,z coordinate values
        @return [x,y,z] coordinate in units given as self.options['units']
        '''
        return self.positions[:,:3].ptp(axis=0)
        
    def set_sine_window(self):
        '''
        @brief set our weights to reflect a sine window
        '''
        mins = self.get_min_positions()
        rng  = self.get_rng_positions()
        #this follows the equation sin(pi*n/N)
        #N is our range n is our position minus our min
        N = rng
        n = self.positions[:,:3]-mins
        vals = np.divide(np.pi*n, N, out=np.ones_like(n)*np.pi/2, where=N!=0) #take care of where N=0 (planar arrays)
        self.weights = np.sin(vals).prod(axis=1) #now take the sine
    
    def set_sine_power_window(self,power):
        '''
        @brief set our weights to reflect a sine power window
            Hann window is power=2
        @param[in] power - power to set the sine to (e.g. power=2 produces sin(pi*n/N)**2)
        '''
        mins = self.get_min_positions()
        rng  = self.get_rng_positions()
        #this follows the equation sin(pi*n/N)
        #N is our range n is our position minus our min
        N = rng
        n = self.positions[:,:3]-mins
        vals = np.divide(np.pi*n, N, out=np.ones_like(n)*np.pi/2, where=N!=0) #take care of where N=0 (planar arrays)
        vals = np.sin(vals)**power #now take the sine
        self.weights = vals.prod(axis=1)
        
    def set_cosine_sum_window(self,coeffs):
        '''
        @brief set our weights for a generalized cosine sum window
        @param[in] coeffs - list of coefficients for a0,a1,a2,...,etc. can be any length
        '''
        mins = self.get_min_positions()
        rng  = self.get_rng_positions()
        coeffs=np.array(coeffs)
        if np.round(coeffs.sum(),10) != 1:
            raise Exception("Coefficients do not add to 1 (they add to %f)" %coeffs.sum())
        #this follows the equation sin(pi*n/N)
        #N is our range n is our position minus our min
        N = rng
        n = self.positions[:,:3]-mins
        cos_mults = (np.arange(len(coeffs)-1)+1) #k=1,2,3,4,...,etc
        cm = cos_mults.reshape((1,1,-1))
        num = 2*np.pi*cm*n[:,:,np.newaxis]
        den = N.reshape(1,-1,1)
        vals = np.divide(num, den, out=np.ones_like(num)*np.pi, where=den!=0)
        cf0 = coeffs[0]
        coeffs = coeffs[1:].reshape((1,1,-1))
        vals = (-1)**(cm)*np.cos(vals)*coeffs #a1cos(2pn/N),a2cos(4pin/N)
        vals=vals.sum(axis=2)+cf0 #a0+a1cos(2pn/N)+a2cos(4pin/N)
        self.weights=vals.prod(axis=1)
        
        
    def set_cosine_sum_window_by_name(self,name):
        '''
        @brief set the cosine sum window by a name
        @param[in] name - name of filter ('hann','hamming','blackman','nutall',
                      'blackman-nutall','blackman-harris','flat-top')
        @note these coefficient values are taken from wikipedia
        '''
        coeff_dict = {
                'hann'            :[0.5,0.5],
                'hamming'         :[25/46,1-(25/46)],
                'blackman'        :[7938/18608,9240/18608,1430/18608],
                'nutall'          :[0.355768,0.487396,0.144232,0.012604],
                'blackman-nutall' :[0.3635819,0.4891775,0.1365995,0.0106411],
                'blackman-harris' :[0.35875,0.48829,0.14128,0.01168],
                'flat-top'        :[0.21557895,0.41663158,0.277263158,0.083578947,0.006947368],
                }
        coeffs = coeff_dict[name.lower()]  #get the coeffs
        self.set_cosine_sum_window(coeffs) #set the values
        
        
    def set_binomial_window(self):
        '''
        @brief set a binomial window on the data
        @todo implement this...
        '''
        pass
    
    def reset_window(self):
        '''
        @brief reset our window to all equal weighting (i.e. no windowing)
        '''
        self.weights = np.ones(self.positions.shape[0])
            
    def plot_positions(self,pos_units='m',plot_type='weights',**arg_options):
        '''
        @brief plot the positions of our aperture in 3D
            points will be colored based on the plot type
        @param[in/OPT] pos_units - units for position (m,mm,cm,in)
        @param[in/OPT] plot_type - whether to plot 'weights','mag','phase','phase_d','real','imag'
        @param[in/OPT] **arg_options - keyword args as follows 
                out_name - plot output name (for plotly)
                freq_point - which s-parameter frequency point to plot (default 0)
        '''
        options = {}
        options['out_name'] = 'positions_plot.html'
        options['freq_point'] = 0
        for key,val in six.iteritems(arg_options):
            options[key] = val
        fp = options['freq_point']
        #get our data 
        plot_data_dict = {
            'weights':self.weights,
            'mag_db':lambda: 20*np.log10(np.abs(self.s_parameter_data[:,fp])),
            'mag':lambda: np.abs(self.s_parameter_data[:,fp]),
            'phase':lambda: np.angle(self.s_parameter_data[:,fp]),
            'phase_d':lambda: np.angle(self.s_parameter_data[:,fp])*180/np.pi,
            'real':lambda: np.abs(self.s_parameter_data[:,fp]),
            'imag':lambda: np.abs(self.s_parameter_data[:,fp])
            }
        plot_data =  plot_data_dict[plot_type]#use phase at first frequency
        pos = self.get_positions(pos_units)
        #now get our xyz values
        X = pos[:,0]
        Y = pos[:,1]
        Z = pos[:,2]
        #and plot
        plotly_surf = [go.Scatter3d(z = Z, x = X, y = Y,
                                    mode = 'markers',
                                    marker = dict(
                                            color=plot_data,
                                            colorbar=dict(title='Phase (degrees)')
                                            )
                                    )]
        layout = go.Layout(
            title='Aperture Positions',
            scene = dict(
                xaxis = dict(title='X'),
                yaxis = dict(title='Y'),
                zaxis = dict(title='Z')
            ),
            autosize=True,
            margin=dict(l=65,r=50,b=65,t=90),
        )
        fig = go.Figure(data=plotly_surf,layout=layout)
        ploff.plot(fig,filename=options['out_name'])
    
    
    @property
    def positions(self):
        '''
        @brief getter for our positinos. This will allow us to mask out undesired locations
        @return all desired positions that are not masked out
        @todo implemment masking
        '''
        if self.metafile["positioner"]=='maturo':
            #then finangle the positions to match the meca
            z = self.all_positions[:,0]
            y = self.all_positions[:,3]
            x = np.zeros_like(z)
            alph = np.zeros_like(z)
            beta = np.zeros_like(z)
            gamm = np.zeros_like(z)
            self.options['units']='cm'
            pos = np.stack([x,y,z,alph,beta,gamm],axis=1)
        else:
            #otherwise we are using the meca
            pos = self.all_positions
        return pos
    
    @property
    def s_parameter_data(self):
        '''
        @brief getter for our s parameter data. This will allow us to mask out undesired locations
        @return all s_parameter_data for desired positions that are not masked out
        @todo implemment masking
        '''
        return self.all_s_parameter_data
    
    @property
    def weights(self):
        '''
        @brief getter for our antenna weights
        @return all weighting values for desired positions that are not masked out
        @todo implemment masking
        '''
        if np.any(self.all_weights==None) or len(self.all_weights)<1:
            return np.ones(self.positions.shape[0])
        else:
            return self.all_weights
    @weights.setter
    def weights(self,weights):
        '''
        @brief setter for our antenna weights
            for now these weights will be for just our values in use (masking doesnt effect)
            This means weights will need to be recalculated when masking is done
        @param[in] weights - weights to set
        @todo implemment masking
        '''
        self.all_weights = weights
        
def to_azel(az_u,el_v,coord,replace_val = np.nan):
    '''
    @brief change a provided coordinate system ('azel' or 'uv') to azel
    @param[in] az_u list of azimuth or u values
    @param[in] el_v list of azimuth or v values
    @param[in] coord - what coordinate system our input values are
    @param[in/OPT] replace_val - value to replace uv outside of radius 1 with (default is nan)
    @return lists of [azimuth,elevation] values
    '''
    if(coord=='azel'):
        azimuth = az_u
        elevation = el_v
    elif(coord=='uv'):
        l1_vals = np.sqrt(az_u**2*el_v**2)<1
        az_u[l1_vals] = np.nan
        el_v[l1_vals] = np.nan
        azimuth = np.rad2deg(np.arctan2(az_u,np.sqrt(1-az_u**2-el_v**2)))
        elevation = np.rad2deg(np.arcsin(el_v))
    return np.array(azimuth),np.array(elevation)
 
def get_k_vectors(az_u,el_v,coord='azel',**arg_options):
    '''
    @brief get our k vector to later calculate the steering vector
        calculates i_hat+j_hat+k_hat 
        To get steering vectors use np.exp(-1j*k*dot(k_vectors*position_vectors))
    @param[in] az_u - azimuth or u values to get k vecs for
    @param[in] el_v - elevatio nor v values to get k vecs for
    @note az_u and el_v will be a pair list like from meshgrid. Shape doesnt matter. They will be flattened
    @param[in/OPT] coord - what coordinate system our input values are (azel or uv) (default azel)
    @param[in/OPT] arg_options - keyword argument options as follows
        - None Yet!
    @return the calculated k vectors for az_u and el_v at the provided k value, or without a k value.
        The first axis of the returned matrix is the x,y,z components respectively
        The second axis is each of the measurements from the input az_u,el_v
    '''
    az = np.deg2rad(az_u.flatten())
    el = np.deg2rad(el_v.flatten())
    #now calculate our steering vector values
    k_vecs = np.array([
            np.cos(el)*np.cos(az), #propogation direction (X)
            np.cos(el)*np.sin(az), #side to side (Y)
            np.sin(el) #up and down (Z)
            ])
    return k_vecs

def get_k(freq,eps_r=1,mu_r=1):
    cr = sp_consts.speed_of_light/np.sqrt(eps_r*mu_r)
    lam = cr/freq
    k = 2*np.pi/lam
    return k
    
#import matplotlib.pyplot as plt
#from matplotlib import cm
#from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objs as go
import plotly.offline as ploff
        
class CalculatedSyntheticAperture:
    '''
    @brief this class provides a container for calculated synthetic aperture values
        Here we have things such as our theta,phi meshgrid, our u,v meshgrid, and our complex values
        It also contains methods to nicely plot each of these values.
        This will be a single beamformed setup
    '''
    def __init__(self,AZIMUTH,ELEVATION,complex_values=np.array([]),freqs=np.array([]),**arg_options):
        '''
        @brief intializer for the class. This can be initialized without any data and 
                        just use the self.add_frequency_data() method
        @param[in] AZIMUTH   - meshgrid output of AZIMUTH angles   (azimuth from x) (2D)
        @param[in] ELEVATION - meshgrid output of ELEVATION angles (elevation up from xy plane) (2D)
        @param[in/OPT] complex_values - values corresponding to a direction [THETA[i,j],PHI[i,j]]
        @param[in/OPT] freqs - list of frequencies (if we are storing multiple)
        @param[in/OPT] arg_options - optional input keyword arguments as follows:
                -None yet
        @return CalculatedSyntheticAperture class
        '''
        self.options = {}
        AZ = np.array(AZIMUTH)
        EL = np.array(ELEVATION)
        if(AZ.shape != EL.shape):
            raise Exception("Azimuth and Elevation meshgrids must be the same size")
        self.elevation = EL
        self.azimuth   = AZ
        self.complex_values = np.array([])
        self.freq_list = np.array([])
        if complex_values.size>0 and freqs.size>0: #populate data if provided
            self.add_frequency_data(complex_values,freqs)
        
    def add_frequency_data(self,complex_values,freqs):
        '''
        @brief add data for a frequency or frequencies
        @param[in] complex_values - array of complex values for each frequency (pointing angle dim 0 and 1, freq dim 2)
                Dimension 0,1 of this array must match the length of the self.azimuth and self.elevation
        @param[in] freqs - list of frequencies to append (1D array)
        '''
        if not hasattr(freqs,'__iter__'):
            freqs = [freqs]
        #append our data and frequencies
        freqs = np.array(freqs)
        cv = np.array(complex_values)
        #now sort and add dimensions
        if cv.ndim<3:
            cv = cv[:,:,np.newaxis]
        #sort the input
        sort_ord = np.argsort(freqs)
        freqs = freqs[sort_ord]
        cv = cv[:,:,sort_ord]
        #now insert in sorted order
        in_ord = np.searchsorted(self.freq_list,freqs)
        if cv.shape[:2] != self.elevation.shape: #ensure shaping is correct
            raise Exception("Complex data must be the same shape as the input angles meshgrid")
        if self.complex_values.size<1: #if its the first data, make it the right size
            self.complex_values = cv
        else: #else append
            self.complex_values = np.insert(self.complex_values,in_ord,cv,axis=2)
        self.freq_list = np.insert(self.freq_list,in_ord,freqs)
        
        
    
    def plot_azel(self,plot_type='mag_db',out_name='test'):
        '''
        @brief plot calculated data in azimuth elevation
        @param[in] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] out_name - name of output plot (plotly)
        @return a handle for the figure
        '''
        plot_data = self.get_data(plot_type)
        
        
        #fig = plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #ax.plot_surface(self.elevation,self.AZIMUTH,plot_data,cmap=cm.coolwarm,
        #               linewidth=0, antialiased=False)

        plotly_surf = [go.Surface(z = plot_data, x = self.azimuth, y = self.elevation)]
        layout = go.Layout(
            title='UV Beamformed Plot',
            scene = dict(
                xaxis = dict(title='$\phi$ (Azimuth)'),
                yaxis = dict(title='$theta$ (Elevation)'),
                zaxis = dict(title='Beamformed value (%s)' %(plot_type))
            ),
            autosize=True,
            margin=dict(
                l=65,
                r=50,
                b=65,
                t=90
            )
        )
        fig = go.Figure(data=plotly_surf,layout=layout)
        ploff.plot(fig,filename=out_name)

        # Customize the z axis.
        #ax.set_zlim(-1.01, 1.01)
        #ax.zaxis.set_major_locator(LinearLocator(10))
        #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        
        # Add a color bar which maps values to colors.
        #fig.colorbar(surf, shrink=0.5, aspect=5)
        return fig
    
    def plot_uv(self,plot_type='mag_db',out_name='test'):
        '''
        @brief plot calculated data in uv space
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] out_name - name of output plot (plotly)
        @return a handle for the figure
        '''
        plot_data = self.get_data(plot_type)
        U = np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        V = np.sin(np.deg2rad(self.elevation))
        #[Un,Vn,Dn] = increase_meshing_3D(U,V,plot_data,4)
        Un = U
        Vn = V
        Dn = plot_data
        
        #plt_mask = np.isfinite(Dn.flatten())
        #mv = np.nanmin(Dn,-1).mean()
        #fig = plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #ax.plot_surface(Un,Vn,mask_value(Dn,plt_mask,mv)
        #    ,cmap=cm.summer,linewidth=0, antialiased=False)
        #ax.set_xlabel("U (Azimuth)")
        #ax.set_ylabel("V (Elevation)")
        
        ##### Plotly #####
        plotly_surf = [go.Surface(z = Dn, x = Un, y = Vn)]
        layout = go.Layout(
            title='UV Beamformed Plot',
            scene = dict(
                xaxis = dict(
                    title='U (Azimuth)'),
                yaxis = dict(
                    title='V (Elevation)'),
                zaxis = dict(
                    title='Beamformed value (%s)' %(plot_type))),
            autosize=True,
            margin=dict(
                l=65,
                r=50,
                b=65,
                t=90
            )
        )
        fig = go.Figure(data=plotly_surf,layout=layout)
        ploff.plot(fig,filename=out_name)
            
        
    def plot_3d(self,plot_type='mag_db',out_name='aperture_results_3d.html'):
        '''
        @brief plot calculated data in 3d space (radiation pattern)
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @return a handle for the figure
        '''
        plot_data = self.get_data(plot_type)
        [plot_data,caxis_min,caxis_max,db_range] = self.adjust_caxis(plot_data,plot_type,60)
        
        #now get our xyz values
        X = plot_data*np.cos(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
        Y = plot_data*np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        Z = plot_data*np.sin(np.deg2rad(self.elevation))
        
        #and plot
        plotly_surf = [go.Surface(z = Z, x = X, y = Y,surfacecolor=plot_data,
                                  colorbar=dict(
                                            title=plot_type,
                                            tickvals=[0,db_range],
                                            ticktext=[str(round(caxis_min,2)),str(round(caxis_max,2))]
                                            ))]
        layout = go.Layout(
            title='Beamformed Data (%s)' %(plot_type),
            scene = dict(
                xaxis = dict(title='X'),
                yaxis = dict(title='Y'),
                zaxis = dict(title='Z')
            ),
            autosize=True,
            margin=dict(
                l=65,
                r=50,
                b=65,
                t=90
            ),
        )
        fig = go.Figure(data=plotly_surf,layout=layout)
        ploff.plot(fig,filename=out_name)
       
        
    def plot_scatter_3d(self,plot_type='mag_db',out_name='test'):
        '''
        @brief scatter plot calculated data in 3d space (radiation pattern)
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @return a handle for the figure
        '''
        
        #get our data
        plot_data = self.get_data(plot_type)
        [plot_data,caxis_min,caxis_max,db_range] = self.adjust_caxis(plot_data,plot_type,60)
        
        #now get our xyz values
        X = plot_data*np.cos(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
        Y = plot_data*np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        Z = plot_data*np.sin(np.deg2rad(self.elevation))
        
        #and plot
        plotly_surf = [go.Scatter3d(z = Z, x = X, y = Y,
                                    mode = 'markers',
                                    marker = dict(
                                            color=plot_data,
                                            colorbar=dict(
                                                title=plot_type,
                                                tickvals=[0,db_range],
                                                ticktext=[str(round(caxis_min,2)),str(round(caxis_max,2))]
                                                )
                                            )
                                    )]
        layout = go.Layout(
            title='Beamformed Data (%s)' %(plot_type),
            scene = dict(
                xaxis = dict(title='X'),
                yaxis = dict(title='Y'),
                zaxis = dict(title='Z')
            ),
            autosize=True,
            margin=dict(
                l=65,
                r=50,
                b=65,
                t=90
            ),
        )
        fig = go.Figure(data=plotly_surf,layout=layout)
        ploff.plot(fig,filename=out_name)
        
        #fig = plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #ax.plot_surface(X,Y,Z,cmap=cm.coolwarm,
        #               linewidth=0, antialiased=False)
    
    def get_data(self,data_str,freqs='all'):
        '''
        @brief get the desired data from a string (e.g. 'mag_db','phase_d','mag', etc.)
            this can also be used to select which frequencies to average
        @param[in] data_str - string of the data to get. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] freqs - which frequencies to average (default 'all'). if the freq doesnt exist, throw an exception
        @return np array of shape self.azimuth (or elevation) with the mean s parameters from the provided frequencies
        '''
        data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag
            }
        freq_idx = self.get_freq_idx(freqs)
        data = data_dict[data_str]
        data = data[:,:,freq_idx]
        return np.mean(data,axis=2)
        
    def get_freq_idx(self,freqs):
        '''
        @brief get the index of the frequeny provided
            'all' will return all indexes
        @param[in] freqs to get indices of ('all' returns all)
        '''
        if freqs=='all':
            freqs = self.freq_list
        if not hasattr(freqs,'__iter__'):
            freqs = [freqs]
        freqs = np.array(freqs)
        idx = np.array([],dtype=np.int)
        for f in freqs:
            loc = np.where(self.freq_list==f)
            if len(loc)!=1:
                raise Exception("Frequency %f is not in the list or is repeated in the list" %(f))
            idx = np.append(idx,loc[0][0])
        return idx
    
    def adjust_caxis(self,plot_data,plot_type,db_range=60,**arg_options):
        '''
        @brief adjust our plotting values for a colorbar axis.
            This ensures we dont have negative values in 3D plotting.
            This is really important to use for mag_db plots. Everything else
            will just be shifted to 0
        @param[in] plot_data - data we are plotting
        @param[in] plot_type - type of data we are plotting (e.g. 'mag_db','mag','real',etc.)
        @param[in/OPT] db_range  - dynamic range of our plot in db (only important for mag_db default 60)
        @param[in/OPT] arg_options - kyeworkd option arguments:
            - None Yet!
        @return new_plot_data, caxis_min, caxis_max, db_range - our new data, our miinimum colorbar value, our max colorbar value
        '''
        if(plot_type=='mag_db'):
            #mask out lower values
            db_range = 60 #lower than the max
            caxis_min = np.nanmax(plot_data)-db_range
            caxis_max = np.nanmax(plot_data)
            new_plot_data = plot_data-(np.nanmax(plot_data)-db_range) #shift the values
            new_plot_data = mask_value(new_plot_data,new_plot_data<=0)
        else: 
            #Zero the data
            caxis_min = np.nanmin(plot_data)
            caxis_max = np.nanmax(plot_data)
            new_plot_data = plot_data-np.nanmin(plot_data)
        return new_plot_data,caxis_min,caxis_max,db_range
    
    def write_snp_data(self,out_dir,**arg_options):
        '''
        @brief write out our frequencies over our angles into s2p files 
            s21,s12 will be our complex values, s11,s22 will be 0.
            Files will be written out as 'beamformed_<number>.snp'.
            A json file (beamformed.json) will also be written out
            giving the azimuth elevation values.
        @param[in] out_dir - output directory to save the files
        @param[in/OPT] arg_options - keyword args as follows:
                -None Yet!
        @return list of SnpEditor classes with the data written out
        '''
        #loop through all of our positions
        meas_info = []
        meas_data = [] #values for returning
        freqs = self.freq_list/1e9 #freqs in ghz
        for i in range(self.num_positions):
            cur_idx = np.unravel_index(i,self.azimuth.shape)
            az = self.azimuth[cur_idx]
            el = self.elevation[cur_idx]
            #assume our freq_list is in hz then write out in GHz
            mys = SnpEditor([2,freqs],comments=['azimuth = '+str(az)+' degrees','elevation = '+str(el)+' degrees'],header='GHz S RI 50') #create a s2p file
            #populate the s21,values
            mys.S[21].update(freqs,self.complex_values[cur_idx])
            mys.S[12].update(freqs,self.complex_values[cur_idx])
            #now save out
            out_name = 'beamformed_'+str(i)+'.s2p'
            out_path = os.path.join(out_dir,out_name)
            mys.write(out_path)
            meas_data.append(mys)
            meas_info.append({'filepath':out_path,'azimuth':float(az),'elevation':float(el)})
        with open(os.path.join(out_dir,'beamformed.json'),'w+') as fp:
            json.dump(meas_info,fp)
        return meas_data
        
    @property
    def mag_db(self):
        '''
        @brief get the maginutude in db of our values. This uses 20*log10(val)
        '''
        return 20*np.log10(self.mag)
    
    @property
    def mag(self):
        '''
        @brief get our data values magnitude (average across freqs)
        '''
        return np.abs(self.complex_values)
        
    @property
    def phase(self):
        '''
        @brief get our data values phase in radians
        '''
        return np.angle(self.complex_values)
    
    @property
    def phase_d(self):
        '''
        @brief get our data values phase in degrees
        '''
        return np.angle(self.complex_values)*180./np.pi
    
    @property
    def real(self):
        '''
        @brief get real part of the data
        '''
        return self.complex_values.real
    
    @property
    def imag(self):
        '''
        @brief get real part of the data
        '''
        return self.complex_values.imag
    
    @property
    def PHI(self):
        '''
        @brief alias for returning azimuth meshgrid (same thing as phi)
        '''
        return self.azimuth
    
    @PHI.setter
    def PHI(self,vals):
        '''
        @brief alias for setting azimuth meshgrid (same thing as phi)
        '''
        self.azimuth = vals
    
    @property
    def THETA(self):
        '''
        @brief alias for returning elevation meshgrid (same thing as theta)
        '''
        return self.elevation
    
    @THETA.setter
    def THETA(self,vals):
        '''
        @brief alias for setting elevation meshgrid (same thing as theta)
        '''
        self.elevation = vals
        
    @property
    def U(self):
        '''
        @brief get our U grid values from our angles
        '''
        return np.sin(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
    
    @property
    def V(self):
        '''
        @brief get our V grid values from our angles
        '''
        return np.sin(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
    
    @property
    def num_positions(self):
        '''
        @brief get our number of positions (from azimuth values)
        '''
        return self.azimuth.size


from collections import OrderedDict
#import numpy as np

class Antenna(OrderedDict):
    '''
    @brief class to store all information about an antenna (including pattern info)
    '''
    
    def __init__(self,pattern_file_path=None,**antenna_info):
        '''
        @brief initialize antenna
        @param[in/OPT], pattern_file_path - path to load pattern from (default None)
        @param[in/OPT] antenna_info - dicitonary (or kwarg) info about antenna
        '''
        #some default values
        self['name']          = 'generic'
        self['serial_number'] = 'XXXX-XX'
        self['gain_dbi']      = 0
        self['beamwidth_e']   = np.inf
        self['beamwidth_h']   = np.inf
        self['pattern']       = {}
        #update antenna info
        self.update(antenna_info)
        #now load file if given
        self.antenna_pattern = None #set to none in case one isnt given
        if(pattern_file_path):
            self.load_pattern(pattern_file_path,**antenna_info)
            
    def load_pattern(self,pattern_file_path,**antenna_info):
        '''
        @brief load an antenna pattern from a file
        @param[in] pattern_file_path - pattern file to load. For more information see AntennaPattern.load()
        '''
        self['pattern'] = AntennaPattern(pattern_file_path,**antenna_info)
        

import os
import re
    
class AntennaPattern(CalculatedSyntheticAperture):
    '''
    @brief class to hold antenna pattern values
        This inherits from CalculatedSyntheticAperture class
        which provides many methods we want except the loading
    '''
    def __init__(self,pattern_file,**arg_options):
        '''
        @brief class constructor
        @param[in] pattern file - file to load the pattern from
        @param[in/OPT] keyword args as follows:
            dimension - dimension of the loaded file (1D for single cut or 2D for full pattern)
            plane     - plane of 1D cut ('az' or 'el' only required for 1D cut)
        '''
        self.load(pattern_file,**arg_options)
    
    def load(self,pattern_file,**arg_options):
        '''
        @brief method to load pattern data from a file
            Currently the following filetypes are supported:
                --- CSV ---
                comma separated value files with the format
                'azimuth, elevation, value (complex)' are supported
        @param[in] pattern_file - file to load
        @param[in/OPT] keyword args as follows:
                dimension - dimension of the loaded file (1D for single cut or 2D for full pattern)
                plane     - plane of 1D cut ('az' or 'el' only required for 1D cut)
                grid      - grid increment to fit to in degrees. 
                    This data will be fit to a grid for finding our values. Defaults to 1 degree
        @return [azimuth,elevation,values(complex)]
        '''
        #our options
        options = {}
        options['dimension'] = 2 #default to 2D pattern (full spherical pattern)
        options['plane']     = None
        options['grid']      = 1 #interp to 1 degree grid
        for key,val in six.iteritems(arg_options): #get input options
            options[key] = val
        self.grid_degrees = options['grid']
        #now load the file
        file_ext = os.path.splitext(pattern_file)[-1]
        load_functs = {
                '.csv':self.load_csv
                }
        load_funct = load_functs[file_ext]
        [az,el,vals] = load_funct(pattern_file)
        self.type = {'dimension':options['dimension'],'plane':options['plane']}
        [az,el,vals] = self.interp_to_grid(az,el,vals) #interp to our grid
        super(AntennaPattern,self).__init__(az,el,vals) #init the superclass
    
    def load_csv(self,pattern_file):
        '''
        @brief method to load pattern data from CSV 
            data should be in the format 'azimuth, elevation, real(value),imag(value)'
            all angles should be in degrees with 0,90=az,el pointing boresight
            all field values should be E fields (20*log10(val) for dB)
        @param[in] pattern_file - file to load
        @return [azimuth,elevation,values(complex)]
        '''
        with open(pattern_file,'r') as fp: 
            for line in fp:
                if(line.strip()[0]=='#'):
                    self.options['header'].append(line.strip()[1:])
                elif(line.strip()[0]=='!'):
                    self.options['comments'].append(line.strip()[1:])
                else: #else its data
                    pass     
        #now read in data from the file with many possible delimiters in cases
        #of badly formated files
        with open(pattern_file) as fp:
            regex_str = r'[ ,|\t]+'
            rc = re.compile(regex_str)
            raw_data = np.loadtxt((rc.sub(' ',l) for l in fp),comments=['#','!'])                  
                                  
        return [raw_data[:,0],raw_data[:,1],raw_data[:,2]+raw_data[:,3]*1j]
    
    def interp_to_grid(self,az,el,vals):
        '''
        @brief interpolate our input pattern to a grid
        @param[in] az - azimuth locations of values
        @param[in] el - elevation locations of values
        @param[in] vals - list of corresponding complex values
        @return [interp_az,interp_el,interp_vals] - list of our interpolated values interpolated to self.grid_degrees
        '''
        if(self.type['dimension']==1): #1D interp using griddata
            new_pts = np.arange(-180,180+self.grid_degrees,self.grid_degrees) #build our values in our dimensino given (az or el)
            static_pts = np.zeros(new_pts.shape) #make a zero vector for our other values
            pts_dict = {
                'az':az,
                'el':el
            }
            pts = pts_dict[self.type['plane']] #get the points to interpolate (elevation or azimuth)
            new_vals = interp.griddata(pts,vals,new_pts,fill_value=np.mean([vals[0],vals[-1]])) #interpolate (fill with min of pattern)
            #now write out correctly
            if(self.type['plane']=='el'): #elevation cut
                new_el = new_pts
                new_az = static_pts
            else: #else azimuth cut
                new_el = static_pts
                new_az = new_pts
                
        else:
            raise ReferenceError("Dimension argument not implemented")

        return [new_az,new_el,new_vals]

    def get_values(self,az_u,el_v,coord='azel'):
        '''
        @brief get list of values from our antenna pattern
        @param[in] az_u - azimuth or u coord to get pattern value
        @param[in] el_v - elevation or v coord to get pattern value
        @param[in] coord - type of system 'azel' or 'uv' (currently only 'azel' supported)
        @todo - implement 'uv' coordinates
        @return list of linear complex values at the angles specified
        '''
        #first get the function on whether its 1D or 2D data
        getter_dict = {
            1:self.get_values_1D,
            2:self.get_values_2D
        }
        getter_funct = getter_dict[self.type['dimension']]
        #perform uv2azel conversion here
        az = az_u
        el = el_v
        #wrap to ensure -180 to 180 degrees
        az = np.mod(az+180,360)-180
        el = np.mod(el+180,360)-180
        return getter_funct(az,el) #return our values

    
    def get_values_1D(self,az,el):
        '''
        @brief get list of values for a 1D pattern ONLY supports azel
        @param[in] az - list of azimuth values to get
        @param[in] el - list of elevation values to get
        '''
        #here we are going to find the plane
        search_vals_dict = {
            'az': [self.azimuth,az],
            'el': [self.elevation,el]
        }
        [search_vals,in_vals] = search_vals_dict[self.type['plane']] #values to find indexes for
        #THIS ASSUMES AZIMUTH AND ELEVATION VALUES ARE SORTED LO to HI and GRIDDED to self.grid_degrees!!!
        min_val = search_vals.min() #get minimum of our angles to index from
        idx_vals = np.round((in_vals-min_val)/self.grid_degrees).astype(int) #this should give us our indices
        vals = self.complex_values[idx_vals]
        return vals

    @incomplete("Not at all implemented right now")
    def get_values_2D(self,az,el):
        '''
        @brief get a list of values for a 2D pattern ONLY supports azel
        @param[in] az - list of azimuth values to get
        @param[in] el - list of elevation values to get
        @todo IMPLEMENT
        '''
        return []
    
@vectorize(['complex128(float64,float64)'],target='cpu')
def calculate_steering_vector(k_vector,k):
    return cmath.exp(-1j*k*k_vector)

#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
#ax.plot_surface(X,Y,np.angle(sv[:,1830].reshape(X.shape)))
#ax.plot_surface(y.reshape((35,35)),z.reshape((35,35)),(np.angle(s21.reshape(X.shape))))
# ax.plot_surface(y.reshape((35,35)),z.reshape((35,35)),dr[:,10000].reshape(35,35))
    
def mask_value(arr,mask,value=0):
    '''
    @brief replace values in ndarray from mask
    @param[in] arr   - array to mask
    @param[in] mask  - masking values (these values will be changed)
    @param[in] value - value to exchange for (if none delete)
    '''
    mask = mask.flatten()
    shape = arr.shape #original size
    af = arr.flatten()
    af[mask] = value
    rv = np.reshape(af,shape)
    return rv

    
if __name__=='__main__':
    
    #test_ant_path = './data/test_ant_pattern.csv'
    #myant = Antenna(test_ant_path,dimension=1,plane='az')
    #myap = myant['pattern']
    #print(myap.type)
    #myap.plot_scatter_3d()
    #myant['pattern'].plot_scatter_3d()
    #print(myap.get_values([0,0.5,1,45,-45],[0,0,0,0,0]))
    
    #some unit tests
    import unittest
    class TestSamuraiPostProcess(unittest.TestCase):   
        #def test_to_azel(self):
        #    self.assertEqual('foo'.upper(),'FOO')
        def test_k_vector_calculation_azel(self):
            #ssaa = SamuraiSyntheticApertureAlgorithm()
            #ssaa.all_positions = np.random.rand(1225,3)*0.115 #random data points between 0 and 0.115m
            az_angles = np.arange(-90,90,1)
            el_angles = np.arange(-90,90,1)
            [AZ,EL] = np.meshgrid(az_angles,el_angles)
            az = AZ.flatten()
            el = EL.flatten()
            kvecs = get_k_vectors(az,el)
            kr = np.sqrt(kvecs[0]**2+kvecs[1]**2+kvecs[2]**2) #r should be 1
            self.assertTrue(np.all(np.round(kr,2)==1),'K Vector radius mean = %f' %kr.mean())
    unittest.main()
            
    
    
    
    
    
    