# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""

import numpy as np #import constants
import math #for vectorize math functions
import scipy.constants as sp_consts #import constants for speed of light
import cmath #cmath for phase
from numba import vectorize

from plotting_help import increase_meshing_3D

from samurai.analysis.support.metaFileController import MetaFileController 
   
class SamuraiPostProcess(MetaFileController):
    '''
    @brief this is a class to inherit from for processing samurai data
        This will implement generic things like loading metadata used for all
        post-processing techniques. It currently inherits from metafile controller
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
    def __init__(self,ELEVATION,AZIMUTH,complex_values,**arg_options):
        '''
        @brief intializer for the class
        @param[in] THETA - meshgrid output of THETA angles (elevation up from xy plane)
        @param[in] PHI   - meshgrid output of PHI angles   (azimuth from x)
        @param[in] complex_values - values corresponding to a direction [THETA[i,j],PHI[i,j]]
        @param[in] arg_options - optional input keyword arguments as follows:
                -None yet
        @return CalculatedSyntheticAperture class
        '''
        self.options = {}
        self.elevation = ELEVATION
        self.azimuth   = AZIMUTH
        self.complex_values  = complex_values
    
    def plot_azel(self,plot_type='mag_db',out_name='test'):
        '''
        @brief plot calculated data in azimuth elevation
        @param[in] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] out_name - name of output plot (plotly)
        @return a handle for the figure
        '''
        plot_data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag
            }
        
        plot_data = plot_data_dict[plot_type] #get the type of plot
        
        
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
        plot_data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag
            }
        #get our data
        plot_data = plot_data_dict[plot_type] #get the type of plot
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
                    title='U (Azimuth'),
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
            
        
    def plot_3d(self,plot_type='mag_db',out_name='test'):
        '''
        @brief plot calculated data in 3d space (radiation pattern)
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @return a handle for the figure
        '''
        plot_data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag
            }
        #get our data
        plot_data = plot_data_dict[plot_type] #get the type of plot
        #minimum value if were plotting db
        if(plot_type=='mag_db'):
            #mask out lower values
            db_range = 60 #lower than the max
            caxis_min = plot_data.max()-db_range
            caxis_max = plot_data.max()
            plot_data = plot_data-(plot_data.max()-db_range) #shift the values
            plot_data = mask_value(plot_data,plot_data<=0)
        else: 
            #Zero the data
            caxis_min = plot_data.min()
            caxis_max = plot_data.max()
            plot_data = plot_data-plot_data.min()
        
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
        plot_data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag
            }
        #get our data
        plot_data = plot_data_dict[plot_type] #get the type of plot
        
        #now get our xyz values
        X = plot_data*np.cos(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
        Y = plot_data*np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        Z = plot_data*np.sin(np.deg2rad(self.elevation))
        
        #and plot
        plotly_surf = [go.Scatter3d(z = Z, x = X, y = Y)]
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
        
        
    @property
    def mag_db(self):
        '''
        @brief get the maginutude in db of our values. This uses 20*log10(val)
        '''
        return 20*np.log10(self.mag)
    
    @property
    def mag(self):
        '''
        @brief get our data values magnitude
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
            self.load_pattern(pattern_file_path)
            
    def load_pattern(self,pattern_file_path):
        '''
        @brief load an antenna pattern from a file
        @param[in] pattern_file_path - pattern file to load. For more information see AntennaPattern.load()
        '''
        self['pattern'] = AntennaPattern(pattern_file_path)
        

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
            None Yet!
        '''
        self.load(pattern_file)
    
    def load(self,pattern_file):
        '''
        @brief method to load pattern data from a file
            Currently the following filetypes are supported:
                --- CSV ---
                comma separated value files with the format
                'azimuth, elevation, value (complex)' are supported
        @param[in] pattern_file - file to load
        @return [azimuth,elevation,values(complex)]
        '''
        file_ext = os.path.splitext(pattern_file)[-1]
        load_functs = {
                '.csv':self.load_csv
                }
        load_funct = load_functs[file_ext]
        [az,el,vals] = load_funct(pattern_file)
        super(AntennaPattern,self).__init__(el,az,vals) #init the superclass
    
    def load_csv(self,pattern_file):
        '''
        @brief method to load pattern data from CSV 
            data should be in the format 'azimuth, elevation, real(value),imag(value)'
            all angles should be in degrees with 0,90=az,el pointing boresight
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
    
    
    
#        if()
    
@vectorize(['float32(float32,float32,float32)'],target='cuda')
def vector_dist(dx,dy,dz):
    return math.sqrt(dx**2+dy**2+dz**2)

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
    #test_path = r".\binary_aperture\metafile_binary.json"
   # mysp = SamuraiProcess(test_path)
    #[mycsa_list,sv,s21,x,y,z,dr] = mysp.beamforming_farfield(np.arange(60,120),np.arange(-30,30),40e9,verbose=True)
    #[mycsa_list,sv,s21,x,y,z,dr] = mysp.beamforming_farfield(np.arange(0,180),np.arange(-90,90),40e9,verbose=True)
    #mycsa_list = mysp.beamforming_farfield(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
    #mycsa_list = mysp.beamforming_farfield_uv(np.arange(-1,1,0.01),np.arange(-1,1,0.01),40e9,verbose=True)
   # mycsa = mycsa_list[0]
    #mycsa.plot_uv()
    #mycsa.plot_3d()
    
    test_ant_path = './test_ant_pattern.csv'
    myant = Antenna(test_ant_path)
    myant['pattern'].plot_scatter_3d()
    

    
    
    
    
    
    