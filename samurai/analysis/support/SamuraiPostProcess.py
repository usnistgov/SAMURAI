# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""

import numpy as np #import constants
#import math #for vectorize math functions
import scipy.special #for RectangularHorn
#import scipy.interpolate as interp
import six
import os
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
#import json

from samurai.analysis.support.MetafileController import MetafileController 
from samurai.base.SamuraiDict import SamuraiDict
#from samurai.analysis.support.generic import incomplete,deprecated,verified
#from samurai.analysis.support.generic import round_arb
#from samurai.analysis.support.snpEditor import SnpEditor
#from samurai.analysis.support.MatlabPlotter import MatlabPlotter
#from samurai.acquisition.support.samurai_apertureBuilder import v1_to_v2_convert #import v1 to v2 conversion matrix
#from samurai.analysis.support.SamuraiCalculatedSyntheticAperture import CalculatedSyntheticAperture
#from samurai.acquisition.support.SamuraiPlotter import SamuraiPlotter

SPEED_OF_LIGHT=299792458.

#%% generic class for synthetic aperture algorithms
class SamuraiSyntheticApertureAlgorithm:
    ''' 
    @brief this is a generic class for samurai aglorithms.
    This should be completed and the rest of this restructured in the futur
    This will allow a more generic things to work with such as importing measured vs. simed values
    '''
    SPEED_OF_LIGHT = 299792458.
    def __init__(self,metafile_path=None,**arg_options):
        '''
        @brief initilaize the SamSynthApAlg class  
        @param[in/OPT] metafile_path - metafile for real measurements (defaults to None)  
        @param[in/OPT] arg_options - keyword arguments as follows. Also passed to MetaFileController from which we inherit  
            - verbose         - whether or not to be verbose (default False)  
            - antenna_pattern - AntennaPattern Class parameter to include (default None)  
            - measured_values_flg - are we using measurements, or simulated data (default True)  
            - load_key        - Key to load values from (e.g. 21,11,12,22) when using measured values (default 21)  
            - load_data       - whether or not to load data on init (default true)  
            - These are also passed to the load_metafile function  
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
            
        self.unit_conversion_dict = { #dictionary to get to meters
                'mm': 0.001,
                'cm': 0.01,
                'm' : 1,
                'in': 0.0254
                }

        #initialize so we know if weve loaded them or not
        self.all_s_parameter_data = None #must be 2D array with axis 0 as each measurement and axis 1 as each position
        self.all_data_perturbation = None #perturbation on our S parameters
        #self.freq_list = None #this is now a property
        self.all_weights = None #weighting for our antennas
        self.all_positions = None #must be in list of [x,y,z,alpha,beta,gamma] points like on robot
        self.all_positions_perturbation = None #perturbations
        self.metafile = None
        if(metafile_path): #if theres a metafile load it
            self.load_metafile(metafile_path,**arg_options)

    def load_metafile(self,metafile_path,**arg_options):
        '''
        @brief function to load in our metafile and S parameter data from it
        @param[in] metafile_path - path to the metafile to load measurement from
        @param[in/OPT] freq_mult - how much to multiply the freq by to get hz (e.g. 1e9 for GHz)
        @param[in/OPT] arg_options -keyword arguments passed to MetaFileController.__init__ and MetaFileController.load_data
        '''
        self.metafile = MetafileController(metafile_path,**arg_options)
        if arg_options.get('load_data',True): #dont load if arg_options['load_data'] is False
            self.load_data(**arg_options)
            self.all_positions = self.metafile.get_positions()
        
    def load_data(self,data_type='nominal',data_meas_num=None,**arg_options):
        '''
        @brief load s parameter data using metafile paths
        @param[in/OPT] data_type - nominal,monte_carlo,perturbed,etc. If none do nominal
        @param[in/OPT] data_meas_num - which measurement of monte_carlo or perturbed to use
        @param[in/OPT] arg_options - keyword parameters as follows. They are all passed to self.metafile.load_data()
                None here
        '''
        options = self.options.copy() #create local options
        options['data_type'] = data_type
        options['data_meas_num'] = data_meas_num
        for k,v in arg_options.items():
            options[k] = v #add any other arg inputs
        s_data = self.metafile.load_data(**options)
        self.all_s_parameter_data = s_data
        
    def load_positions_from_file(self,file_path,**arg_options):
        '''
        @brief load positions from a file (like a csv)
        @param[in] file_path - path to file to load
        @param[in/OPT] arg_options - keyword arguments as follows:
                comment_character - character to ignore as comments when loading (default '#')
        '''
        options = {}
        options['comment_character'] = '#'
        for key,val in six.iteritems(arg_options):
            options[key] = val
        ext = os.path.splitext(file_path)[-1].strip('.')
        if ext=='csv':
            #load values in from CSV
            pos = np.loadtxt(file_path,delimiter=',',comments=options['comment_character'])
            self.all_positions = pos[:,:3]
        

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
    
#%% Positional Functions
    ###########################################################################
    ### Positional Functions
    ###########################################################################
    @property
    def positions(self):
        '''
        @brief getter for our positions. This will allow us to mask out undesired locations
        @return all desired positions that are not masked out
        @todo implement masking
        '''
        if self.all_positions is not None:
            #retrun a copy
            pos = self.all_positions.copy()   
            #now perturb if that is set. we must return a copy as to not overwrite the original positions
            if self.all_positions_perturbation is not None:
                pos += self.all_positions_perturbation
        else:
            pos=None
        return pos
    
    def normalize_positions(self,norm_funct=np.mean):
        '''
        @brief Normalize the values in self.all_positions to some combination of the positions
            By default normalize to the mean of all positions
        @param[in/OPT] norm_type - Function for normalization. Should have prototype 
            norm_funct(pos,axis=None) where pos is [[x,y,z,alpha,beta,gamma],[...],...].
            The return value will then be subtracted from self.all_positions.
        '''
        self.all_positions-=norm_funct(self.all_positions,axis=0)
          
    def get_positions(self,units='m'):
        '''
        @brief check our units options and get our positions in a given unit
        @param[in/OPT] units - what units to get our positions in (default meters)
        @return return our position in whatever units specified (default meters)
        '''
        to_meters_dict=self.unit_conversion_dict
        #multiply to get to meters and divide to get to desired units
        multiplier = to_meters_dict[self.options['units']]/to_meters_dict[units] 
        return self.positions*multiplier
    
    def set_positions(self,positions,units='m'):
        '''
        @brief set our positions with unit checking
        @param[in] positions [[X,Y,Z,alpha,beta,gamma],...] 2D numpy array of positions
        @param[in/OPT] units - units of the input positions default 'm' (meters)
        '''
        to_meters_dict=self.unit_conversion_dict
        #multiply to get to meters and divide to get to desired units
        multiplier = to_meters_dict[units]/to_meters_dict[self.options['units']]
        self.all_positions = multiplier*positions
    
    def perturb_positions(self,perturb_funct,*args,**kwargs):
        '''
        @brief Generate and add a perturbation to our positions.
            This will be added to self.all_positions_perturbation as to not change
            the raw positions themselves. This will then be added to the positions
            when getting the positions property. If self.all_positions_perturbation = None
            the raw positions will be returned.
        @param[in] perturb_funct - function to use to generate perturbation values.
            This will typically be from numpy.random.(normal/uniform/binomial/etc...) 
            but could also be a user made function that takes a 2D array of values
            and outputs perturbed values of the same shape.
        @param[in] *args - These are the arguments for the perturbation function.
            Before being passed to the funciton, if a scalar or 1D array is passed in
            it will be extended to match the shape of the positions.
        @param[in/OPT] kwargs - keyword arguments as follows
            units - units that the input data is in ('mm','cm','m','in') defaults meters 'm'
        '''
        options = {}
        options['units'] = 'm' #default to meters
        for k,v in kwargs.items():
            options[k] = v #overwrite defaults
        
        to_meters_dict=self.unit_conversion_dict
        multiplier = to_meters_dict[options['units']]/to_meters_dict[self.options['units']]
        #now extend along our axes if required
        args_new = []
        for arg in args:
            arg_new = self.expand_position_perturbation_val(arg)
            args_new.append(arg_new*multiplier)
        args_new = tuple(args_new)
        self.all_positions_perturbation = perturb_funct(*args_new)
    
    def perturb_positions_normal(self,stdev,units='m'):
        '''
        @brief generate positional perturbations using a normal distribution
        @param[in] stdev - Standard deviation of the positions. Can be a scalar,
            1D array [x,y,z,alph,bet,gam] or 2D array [[x,y,z,alph,bet,gam],...]
            to match the size of the position array from self.all_positions.
        @param[in/OPT] units - units that the standard deviations are in
        '''
        self.perturb_positions(np.random.normal,0,stdev,units=units)
        
    def expand_position_perturbation_val(self,val):
        '''
        @brief expand a perturbation value to the correct size (e.g. scalar to 2D array)
        @param[in] val - value to expand
        '''
        val = np.array(val)
        pos_shape = np.array(self.all_positions).shape
        if len(val.shape)<1: #then extend to 1d from scalar
            val = np.repeat(val,pos_shape[1],axis=0)
        if len(val.shape): #then extend to 2d
            val = np.repeat([val],pos_shape[0],axis=0)
        return val
    

    
    def clear_position_perturbation(self):
        '''
        @brief clear our perturbing of the position
        '''
        self.all_positions_perturbation = None
    
    @property
    def position_units(self):
        '''
        @brief get the units that the positions are in
        '''
        return self.options['units']
    
    def set_position_units(self,units):
        '''
        @brief change the units of our positions ('mm','cm','m','in') possible, 
            we must also convert our positions
        @param[in] units - the units to change to ('mm','cm','m','in')
        '''
        to_meters_dict=self.unit_conversion_dict
        multiplier = to_meters_dict[self.options['units']]/to_meters_dict[units]
        self.all_positions *= multiplier
        
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
    
    def plot_positions(self,pos_units='m',plot_type='weights',**arg_options):
        '''
        @brief plot the positions of our aperture in 3D, 
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
    
#%% S param functs
    ###########################################################################
    ### s parameter functions
    ########################################################################### 
    @property
    def s_parameter_data(self):
        '''
        @brief Getter for our s parameter data. This will allow us to mask out undesired locations.
        @note unlike all_s_parameter_data, this will return a numpy array, not a list of SnpEditors
        @return all s_parameter_data for desired positions that are not masked out
        @todo implemment masking
        '''           
        if self.all_s_parameter_data is not None:
            sp_dat = []
            keys = self.options['load_key']
            if not hasattr(keys, "__len__"):
                keys = [keys]
            for s in self.all_s_parameter_data:
                #self.all_s_parameter_data.append(np.array([s.S[load_key].raw for load_key in keys])) #turn the s parameters into an array
                data = np.array([s.S[load_key].raw for load_key in keys]) #turn the s parameters into an array
                sp_dat.append(data.transpose())
            if self.all_data_perturbation is not None:
                sp_dat+=self.all_data_perturbation
            return np.array(sp_dat)
        else:
            sp_dat = None
        return sp_dat
    
    @property
    def freq_list(self):
        '''
        @brief Getter for frequency list. This will use the first TouchstoneEditor value in self.all_s_parameters
            to ensure it is up to date in case we cut our data.
        '''
        if self.all_s_parameter_data is not None:
            return self.all_s_parameter_data[0].freq_list
    
    def perturb_data(self,stdev):
        '''
        @brief Generate and add a perturbation to our s parameter data.
            This will be added to self.all_data_perturbation as to not change
            the raw data. This will then be added to the data
            when getting the s_parameter_data property. If self.all_data_perturbation = None
            the raw data will be returned.
        @param[in] stdev - standard deviation to generate a random normal perturbation from.
            This value can be a scalar, or a set of values equal to the shape of the s_parameter_data
        '''
        self.all_data_perturbation = np.random.normal(scale=stdev)

#%% steering vector functions
    ###########################################################################
    ### Steering Vector Functions
    ###########################################################################
    def get_steering_vectors(self,az_u,el_v,k,coord='azel',**arg_options):
        '''
        @brief Get our steering vectors with wavenumber provided. calculates np.exp(1j*k*kvec)
            where kvec is i_hat+j_hat+k_hat.
            It is better to not use this for large calculations. Instead calculate the k vectors and get steering vectors in the algorithm
            to prevent recalculating k vectors.
        @param[in] az_u - azimuth or u values to get steering vectors for 
        @param[in] el_v - elevation nor v values to get steering vectors for
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
        @brief Get our partial steering vectors vector to later calculate the steering vector.
            Calculates i_hat+j_hat+k_hat dot position 
            (i.e. k_vectors*pos_vecs) and multiplies by position vectors.
            To get steering vectors use np.exp(-1j*k*psv_vecs).
        @param[in] az_u - azimuth or u values to get steering vectors for 
        @param[in] el_v - elevation nor v values to get steering vectors for
        @note az_u and el_v will be a pair list like from meshgrid. Shape doesnt matter. They will be flattened
        @param[in/OPT] coord - what coordinate system our input values are (azel or uv) (default azel)
        @param[in/OPT] arg_options - keyword argument options as follows
            - None Yet!
        @return The calculated partial steering vectors vectors for az_u and el_v at the provided k value, or without a k value.
            The first axis of the returned matrix is the position value .
            The second axis corresponds to the azel values.
        '''
        #[az,el] = self.to_azel(az_u,el_v,coord) #change to azel
        #az = np.deg2rad(az.reshape((-1))) #flatten arrays along the desired axis and change to radians
        #el = np.deg2rad(el.reshape((-1)))
        #get and center our positions
        pos = self.get_positions('m')[:,0:3] # positions 4,5,6 are rotations only get xyz
        #pos -= pos.mean(axis=0) #center around mean values
        
        #now calculate our steering vector values
        k_vecs = get_k_vectors(az_u,el_v,coord,**arg_options)
        psv_vecs = np.dot(pos,k_vecs) #this will multiply sv_vals by our x,y,z values and sum the three
        return psv_vecs
    
    def add_plane_wave(self,az_u,el_v,amplitude_db=-50,coord='azel'):
        '''
        @brief Add a plane wave to the s parameter data.
            If data doesnt exist then start from 0s.
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
    

#%% windowing
    ###########################################################################
    ### Windowing Functions
    ###########################################################################
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
        @brief set our weights to reflect a sine power window, 
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
    
    def set_tchebyshev_window(self,sll):
        '''
        @brief set a tschebyshev window on the data
        @note this only works for equally spaced elements where each row and 
            column have the same spacing (rectangular planar array)
        @todo implement this correctly for 2D
        '''
        x_unique = np.unique(self.positions[...,0])
        y_unique = np.unique(self.positions[...,1])
        #assume the positions are stored [x1,x2,...xn,x1,x2,...,xn-1,xn] 
        # and [y1,y1,y1,...,y2,y2,y2...,yn,yn,yn]
        
        pass
    
    def reset_window(self):
        '''
        @brief reset our window to all equal weighting (i.e. no windowing)
        '''
        self.weights = np.ones(self.positions.shape[0])
    
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
        @brief Setter for our antenna weights.
            For now these weights will be for just our values in use (masking doesnt effect).
            This means weights will need to be recalculated when masking is done
        @param[in] weights - weights to set
        @todo implemment masking
        '''
        self.all_weights = weights
        
#%% other useful things
###########################################################################
### some useful other functions
###########################################################################        
def to_azel(az_u,el_v,coord,replace_val = np.nan):
    '''
    @brief change a provided coordinate system ('azel' or 'uv') to azel
    @param[in] az_u list of azimuth (radians) or u values
    @param[in] el_v list of azimuth (radians) or v values
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

def to_uv(az_u,el_v,coord,replace_val = np.nan):
    '''
    @brief change a provided coordinate system ('azel' or 'uv') to uv
    @param[in] az_u list of azimuth (radians) or u values
    @param[in] el_v list of azimuth (radians) or v values
    @param[in] coord - what coordinate system our input values are
    @param[in/OPT] replace_val - value to replace uv outside of radius 1 with (default is nan)
    @return lists of [azimuth,elevation] values
    '''
    if(coord=='azel'):
        u = np.cos(el_v)*np.sin(az_u)
        v = np.sin(el_v)
    elif(coord=='uv'): 
        u = az_u; v = el_v
    return np.array(azimuth),np.array(elevation)
 
def get_k_vectors(az_u,el_v,coord='azel',**arg_options):
    '''
    @brief Get our k vector to later calculate the steering vector.
        Calculates i_hat+j_hat+k_hat.
        To get steering vectors use np.exp(-1j*k*dot(k_vectors*position_vectors)).
    @param[in] az_u - azimuth or u values to get k vecs for
    @param[in] el_v - elevation nor v values to get k vecs for
    @note az_u and el_v will be a pair list like from meshgrid. Shape doesnt matter. They will be flattened
    @param[in/OPT] coord - what coordinate system our input values are (azel or uv) (default azel)
    @param[in/OPT] arg_options - keyword argument options as follows
        - None Yet!
    @return The calculated k vectors for az_u and el_v at the provided k value, or without a k value.
        The first axis of the returned matrix is the x,y,z components respectively.
        The second axis is each of the measurements from the input az_u,el_v.
    '''
    az = np.deg2rad(az_u.flatten())
    el = np.deg2rad(el_v.flatten())
    #now calculate our steering vector values
    k_vecs = np.array([
            np.cos(el)*np.sin(az), #side to side (X)
            np.sin(el), #up and down (Y)
            np.cos(el)*np.cos(az) #propogation direction (Z)
            ])
    return k_vecs

def get_k(freq,eps_r=1,mu_r=1):
    cr = SPEED_OF_LIGHT/np.sqrt(eps_r*mu_r)
    lam = cr/freq
    k = 2*np.pi/lam
    return k


from numba import vectorize, complex64,float32
import cmath
@vectorize(['complex64(complex64,complex64)'],target='cpu')
def calculate_steering_vector_from_partial_k(partial_k,k):
    return cmath.exp(-1j*k*partial_k)

@vectorize(['complex64(complex64,complex64)'],target='cuda')
def vector_mult_complex(a,b):
    return a*b

@vectorize(['complex64(complex64,complex64)'],target='cpu')
def vector_div_complex(num,denom):
    return num/denom


#%% Class to utilize antennas
class Antenna(SamuraiDict):
    SPEED_OF_LIGHT=299792458.
    Z0 = 376.7 #impedance of free space
    '''
    @brief Class to hold antenna data. This is partially based on Ben's previous implementation
        , and partially based on my original the AntennaPattern Class.
    @note this is built as a dictionary containing all of the antenna patterns so things can be saved out
    @cite John D. Kraus Antennas
    @param[in] *args,**kwargs - all parameters passed to super().__init__
    '''
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def write(self,fpath,**kwargs):
        '''
        @brief Write antenna info to a file. This also adds self.eval_gain method to self['eval_gain']  
        @param[in] fpath - file path for writing out  
        @param[in/OPT] kwargs - keyword args passed to super().write
        @todo get this to work correctly
        '''
        self['eval_gain'] = self.eval_gain #write out the method
        super().write(fpath,**kwargs)
        
    def load(self,fpath,**kwargs):
        '''
        @brief Read antenna info from a file. This also loads self['eval_gain'] to self.eval_gain.
        @param[in] fpath - path to file to load
        @param[in/OPT] kwargs - keyword args passed to super().load
        @todo get this to work correctly
        '''
        super().load(fpath,**kwargs)
        #setattr(self,'eval_gain',self['eval_gain'])
        
    def writes(self,**kwargs):
        '''
        @brief Write antenna info to a file. This also adds self.eval_gain method to self['eval_gain'].
        @param[in/OPT] kwargs - keyword args passed to super().write
        @todo get this to work correctly
        '''
        #self['get_efield'] = self.__class__.__dict__['get_efield']
        return super().writes(**kwargs)
        
    def loads(self,mystr,**kwargs):
        '''
        @brief Read antenna info from a file. This also loads self['eval_gain'] to self.eval_gain.
        @param[in] mystr - string to load from
        @param[in/OPT] kwargs - keyword args passed to super().load
        @todo get this to work correctly
        '''
        super().load(mystr,**kwargs)
        setattr(self,'eval_gain',self['eval_gain'])
        
    def get_power(self,freqs,az,el,*args,**kwargs):
        '''
        @brief Evaluate complex power at a specific azimuth/elevation angle with
            a provided frequency. This needs to be overridden in subclasses.
        '''
        raise NotImplementedError
        
    def get_efield(self,freqs,az,el,*args,**kwargs):
        '''
        @brief Evaluate complex electric field at a specific azimuth/elevation angle with
            a provided frequency. This needs to be overridden in subclasses. 
        @return this should return a numpy array of [etheta,ephi] fields
        '''
        raise NotImplementedError
        
    def get_hfield(self,freqs,az,el,*args,**kwargs):
        '''
        @brief Evaluate complex electric field at a specific azimuth/elevation angle with
            a provided frequency. This needs to be overridden in subclasses.
        '''
        raise NotImplementedError
        
    def get_pvec(self,freqs,az,el,r=1,**kwargs):
        '''
        @brief get the pointing vector at a given frequency, az and el
        @cite Kraus p. 22
        '''
        if not hasattr(freqs,'__iter__'): #typically going to look for list of az,el
            freqs = np.array([freqs])
        pvals = []
        for f in freqs:
            efields = self.get_efield(f,az,el,r)
            pvecs = np.sum(efields**2,axis=0)/self.Z0 #from kraus
            pvals.append(pvecs)
        return np.array(pvals)
        
    def get_directivity(self,freqs,az=None,el=None,r=10,**kwargs):
        '''
        @brief calculate the directivity for a given frequency
        @cite kraus p. 26
        @note if az and el are not provided get the max directivity, otherwise provide pvec(az,el)/np.mean(pvec)
        @todo comment better and add for 2D
        '''
        options = {}
        options['search_angles'] = [np.linspace(0,2*np.pi,1000),
                   np.zeros_like(np.linspace(0,2*np.pi,1000))] #[[az],[el]] sweep angle pairs
        for k,v in kwargs.items():
            options[k] = v
        if not hasattr(freqs,'__iter__'): #typically going to look for list of az,el
            freqs = np.array([freqs])
        #now calculate pointing vectors
        dvals = [] #directivity
        dang = [] #maximum angle
        for f in freqs:
            pvecs = self.get_pvec(f,options['search_angles'][0],options['search_angles'][1],r)[0]
            pavg = np.mean(pvecs)
            if az is None and el is None:
                pmaxidx = np.argmax(np.abs(pvecs))
                pmax = pvecs[pmaxidx]
                dang.append([options['search_angles'][0][pmaxidx],options['search_angles'][1][pmaxidx]])
            else: #otherwise angles were provided
                pmax = self.get_pvec(f,az,el,r)
                dang.append([az,el])
            dvals.append(pmax/pavg)
        return [np.array(dvals),np.array(dang).transpose()]
        
    def plot_fields(self,freq,plane='e'):
        '''
        @brief plot the 2D fields from the antenna
        '''
        d = 0.05; nxy = 500
        Y,X = np.meshgrid(np.linspace(-d,d,nxy),np.linspace(-d,d,nxy))
        R = np.sqrt(X**2+Y**2)
        PHI = np.arctan2(Y,X)
        v = np.ndarray((PHI.size),dtype=np.cdouble)
        for i,r,phi in zip(range(R.size),R.flatten(),PHI.flatten()):
            #calculate the values
            v[i] = self.eval_efield(phi,0,freq,r=r)[1]
            
        V = np.reshape(v,X.shape)
        V[V>1.5] = np.nan
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        
        ax.plot_surface(X, Y, (np.real(V)))
        ax.set_title('Surface plot')
        plt.show()
        
        
class IsotropicAntenna(Antenna):
    '''
    @brief class for generating isotropic radiator data
    @author ajw5
    '''
    def get_efield(self,freqs,az,el,r):
        '''
        @brief isotropic radiator value at a given distance r  
        @param[in] az - azimuth angle (radians)    
        @param[in] el - elevation angle (radians)  
        @param[in] freqs - frequencies to calculate for (in hz)  
        @return values based on isotropic radiator and free space loss
        '''
        #freqs = np.array(freqs)
        lam = self.SPEED_OF_LIGHT/freqs
        kVals = 2.0*np.pi*freqs/self.SPEED_OF_LIGHT
        e_phi = np.sqrt(lam**2/((4*np.pi*r)**2))*np.exp(-1j*kVals*r) #this is not close but seems like the right eqn (sqrt(friis)))
        e_theta = np.sqrt(lam**2/((4*np.pi*r)**2))*np.exp(-1j*kVals*r)
        #e_theta = np.zeros_like(e_phi)
        
        #e_theta = np.sqrt(lam**2/(4*np.pi*r**2))*np.exp(-1j*kVals*r) #this is close but seems like the wrong eqn
        #e_phi   = np.sqrt(lam**2/(4*np.pi*r**2))*np.exp(-1j*kVals*r)
        return np.array([e_theta,e_phi])
    
    def get_power(self,freqs,az,el,r,**kwargs):
        '''
        @brief isotropic radiator value at a given distance r  
        @param[in] az - azimuth angle (radians)    
        @param[in] el - elevation angle (radians)  
        @param[in] freqs - frequencies to calculate for (in hz)  
        @return values based on isotropic radiator and free space loss
        '''
        lam = self.SPEED_OF_LIGHT/freqs
        kVals = 2.0*np.pi*freqs/self.SPEED_OF_LIGHT
        power = ((lam/(4*np.pi*r))**2)*np.exp(-1j*kVals*r)
        return power
    
    

class AnalyticalRectangularHornAntenna(Antenna):
    '''
    @brief class for generating a rectangular horn
    @author bfj
    @note this inherits from the previous Antenna class
    '''
    def get_efield(self, freqs, theta, phi, r=1):
        """
        @brief take in an angle of arrival and return an e field
        @cite Balanis "Antenna Theory: ..."
        @param[in] theta - theta angle to calculate (radians)
        @param[in] phi - phi angle to caluclate (radians)
        @param[in] freqs - ferquency in Hz.
        """
        if 'rho1' not in self:
            self['rho1'] = 0.5*self['b1']/np.tan(np.pi/180*self['psie'])
        if 'rho2' not in self:
            self['rho2'] = 0.5*self['a1']/np.tan(np.pi/180*self['psih'])
        
        kVals = 2.0*np.pi*freqs/self.SPEED_OF_LIGHT
        kyVals = kVals*np.sin(theta)*np.sin(phi)
        kxpVals = kVals*np.sin(theta)*np.cos(phi) + np.pi/self['a1']
        kxppVals = kVals*np.sin(theta)*np.cos(phi) - np.pi/self['a1']
        
        t1Vals = np.sqrt(1.0/(np.pi*kVals*self['rho1']))*(-kVals*self['b1']/2.0 - kyVals*self['rho1'])
        t2Vals = np.sqrt(1.0/(np.pi*kVals*self['rho1']))*( kVals*self['b1']/2.0 - kyVals*self['rho1'])
        
        t1pVals = np.sqrt(1.0/(np.pi*kVals*self['rho2']))*(-kVals*self['a1']/2.0 - kxpVals*self['rho2'])
        t2pVals = np.sqrt(1.0/(np.pi*kVals*self['rho2']))*( kVals*self['a1']/2.0 - kxpVals*self['rho2'])
        
        t1ppVals = np.sqrt(1.0/(np.pi*kVals*self['rho2']))*(-kVals*self['a1']/2.0 - kxppVals*self['rho2'])
        t2ppVals = np.sqrt(1.0/(np.pi*kVals*self['rho2']))*( kVals*self['a1']/2.0 - kxppVals*self['rho2'])
        # Evaluate sine and cosine Fresnel integrals
        st1, ct1 = scipy.special.fresnel(t1Vals)
        st1p, ct1p = scipy.special.fresnel(t1pVals)
        st1pp, ct1pp = scipy.special.fresnel(t1ppVals)
        st2, ct2 = scipy.special.fresnel(t2Vals)
        st2p, ct2p = scipy.special.fresnel(t2pVals)
        st2pp, ct2pp = scipy.special.fresnel(t2ppVals)
        #do some more things
        i1 = 0.5*np.sqrt(np.pi*self['rho2']/kVals)*( np.exp(1j*(kxpVals**2*self['rho2']/(2.0*kVals)))*((ct2p-ct1p) - 1j*(st2p - st1p)) \
                                                + np.exp(1j*(kxppVals**2*self['rho2']/(2.0*kVals)))*((ct2pp-ct1pp) - 1j*(st2pp - st1pp)))

        i2 = np.sqrt((np.pi*self['rho1'])/kVals)*np.exp(1j*(kyVals**2*self['rho1']/(2.0*kVals)))*((ct2 - ct1) - 1j*(st2-st1))
        #print i1, i2
        #nTheta = -1.0/self.eta*np.cos(theta)*np.sin(phi)*i1*i2
        #nPhi = -1.0/self.eta*np.cos(phi)*i1*i2
        
        #lTheta = np.cos(theta)*np.cos(phi)*i1*i2
        #lPhi = np.sin(phi)*i1*i2
        
        eFieldTheta = -1j*kVals*np.exp(-1j*kVals*r)/(4.0*np.pi*r)*(np.sin(phi)*(1+np.cos(theta))*i1*i2)
        eFieldPhi = 1j*kVals*np.exp(-1j*kVals*r)/(4.0*np.pi*r)*(np.cos(phi)*(np.cos(theta)+1)*i1*i2)
        
        return np.array([eFieldTheta, eFieldPhi])
    
    def get_power(self,freqs,theta,phi,r,**kwargs):
        """
        @brief take in an angle of arrival and return a complex gain
        @cite Balanis "Antenna Theory: ..."
        @param[in] theta - theta angle to calculate (radians)
        @param[in] phi - phi angle to caluclate (radians)
        @param[in] freqs - ferquency in Hz.
        """
        ef = self.get_efield(theta, phi, freqs, r)
        efm = np.sqrt(np.sum(ef**2))
        return efm**2

#%% Unit testing
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

    def test_location_perturbation(self):
        #test perturbing the positions
        #this tests to make sure we can perturb and return
        mysp = SamuraiSyntheticApertureAlgorithm()
        zlocs = 0
        xlocs = np.arange(0,0.103,0.003) #default positions in m
        ylocs = np.arange(0,0.103,0.003)
        [X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
        pos = np.zeros((X.size,6))
        pos[:,0] = X.flatten()
        pos[:,1] = Y.flatten()
        pos[:,2] = Z.flatten()
        mysp.set_positions(pos,'m') #set our positions 
        p_m = mysp.get_positions('m')
        mysp.perturb_positions_normal([1,1,1,0,0,0],units='mm')
        pp_m = mysp.get_positions('m')
        self.assertFalse(np.all(pp_m==p_m),'Perturbation not set correctly')
        mysp.clear_position_perturbation()
        self.assertTrue(np.all(p_m==mysp.get_positions('m')),'Perturbation not cleared correctly')
        

#%%
if __name__=='__main__':
    myr = 100; az = 0; el= 0
    freqs = np.array(np.arange(26e9,40e9,10e6))
    #freqs = np.array([33.25])
    #freqs = np.array([26.5e9])
    #lets generate a horn antenna file for sage 17dbi horn (from ben)
    sage17 = AnalyticalRectangularHornAntenna()
    sage17["a"] =  7.112*10**(-3)
    sage17["b"] =  3.556*10**(-3)
    sage17["a1"] = 25.400*10**(-3)
    sage17["b1"] = 19.812*10**(-3)
    sage17["psie"] = 33.4
    sage17["psih"] = 37.3
    #vo = np.array(sage17.get_efield(az,el,freqs,r=myr))
    #v = vo[1]
    #vo = sage17.get_efield(freqs,np.linspace(0,np.pi,5),np.linspace(0,np.pi,5),r=myr)
    #pv = np.sqrt(np.sum(vo**2))
    
    #isorad = IsotropicAntenna()
    #vio = isorad.get_efield(freqs,az,el,r=myr) #just get ephi
    #vi = vio[1]
    #pi = np.sqrt(np.sum(vio**2))
    #pr = sage17.get_power(freqs,az,el,r=myr)
    #pi = isorad.get_power(freqs,az,el,r=myr)
    azv = np.linspace(-np.pi,np.pi,361)
    elv = np.zeros_like(azv)
    #dsv ,dsa  = sage17.get_directivity(freqs,0,0,r=myr)
    #dsva,dsaa = sage17.get_directivity(np.array([33.25e9]),azv,elv,r=myr)
    
    etsf = sage17.get_efield(freqs,0,0,r=myr)
    etsa = sage17.get_efield(np.array([33.25e9]),azv,elv,r=myr)
    
    #di = isorad.get_directivity(freqs,r=myr)
    
    import matplotlib.pyplot as plt
    #plt.figure()
    #plt.plot(dsaa[:,0,0],10*np.log10(dsva[0,0,:]))
    #plt.figure()
    #plt.plot(freqs,10*np.log10(dsv))
    plt.figure()
    plt.plot(azv,10*np.log10(np.abs(etsa[1])))
    plt.figure()
    plt.plot(freqs,10*np.log10(np.abs(etsf[1])))
    #plt.plot(freqs,10*np.log10(np.abs(pr/pi)),label='Magnitude')
    #plt.plot(freqs,20*np.log10(np.angle(v/vi)),label='Phase')
    #plt.plot(freqs,20*np.log10(np.real(v/vi)),label='Real')
    #plt.plot(freqs,20*np.log10(np.imag(v/vi)),label='Imag')
    #plt.legend()
    
    #o = 10*np.log10(np.abs(pv/pi))
    
    #def friis(freqs,r)
    #isorad.plot_fields(30e9)
    #sage17.plot_fields(30e9)
    
    #test_ant_path = './data/test_ant_pattern.csv'
    #myant = Antenna(test_ant_path,dimension=1,plane='az')
    #myap = myant['pattern']
    #print(myap.type)
    #myap.plot_scatter_3d()
    #myant['pattern'].plot_scatter_3d()
    #print(myap.get_values([0,0.5,1,45,-45],[0,0,0,0,0]))
    #mysp = SamuraiSyntheticApertureAlgorithm()
    #zlocs = 0
    #xlocs = np.arange(0,0.103,0.003) #default positions in m
    #ylocs = np.arange(0,0.103,0.003)
    #[X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
    #pos = np.zeros((X.size,6))
    #pos[:,0] = X.flatten()
    #pos[:,1] = Y.flatten()
    #pos[:,2] = Z.flatten()
    #mysp.set_positions(pos,'m') #set our positions 
    #mysp.perturb_positions_normal([1,1,1,0,0,0],units='mm')

            
    #unittest.main()
            
    
    
    