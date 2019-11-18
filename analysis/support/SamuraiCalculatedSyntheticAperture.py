###########################################################################
### Calculated aperture output
########################################################################### 
#import matplotlib.pyplot as plt
#from matplotlib import cm
#from mpl_toolkits.mplot3d import Axes3D
import numpy as np #import constants
#import math #for vectorize math functions
import scipy.constants as sp_consts #import constants for speed of light
import scipy.interpolate as interp
import six
import json

from samurai.base.generic import incomplete,deprecated,verified
from samurai.base.generic import round_arb
from samurai.base.TouchstoneEditor import SnpEditor
from samurai.base.SamuraiPlotter import SamuraiPlotter
from samurai.analysis.support.MetaFileController import MetaFileController
from samurai.acquisition.support.samurai_optitrack import rotate_3d

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
                plot_program - 'matlab' or 'plotly' possible (default 'matlab')
                verbose - whether or not to be verbose (default False)
                metafile_data - extra data to pass to metafile when writing out
                    angular snp files. This usually will simply be passed as
                    the metafile loaded into a SamuraiSyntheticApertureAlgorithm
                    class. it should be a dictionary or subset of a dictionary
        @return CalculatedSyntheticAperture class
        '''
        self.options = {}
        self.options['plot_program'] = 'plotly'
        self.options['verbose'] = False
        self.options['metafile'] = None
        for key,val in six.iteritems(arg_options):
            self.options[key] = val
        AZ = np.array(AZIMUTH)
        EL = np.array(ELEVATION)
        if(AZ.shape != EL.shape):
            raise Exception("Azimuth and Elevation meshgrids must be the same size")
        self.elevation = EL
        self.azimuth   = AZ
        self.mp = None #initialize matlab plotter to none
        self.complex_values = np.array([])
        self.freq_list = np.array([])
        self.plotter = SamuraiPlotter(**self.options)
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
        
    def set_options(self,**arg_options):
        '''
        @brief set options of the class
        '''
        for key,val in six.iteritems(arg_options):
            self.options[key] = val
    
    def plot_azel(self,plot_type='mag_db',**arg_options):
        '''
        @brief plot calculated data in azimuth elevation
        @param[in] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] out_name - name of output plot (plotly)
        @param[in/OPT] arg_options - keyword arguments as follows:
            plot_program - 'matlab' or 'plotly' possible (default 'matlab')
        @return a handle for the figure
        '''
        options = {}
        options['plot_program'] = self.options['plot_program']
        for key,val in six.iteritems(arg_options):
            self.options[key] = val
            
        plot_data = self.get_data(plot_type,mean_flg=True)
        
        plot_arg_dict = {}
        plot_arg_dict.update({'xlabel':'Azimuth (degrees)','ylabel':'Elevation (degrees)','zlabel':plot_type})
        #plot_arg_dict.update({'xlim':[-db_range,db_range],'ylim':[0,db_range*2],'zlim':[-db_range,db_range]})
        plot_arg_dict.update({'shading':'interp'})
        plot_arg_dict.update({'colorbar':()})
        for k,v in arg_options.items():
            plot_arg_dict[k] = v
        rv = self.plotter.surf(self.azimuth,self.elevation,plot_data,**plot_arg_dict)
        return rv
    
    def plot_uv(self,plot_type='mag_db',out_name='test',**arg_options):
        '''
        @brief plot calculated data in uv space
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] out_name - name of output plot (plotly)
        @param[in/OPT] 
        @param[in/OPT] arg_options - keyword arguments as follows:
            plot_program - 'matlab' or 'plotly' possible (default 'matlab')
        @return a handle for the figure
        '''
        options = {}
        options['plot_program'] = self.options['plot_program']
        for key,val in six.iteritems(arg_options):
            self.options[key] = val
            
        plot_data = self.get_data(plot_type,mean_flg=True)
        #U = np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        #V = np.sin(np.deg2rad(self.elevation))
        #[Un,Vn,Dn] = increase_meshing_3D(U,V,plot_data,4)
        Un = self.U
        Vn = self.V
        Dn = plot_data
        
        #plt_mask = np.isfinite(Dn.flatten())
        #mv = np.nanmin(Dn,-1).mean()
        #fig = plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #ax.plot_surface(Un,Vn,mask_value(Dn,plt_mask,mv)
        #    ,cmap=cm.summer,linewidth=0, antialiased=False)
        #ax.set_xlabel("U (Azimuth)")
        #ax.set_ylabel("V (Elevation)")
        '''
        if(options['plot_program'].lower()=='matlab'):
            self.init_matlab_plotter()
            fig = self.mp.figure()
            self.mp.surf(Un,Vn,Dn)
            self.mp.view([0,90])
            self.mp.xlabel('U (Azimuth)')
            self.mp.ylabel('V (Elevation)')
            self.mp.zlabel(plot_type)
            return fig
        '''  
        if(options['plot_program'].lower()=='plotly'): 
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
            return fig
        else:
            raise Exception("Program %s not recognized" %(options['plot_program']))
            
        
    def plot_3d(self,plot_type='mag_db',**arg_options):
        '''
        @brief plot calculated data in 3d space (radiation pattern)
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @param[in/OPT] arg_options - keyword arguments as follows:
            plot_program - 'matlab' or 'plotly' possible (default 'matlab')
            translation - [x,y,z] translation points
            rotation - [alpha,beta,gamma] (XYZ) rotation of points
        @return a handle for the figure
        '''
        options = {}
        options['plot_program'] = self.options['plot_program']
        options['translation'] = [0,0,0]
        options['rotation'] = [0,0,0]
        for key,val in six.iteritems(arg_options):
            options[key] = val
            
        [X,Y,Z,plot_data,caxis_min,caxis_max] = self.get_3d_data(plot_type,translation=options['translation'],rotation=options['rotation'])
        X = -X #this is dependent on the robot reference frame. required for V2 reference frame
        db_range = caxis_max-caxis_min
        
        plot_arg_dict = {}
        plot_arg_dict.update({'xlabel':'X','ylabel':'Z','zlabel':'Y'})
        plot_arg_dict.update({'xlim':[-db_range,db_range],'ylim':[0,db_range*2],'zlim':[-db_range,db_range]})
        plot_arg_dict.update({'shading':'interp'})
        plot_arg_dict.update({'colorbar':('XTick',[0,db_range/2,db_range],'XTickLabel',[str(caxis_min),str(caxis_min+db_range/2),str(caxis_max)])})
        for k,v in arg_options.items():
            plot_arg_dict[k] = v
        #plot_arg_dict.update({'colorbar':('XTick',[caxis_min,caxis_max],'XTickLabel',[str(caxis_min),str(caxis_max)])})
        rv = self.plotter.surf(X,Z,Y,plot_data,**plot_arg_dict)
        return rv
        
    def plot_scatter_3d(self,plot_type='mag_db',out_name='test',**arg_options):
        '''
        @brief scatter plot calculated data in 3d space (radiation pattern)
        @param[in/OPT] plot_type - data to plot. can be 'mag','phase','phase_d','real','imag'
        @return a handle for the figure
        '''
        
        #get our data
        plot_data = self.get_data(plot_type,mean_flg=True)
        #[plot_data,caxis_min,caxis_max,db_range] = self.adjust_caxis(plot_data,plot_type,60)
        
        #now get our xyz values
        #X = plot_data*np.cos(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
        #Y = plot_data*np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        #Z = plot_data*np.sin(np.deg2rad(self.elevation))
        [X,Y,Z,plot_data,caxis_min,caxis_max] = self.get_3d_data(plot_type)
        db_range = caxis_max-caxis_min
        
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
        return fig
     
    def get_data(self,data_str,freqs='all',**arg_options):
        '''
        @brief get the desired data from a string (e.g. 'mag_db','phase_d','mag', etc.)
            this can also be used to select which frequencies to average
        @param[in] data_str - string of the data to get. can be 'mag','phase','phase_d','real','imag',complex
        @param[in/OPT] freqs - which frequencies to average (default 'all'). if the freq doesnt exist, throw an exception
        @param[in/OPT] arg_options - keyword arguments as follows
                mean_flg - whether or not to return the mean across all frequencies
                constant_output - add a new dimension to our data to ensure consistent output even when using mean_flg
        @return np array of shape self.azimuth (or elevation) with the values from the provided frequencies
        '''
        options = {}
        options['mean_flg'] = False
        options['constant_output'] = False
        for key,val in six.iteritems(arg_options):
            options[key] = val
            
        data_dict = {
            'mag_db':self.mag_db,
            'mag':self.mag,
            'phase':self.phase,
            'phase_d':self.phase_d,
            'real':self.real,
            'imag':self.imag,
            'complex':self.complex_values
            }
        freq_idx = self.get_freq_idx(freqs)
        data = data_dict[data_str]
        data = data[:,:,freq_idx]
        if options['mean_flg']:
            data = np.mean(data,axis=2)
            if options['constant_output']: 
                data = data[...,np.newaxis] #ensure we always return a 3D tuple
        return data
        
    def get_freq_idx(self,freqs):
        '''
        @brief get the index of the frequeny provided
            'all' will return all indexes
        @param[in] freqs to get indices of ('all' returns all)
        '''
        if np.any(np.array(freqs)=='all'):
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
    
    def get_snp_data(self,**arg_options):
        '''
        @brief get all of our calculated data as a list of info dictionaries and SnpEditor objects
        @param[in/OPT] arg_options - keyword args as follows
            None Yet!
        @return [meas_info_list,SnpEditor_list]
        '''
        meas_info = []
        meas_data = [] #values for returning
        pos_key_entry = {'position_key':['azimuth','elevation']}
        freqs = self.freq_list/1e9 #freqs in ghz
        for i in range(self.num_positions):
            cur_idx = np.unravel_index(i,self.azimuth.shape)
            az = self.azimuth[cur_idx]
            el = self.elevation[cur_idx]
            #assume our freq_list is in hz then write out in GHz
            mys = SnpEditor([2,freqs],comments=['azimuth = '+str(az)+' degrees','elevation = '+str(el)+' degrees'],header='GHz S RI 50') #create a s2p file
            #populate the s21,values
            mys.S[21].update(self.freq_list,self.complex_values[cur_idx])
            mys.S[12].update(self.freq_list,self.complex_values[cur_idx])
            #add to list and create our info
            meas_data.append(mys)
            cur_info = {}
            cur_info.update(pos_key_entry)
            cur_info.update({'position':[float(az),float(el)]})
            meas_info.append(cur_info)
        return meas_info,meas_data
    
    def write_snp_data(self,out_dir='./',**arg_options):
        '''
        @brief write out our frequencies over our angles into s2p files 
            s21,s12 will be our complex values, s11,s22 will be 0.
            Files will be written out as 'beamformed_<number>.snp'.
            A json file (beamformed.json) will also be written out
            giving the azimuth elevation values.
        @param[in/OPT] out_dir - output directory to save the files and the metafile
        @param[in/OPT] arg_options - keyword args as follows:
                out_path_format - what the output path of the measurements will look like. 
                    This will be appended to out_dir. any format value (i.e. {}) will be replaced
                json_path - path where the json file will be saved. This will be appended to out_dir
        @return list of SnpEditor classes with the data written out, and list of absolute paths to the files
        '''
        #get input options
        options = {}
        options['out_path_format'] = 'beamformed_{}.s2p_binary'
        options['json_path'] = 'beamformed.json'
        for k,v in arg_options.items():
            options[k] = v
        #loop through all of our positions
        meas_paths = []
        meas_info,meas_data = self.get_snp_data(**arg_options)
        for i,mys in enumerate(meas_data):
            #now save out
            out_path = options['out_path_format'].format(i)
            out_path = os.path.join(out_dir,out_path)
            #make the dir if it doesnt exist
            out_path_dir = os.path.dirname(out_path)
            if not os.path.exists(out_path_dir):
                os.makedirs(out_path_dir)
            meas_paths.append(os.path.abspath(out_path))
            mys.write(out_path)
            cur_info = {'filename':out_path}
            meas_info[i].update(cur_info)
            
        if self.options['metafile'] is None: #create a metafile from default if one wasnt provided
            self.options['metafile'] = MetaFileController(None)
        #update our measurements to beamformed data and change some important options
        self.options['metafile']['positioner'] = 'beamforming'
        self.options['metafile'].wdir = out_dir #set the wdir to the output dir
        self.options['metafile'].update({'measurements':meas_info})
        self.options['metafile'].write(os.path.join(out_dir,options['json_path']))
        return meas_data, meas_paths
    
    def get_max_beam_idx(self,freqs='all',**arg_options):
        '''
        @brief get the index of the maximum beam
        @param[in/OPT] freqs - list of frequencies to calculate for
        @param[in/OPT] arg_options - optional keword arguements as follows:
            mean_flg - whether or not to get the average data
        @return tuple of tuples with indices of the maximum
        '''
        if freqs=='all':
            freqs = self.freq_list
        freqs = np.array(freqs)
        idx_vals = [] #allocate for outputs
        data = self.get_data('mag_db',freqs=freqs,constant_output=True,**arg_options) # get our data
        for i in range(data.shape[-1]):
            cur_dat = data[...,i] #get the current data
            max_idx = np.unravel_index(cur_dat.argmax(),cur_dat.shape)
            idx_vals.append(max_idx)
        return tuple(idx_vals)
    
    def get_max_beam_angle(self,freqs='all',**arg_options):
        '''
        @brief get the angle of the maximum beam
        @param[in/OPT] freqs - list of frequencies to calculate for
        @param[in/OPT] arg_options - keyword args are also as follows:
            None for this method
            also passed to self.get_max_beam_idx() method
        @return 2D array with azel [[az,el],[az,el],[az,el],etc...]
        '''
        idx_vals = self.get_max_beam_idx(freqs,**arg_options)
        for v in idx_vals:
            az_vals = self.azimuth[v]
            el_vals = self.elevation[v]
        return np.stack([az_vals,el_vals])
    
    def get_max_beamwidth(self,freqs='all',**arg_options):
        '''
        @brief get the beamwidth of the maximum beam
        @param[in/OPT] freqs - list of frequencies to calculate for
        @param[in/OPT] arg_options - keyword args are also as follows:
            None for this method
            also passed to self.get_max_beam_idx() method
        @return tuple with (az_bw,el_bw)
        '''
        idx_vals = self.get_max_beam_idx(freqs,**arg_options)
        if freqs=='all':
            freqs = self.freq_list
        return self.get_beamwidth(idx_vals,freqs)
        
    
    def get_max_side_lobe_level(self,freqs='all'):
        '''
        @brief get the maximum side lobe level and its location
        @todo implement this
        @return [max_level_db,(az,el)]
        '''
        pass
    
    def get_all_peak_idx(self,freqs='all'):
        '''
        @brief get all of the peaks from the data
        @param[in/OPT] freqs - frequencies to get the peaks for
        @return 2D list of tuples (x,y) for index of angle magnitude of the peaks
        ### 1D solution ###
        '''
        data = self.get_data('mag_db',freqs=freqs,constant_output=True)
        peak_locs = np.diff(np.diff(data)>0) #
    
    def get_all_peak_idx_1d(self,vals):
        '''
        @brief get all of the peaks in a set of 2D values (such as a elevation or azimuth plane cut)
        @param[in] vals - 1D array of values to find peaks of
        @return 1D numpy array of integers for the indices of each of the peaks
        '''
        d1 = vals
        d1dg = np.diff(d1)>0 #find the derivative and make True > 0
        l = np.diff(d1dg) #get the zero crossings of the derivative 
        # checking for greater than 0, we get - to + transition is False to True (bowls)
        # + to - transition is True to False (peaks) what we are looking for
        locs = np.where(l==True)[0] #get the locions of the zero crossings of the derivative
        peaks = locs[d1dg[locs]]+1 #this will be the indexes of our peaks (+1 because of diff)
        #[1 2 3 4 5 6 7 8 9 10] first derivative indexing
        #[ 1 2 3 4 5 6 7 8 9  ] second derivative indexing
        #[  1 2 3 4 5 6 7 8   ] third derivative indexing
        return peaks
        
    def get_beamwidth(self,peak_idx,freqs,**arg_options):
        '''
        @brief get the beamwidth of a beam with peak at index location (x,y)
            this is the same index provided by get_max_beam_idx. This finds the closest
            calculated angular crossings so will not be extremely accurate
        @param[in] peak_idx - peak locations in list of tuples (x,y) format for each freq in freqs for location in az/el 2D arrays 
        @param[in] freqs - list of frequencies the peaks are at. (can be all)
        @param[in/OPT] arg_options - optional keyword args as follows:
                power_level_db - power level for the beamwidth (default -3dB=HPBW)
                interpolate - true or false whether to interpolate (default true)
                interp_step - angular step (degrees) for our interpolation (default 0.1 degrees)
        @return beamwidths in list of tuples (az_bw,el_bw) for each frequency
        '''
        options = {}
        options['power_level_db'] = -3
        options['interpolate'] = True
        options['interp_step'] = 0.1
        bw_out = []
        if freqs=='all':
            freqs = self.freq_list
        for i,f in enumerate(freqs): #go through each frequency
            fidx=self.get_freq_idx(f)
            pidx = peak_idx[i] #peak idx value
            peak_val   = self.mag_db[pidx][fidx][0]
            peak_az = self.azimuth[pidx]
            peak_el = self.elevation[pidx]
            [az_vals,mymags_az] = self.get_azimuth_cut(peak_el,f)
            [el_vals,mymags_el] = self.get_elevation_cut(peak_az,f)
            mmaz_adj   = (mymags_az-peak_val).mean(axis=1) #adjust for peak
            mmel_adj   = (mymags_el-peak_val).mean(axis=1) #mean combines multiple freqs if we have them
            if options['interpolate']:
                interp_az = np.arange(az_vals.min(),az_vals.max()+options['interp_step'],options['interp_step'])
                interp_el = np.arange(az_vals.min(),az_vals.max()+options['interp_step'],options['interp_step'])
                mmaz_adj = np.interp(interp_az,az_vals,mmaz_adj)
                mmel_adj = np.interp(interp_el,el_vals,mmel_adj)
                az_vals = interp_az
                el_vals = interp_el
            #this uses a level crossing test. Interpolation would be more accurate
            az_cross_idx = np.where(np.diff(mmaz_adj<options['power_level_db']))[0] #find the crossing of the power level
            if(len(az_cross_idx)!=2):
                raise Exception("Must be exactly 2 azimuth crossings (%d found) to calculate beamwidth" %(len(az_cross_idx)))
            el_cross_idx = np.where(np.diff(mmel_adj<options['power_level_db']))[0]
            if(len(el_cross_idx)!=2):
                raise Exception("Must be exactly 2 elevation crossings (%d found) to calculate beamwidth" %(len(el_cross_idx)))
            #now take the difference of the az and el
            az_bw = np.abs(np.diff(az_vals[az_cross_idx]))[0]
            el_bw = np.abs(np.diff(el_vals[el_cross_idx]))[0]
            az_bw = round_arb(az_bw,options['interp_step'])
            el_bw = round_arb(el_bw,options['interp_step'])
            bw_out.append((az_bw,el_bw))
        return bw_out
    
    def get_elevation_cut(self,az_angle,freqs='all',**arg_options):
        '''
        @brief get an elevation cut from our data at azimuth
        @param[in] az_angle - azimuth angle to make cut in degrees 
        @param[in/OPT] freqs - frequencies to get output values for
        @param[in/OPT] arg_options - keyword args. passed to other methods. For this method as follows
                    None Yet!
        @return elevation_values,[mag_db_val1,mag_db_val2,etc...](freq along axis 1)
        '''
        flat_idx = np.argmin(np.abs(self.azimuth-az_angle))
        idx = np.unravel_index(flat_idx,self.azimuth.shape)[1]
        el_vals = self.elevation[:,idx]
        vals = self.get_data('mag_db',freqs,**arg_options)[:,idx]
        return el_vals,vals
        
    def get_azimuth_cut(self,el_angle,freqs='all',**arg_options):
        '''
        @brief get an azimuth cut from our data at elevation index
        @param[in] el_angle - elevation angle to make cut in degrees 
        @param[in/OPT] freqs - frequencies to get output values for
        @param[in/OPT] arg_options - keyword args. passed to other methods. For this method as follows
                    None Yet!
        @return elevation_values,[mag_db_val1,mag_db_val2,etc...](freq along axis 1)
        '''
        flat_idx = np.argmin(np.abs(self.elevation-el_angle))
        idx = np.unravel_index(flat_idx,self.elevation.shape)[0]
        az_vals = self.azimuth[idx,:]
        vals = self.get_data('mag_db',freqs,**arg_options)[idx,:]
        return az_vals,vals
    
    def get_data_from_azel(az,el,data_type='mag_db'):
        '''
        @brief get a value (e.g. mag_db) from a given azimuth elevation angle
        @param[in] az - value or list of azimuth values
        @param[in] el - value or list of corresponding elevation values
        @param[in/OPT] data_type - type of data to get (e.g mag_db)
        @todo unifinished!
        @return list of data from each of the azel pairs
        '''
        pass
    
    def azel_to_idx(az,el):
        '''
        @brief change azel values to a tuple pair for indices
        @param[in] az - value or list of azimuth values
        @param[in] el - value or list of corresponding elevation values
        @todo unifinished!
        @return tuple of tuples for the 2D indexes
        '''
        if not hasattr(az,'__iter__'):
            az = [az]
        if not hasattr(el,'__iter__'):
            el = [el]
        az = np.array(az)
        el = np.array(el)
        out_vals = []
        for i in range(len(az)):
            pass
        return tuple(out_vals)
    
    def get_3d_data(self,data_type='mag_db',**arg_options):
        '''
        @brief get 3D data values X,Y,Z for 3D plotting
        @param[in/OPT] data_type - the type data to get. can be 'mag','phase','phase_d','real','imag' (default mag_db)
        @param[in/OPT] arg_options - keyword arguments as follows:
            translation - set of [x,y,z] values to translate the 3D data in space
            scale - value for how to scale the size of the points.
            rotation - rotation in degrees. this will rotate XYZ in the same form as the meca robot
        @return [X,Y,Z,plot_data_adj,caxis_min,caxis_max] 3D data positions(X,Y,Z), adjusted plot data (to remove negative vals),
            min and max values of our caxis (colorbar). Here z is in the propogation direction.
        '''
        options = {}
        options['translation'] = [0,0,0]
        options['rotation'] = [0,0,0]
        options['scale'] = 1
        options['forward_axis'] = 'z'
        for k,v in arg_options.items():
            options[k] = v
        
        plot_data = self.get_data(data_type,mean_flg=True)
        [plot_data_adj,caxis_min,caxis_max,db_range] = self.adjust_caxis(plot_data,data_type,60)
        Z = plot_data_adj*np.cos(np.deg2rad(self.elevation))*np.cos(np.deg2rad(self.azimuth))
        X = plot_data_adj*np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
        Y = plot_data_adj*np.sin(np.deg2rad(self.elevation))
        
        #rotation
        x_shape = X.shape; y_shape = Y.shape; z_shape = Z.shape
        coords = np.concatenate((X.reshape((-1,1)),Y.reshape((-1,1)),Z.reshape((-1,1))),axis=1)
        rcoords = rotate_3d('xyz',options['rotation'],coords)
        Xf,Yf,Zf = np.split(rcoords,3,axis=1)
        X = Xf.reshape(x_shape); Y = Yf.reshape(y_shape); Z = Zf.reshape(z_shape)
        
        #scale
        X *= options['scale']
        Y *= options['scale']
        Z *= options['scale']
        #translate
        X += options['translation'][0]
        Y += options['translation'][1]
        Z += options['translation'][2]
        
        return [X,Y,Z,plot_data_adj,caxis_min,caxis_max]
        
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
        return np.cos(np.deg2rad(self.elevation))*np.sin(np.deg2rad(self.azimuth))
    
    @property
    def V(self):
        '''
        @brief get our V grid values from our angles
        '''
        return np.sin(np.deg2rad(self.elevation))
    
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
