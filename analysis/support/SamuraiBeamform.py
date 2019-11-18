# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:41:34 2019

@author: ajw5
"""
from samurai.analysis.support.SamuraiPostProcess import SamuraiSyntheticApertureAlgorithm
from samurai.analysis.support.SamuraiPostProcess import to_azel,get_k
from samurai.analysis.support.SamuraiPostProcess import calculate_steering_vector_from_partial_k
from samurai.analysis.support.SamuraiPostProcess import vector_mult_complex,vector_div_complex
from samurai.analysis.support.SamuraiCalculatedSyntheticAperture import CalculatedSyntheticAperture
from samurai.analysis.support.SamuraiCalculatedSyntheticAperture import Antenna
from samurai.base.generic import ValueCounter
import numpy as np #import constants

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
            data_type       - nominal,monte_carlo,perturbed,etc. If none do nominal
            data_meas_num   - which measurement of monte_carlo or perturbed to use
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
            use_vectorized - use vectorized numba operations (default true)
        @note theta and phi vals will be created into a meshgrid
        @return list of CalculatedSyntheticAperture objects
        '''
        #input options (these are defaults)
        options = {}
        options['verbose'] = self.options['verbose']
        options['antenna_pattern'] = self.options['antenna_pattern']
        options['use_vectorized'] = False
        for key,val in six.iteritems(arg_options):
            options[key] = val #set kwargs
        antenna_pattern = options['antenna_pattern']
        verbose = options['verbose']
        
        #validate our current data
        self.validate_data()
        
        #list of calulcated synthetic apertures        
        s_freq_list = self.freq_list
        s21_vals = self.s_parameter_data.astype(np.complex64)
        weights = self.weights.astype(np.complex64)
        
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
        psv_vecs =  self.get_partial_steering_vectors(azimuth,elevation).astype(np.complex64) #k_vectors*position_vectors
        
        #set our antenna values
        az_adj = -1*az_angles[:,np.newaxis]+np.reshape(azimuth,(-1,))
        el_adj = np.zeros(az_adj.shape)
        if(antenna_pattern is not None):
            antenna_values = antenna_pattern.get_values(az_adj,el_adj).astype(np.complex64)
        #else:
            #antenna_values = np.ones(psv_vecs.shape,dtype=np.complex64)
        
        #now lets loop through each of our frequencies in freq_list
        if verbose: print("Beginning beamforming for %d frequencies" %(len(freq_list)))
        mycsa = CalculatedSyntheticAperture(azimuth,elevation,**self.options)
        vc = ValueCounter(freq_list,'    Calculating for {:10G} Hz',update_period=10)
        for freq in freq_list:
            if verbose: vc.update(freq)
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
            s21_current = np.ascontiguousarray(s21_vals[...,freq_idx])
            #now we can calculate the beam phases for each of the angles at each position
            k = get_k(freq)
            if options['use_vectorized']:
                steering_vectors = calculate_steering_vector_from_partial_k(psv_vecs,k)
                s21_weighted = vector_mult_complex(s21_current,weights)
                if(antenna_pattern is not None):
                    sv_div_ants  = vector_div_complex(steering_vectors,antenna_values)
                else:
                    sv_div_ants = steering_vectors
            else:
                steering_vectors = np.exp(-1j*k*psv_vecs)    
                s21_weighted = s21_current*weights
                if(antenna_pattern is not None):
                    sv_div_ants  = steering_vectors/antenna_values
                else:
                    sv_div_ants = steering_vectors            
            
            # sum(value_at_position*steering_vector) for each angle
            # now calculate the values at each angle
            #beamformed_vals = np.dot(s21_current*self.weights,steering_vectors/antenna_values)/self.weights.sum()
            beamformed_vals = np.dot(s21_weighted,sv_div_ants)/self.weights.sum()
            
            #now pack into our CSA (CaluclateSynbteticAperture)
            mycsa.add_frequency_data(np.reshape(beamformed_vals,azimuth.shape),freq)
            #csa_list.append(CalculatedSyntheticAperture(azimuth,elevation,np.reshape(beamformed_vals,azimuth.shape)))
        vc.finalize()
        if antenna_pattern is not None:
            ant_vals = CalculatedSyntheticAperture(azimuth,elevation,np.reshape(antenna_values[1,:],azimuth.shape),**self.options)
        else:
            ant_vals = None

        return mycsa,ant_vals
        #return csa_list,steering_vectors,s21_current,x_locs,y_locs,z_locs,delta_r



###############################################################################
### Test Cases
###############################################################################
#this is a test case for when this file itself is run (not importing the module)
if __name__=='__main__':
    testa = True #synthetic and real data tests (commented out)
    testb = False #data from usc 5-27-2019 (s2p padp output)
    testc = False
    testd = False
    teste = False #plot markers with beamformed data
    testf = False
    #test case for simple beamforming
    if(testa):
        '''
        #measured data test
        #test_path = r".\\data\\2-13-2019\\binary_aperture_planar\\metafile_binary.json"
        test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-17-2019\aperture_vertical_polarization\binary\metafile_binary.json"
        #test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-17-2019\aperture_horizontal_polarization\binary\metafile_binary.json"
        #test_path = r".\\data\\2-13-2019\\binary_aperture_cylindrical\\metafile_binary.json"
        mysp = SamuraiBeamform(test_path,verbose=True)
        '''
        
        #synthetic data test
        #testing our synthetic data capabilities
        mysp = SamuraiBeamform(verbose=True,units='m')

        pos_step = 0.003
        #num_offsets = 7
        #hex_grid_offset = np.linspace(0,pos_step,35)
        hex_grid_offset = np.random.rand(35)*0.103
        hex_grid_offsetz = np.random.rand(35)*0.103
        #hgo = 0
        #hex_grid_offset = np.append(hgo,np.array([0,hgo]*17)) #(offset every other row)
        #now reshape for adding
        #hex_grid_offset = hex_grid_offset.reshape((1,1,-1)) #for y values
        zlocs = 0
        xlocs = np.arange(0,0.103,0.003) #default positions in m
        ylocs = np.arange(0,0.103,0.003)
        #zlocs = 0
        #xlocs = np.arange(0,0.053,0.003) #default positions in m
        #ylocs = np.arange(0,0.053,0.003)
        [X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
        npts = 500
        #Z = np.zeros(npts)
        #X = np.random.rand(npts)*0.103
        #Y = np.random.rand(npts)*0.103
        pos = np.zeros((X.size,6))
        #pos = np.zeros((X.size*2,6))
        #Y = Y+hex_grid_offset
        #X = X+hex_grid_offsetz.reshape((-1,1,1))
        pos[:,0] = X.flatten()
        pos[:,1] = Y.flatten()
        pos[:,2] = Z.flatten()
        #second array
        #pos[:,0] = np.append(X.flatten(),X.flatten())
        #pos[:,1] = np.append(Y.flatten(),Y.flatten()+0.1)
        #pos[:,2] = np.append(Z.flatten(),Z.flatten())
        mysp.all_positions = pos;
        #mysp.freq_list = [26.5e9,30e9,40e9]
        #freqs = [26.5e9,27e9,28e9,29e9,30e9,31e9,33e9,35e9,40e9]
        freqs = [40e9]
        mysp.freq_list = freqs
        #mysp.freq_list= np.arange(27,41)*1e9
        #mysp.add_plane_wave(0,0,-90)
        mysp.add_plane_wave(45,0,-90)
        #mysp.add_plane_wave(45,45,-90)
        #mysp.add_plane_wave(32,43,-90)
        #mysp.add_plane_wave(0,45,-90)
        
        '''
        #synthetic 1 beam lines test
        mysp = SamuraiBeamform(verbose=True,units='m')
        xlocs = 0
        ylocs = np.arange(0,0.103,0.003); yl_zpos = 0.0530
        zlocs = np.arange(0,0.103,0.003); zl_ypos = 0.0515
        #now just make single line
        yl = np.stack([np.zeros_like(ylocs),ylocs,np.ones_like(ylocs)*yl_zpos,np.zeros_like(ylocs),np.zeros_like(ylocs),np.zeros_like(ylocs)],axis=1)
        zl = np.stack([np.zeros_like(zlocs),np.ones_like(zlocs)*zl_ypos,zlocs,np.zeros_like(zlocs),np.zeros_like(zlocs),np.zeros_like(zlocs)],axis=1)
        pos = np.append(yl,zl,axis=0)
        mysp.all_positions = pos;
        mysp.freq_list = [40e9]
        mysp.add_plane_wave(0,0)
        mysp.add_plane_wave(45,0)
        mysp.add_plane_wave(0,45)
        '''
        
        #windowing
        #mysp.set_sine_window() #set a sine window weighting
        #mysp.set_cosine_sum_window_by_name('blackman-nutall')
        #mysp.set_cosine_sum_window_by_name('hamming')
        #mysp.set_sine_window()
        #mysp.plot_positions()
        
        #azel without antenna
        #mycsa_list = mysp.beamforming_farfield(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
        #azel with antenna
        #test_ant_path = './data/test_ant_pattern.csv'
        #myant = Antenna(test_ant_path,dimension=1,plane='az')
        #myap = myant['pattern']
        #mycsa,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True,antenna_pattern=myap)
        #mycsa,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),[30e9,40e9],verbose=True)
        #mycsa,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),'all',verbose=True)
        #mycsa,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),[26.5e9,40e9],verbose=True)
        mycsa,_ = mysp.beamforming_farfield_azel(np.arange(-90,90,5),np.arange(-90,90,5),[40e9],verbose=True)
        mycsa.plotter.set_plot_program('matlab')
        fig = mycsa.plot_3d()
        #mycsa.plotter.write(fig,'test.html')
        #import cProfile
        #cProfile.run("mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),freqs,verbose=True)")
        #mycsa,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),[0,1],'all',verbose=True)
        #UV beamform
        #mycsa_list,ant_vals = mysp.beamforming_farfield_uv(np.arange(-1,1.001,0.01),np.arange(-1,1.001,0.01),40e9,verbose=True,antenna_pattern=myap)
        #mycsa.plot_3d()
        #mycsa.mp.view([90,90])
        #print("Max Beamwidth ",mycsa.get_max_beamwidth())
        #mycsa.plot_uv()
        #mycsa.plot_scatter_3d()
        #print("Max-Mean = %f" %(mycsa.mag_db.max()-mycsa.mag_db.mean()))
        #bw_freqs = 'all'
        #mybw = mycsa.get_beamwidth(mycsa.get_max_beam_idx(bw_freqs),bw_freqs)
        #[az,azv] = mycsa.get_azimuth_cut(0,mean_flg=True)
        #[el,elv] = mycsa.get_elevation_cut(0,mean_flg=True)
        #mycsa.get_data('mag_db')
        #import os
        #os.chdir(r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-24-2018\meas\processed\samurai_scan\test')
        
        '''
        #testing our synthetic data capabilities
        mysp = SamuraiBeamform(verbose=True)
        pos = np.zeros((1225,6))*0.115 #random data points between 0 and 0.115m
        xlocs = np.arange(0,0.103,0.003)
        ylocs = np.arange(0,0.103,0.003)
        zlocs = 0
        [X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
        pos[:,0] = X.flatten()
        pos[:,1] = Y.flatten()
        pos[:,2] = Z.flatten()
        mysp.all_positions = pos;
        mysp.freq_list = [40e9]
        mysp.add_plane_wave(0,0)
        mycsa_list,ant_vals = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),40e9,verbose=True)
        mycsa.plot_3d()
        '''
        #mycsa.mp = mp
        #mycsa.plot_3d(rotation=[20,45,45])

    if(testb):
        #write out a horizontal sweep to s parameter files
        import os
        bf = SamuraiBeamform(r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-27-2018\calibrated\metaFile.json',verbose=True)
        #bf.set_cosine_sum_window_by_name('hamming')
        [csa,_] = bf.beamforming_farfield_azel(np.arange(-45,46,1),[0],'all',verbose=True)
        #[csa,_] = bf.beamforming_farfield_azel(np.arange(-45,46,1),np.arange(-45,45,1),[40e9],verbose=True)
        #csa.mp = mp
        #csa.plot_3d()
        os.chdir(r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\USC\Measurements\8-27-2018\calibrated')
        mys = csa.write_snp_data('az_sweep_vals/')
    
    if(testc):
        #monte carlo analysis testing for 1D setup
        '''
        #synthetic data
        mysp = SamuraiBeamform(verbose=True,units='m')
        az_vals = [] #list for appending azimuth beamformed values to
        zlocs = 0
        xlocs = np.arange(0,0.103,0.003) #default positions in m
        ylocs = np.arange(0,0.103,0.003)
        [X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
        pos = np.zeros((X.size,6))
        pos[:,0] = X.flatten()
        pos[:,1] = Y.flatten()
        pos[:,2] = Z.flatten()
        mysp.all_positions = pos;
        freqs = [40e9]
        mysp.freq_list = freqs
        mysp.add_plane_wave(43,0,-90)
        '''
        
        #measured data test
        test_path = r".\\data\\2-13-2019\\binary_aperture_planar\\metafile_binary.json"
        #test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-17-2019\aperture_vertical_polarization\binary\metafile_binary.json"
        #test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-17-2019\aperture_horizontal_polarization\binary\metafile_binary.json"
        #test_path = r".\\data\\2-13-2019\\binary_aperture_cylindrical\\metafile_binary.json"
        mysp = SamuraiBeamform(test_path,verbose=True)
        
        
        mysp.set_cosine_sum_window_by_name('hamming')
        az_pos = np.arange(-90,90,.1)
        el_pos = 0
        
        nom_csa,_ = mysp.beamforming_farfield_azel(az_pos,el_pos,40e9,verbose=False)
        nom_az_vals = nom_csa.get_azimuth_cut(0)[1]
        pos_uncert = [0.001,0.001,0.001,0,0,0]
        mycsas = []
        az_vals = []
        num_reps = 100
        for i in range(num_reps): 
            print("rep {} Complete".format(i))
            mysp.perturb_positions_normal(pos_uncert)
            cur_csa,_ = mysp.beamforming_farfield_azel(az_pos,el_pos,40e9,verbose=False)
            mycsas.append(cur_csa)
            az_vals.append(cur_csa.get_azimuth_cut(0)[1])
        az_vals = np.array(az_vals)
        az_std = np.std(az_vals,axis=0)
        
    if(testd):
        #timing test
        import timeit
        mysp = SamuraiBeamform(verbose=True,units='m')
        az_vals = [] #list for appending azimuth beamformed values to
        zlocs = 0
        xlocs = np.arange(0,0.103,0.003) #default positions in m
        ylocs = np.arange(0,0.103,0.003)
        [X,Y,Z] = np.meshgrid(xlocs,ylocs,zlocs)
        pos = np.zeros((X.size,6))
        pos[:,0] = X.flatten()
        pos[:,1] = Y.flatten()
        pos[:,2] = Z.flatten()
        mysp.all_positions = pos;
        freqs = np.arange(35e9,40.1e9,1e9)#[40e9]
        mysp.freq_list = freqs
        mysp.add_plane_wave(43,0,-90)
        az_pos = np.arange(-90,90,1)
        el_pos = np.arange(-90,90,1)
        f1 = lambda: mysp.beamforming_farfield_azel(az_pos,el_pos,'all',verbose=False)
        t = timeit.timeit(f1,number=1)
        print("Vectorized:")
        print("  Time = {}".format(t))
        print("  Time per freq = {}".format(t/len(freqs)))
        f1 = lambda: mysp.beamforming_farfield_azel(az_pos,el_pos,'all',verbose=False,use_vectorized=False)
        t = timeit.timeit(f1,number=1)
        print("Non-Vectorized:")
        print("  Time = {}".format(t))
        print("  Time per freq = {}".format(t/len(freqs)))
        #with pip install numpy (openblas)
        #Time = 13.072751499999995
        #Time per freq = 2.178791916666666
        
    if(teste):
       
       #5-17-2019 conference room #1
       test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-17-2019\aperture_vertical_polarization\binary\metafile_binary.json"
       mysp = SamuraiBeamform(test_path,verbose=True) 
       beam3_loc = [-0.001949,0.747873,-0.1964127] #in meters
       beam2_loc = [1.234315,0.864665,-0.2195737] #in meters
       mysp.metafile.add_external_marker('beam-3',beam3_loc,units='m')
       mysp.metafile.add_external_marker('beam-2',beam2_loc,units='m')
       
       '''
       #5-24-2019 conference room #2
       test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-24-2019\aperture_vertical_polarization\binary\metafile_binary.json"
       mysp = SamuraiBeamform(test_path,verbose=True) 
       loc_data_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\5-24-2019\external_data\positions\positions.json"
       mysp.metafile.add_external_marker_from_file(loc_data_path)
       '''
       '''
       #5-31-2019 conference room #3
       test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\5-31-2019\aperture_vertical_polarization\binary\metafile_binary.json"
       mysp = SamuraiBeamform(test_path,verbose=True) 
       loc_data_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\5-31-2019\external_data\positions\positions.json"
       mysp.metafile.add_external_marker_from_file(loc_data_path)
       '''
       mhm = mysp.metafile.get_external_positions_mean('meca_head').mean(0) #meca_head mean location (center of array)
       mhrm_temp = mysp.metafile.get_external_positions_mean('meca_head','rotation').mean(0)
       mhrm = mhrm_temp.copy()
       mhrm[0] = mhrm_temp[0]; mhrm[1] = mhrm_temp[2]; mhrm[2] = mhrm_temp[1] #z is y and y is z
       #mysp.metafile.plotter.matlab = mp #uncomment once matlab engine has been started
       fig = mysp.metafile.plot_external_positions() #plot the external positions
       mysp.set_cosine_sum_window_by_name('hamming')
       #mhm_t[1] = -mhm[1]
       mhrm = [0,90,0]
       mycsa,_ = mysp.beamforming_farfield_azel(np.arange(-90,90,1),np.arange(-90,90,1),[40e9],verbose=True) #beamform
       #[X,Y,Z,plot_data,caxis_min,caxis_max] = mycsa.get_3d_data('mag_db',scale=5,rotation=mhrm+np.array([0,90,0]),translation=mhm)
       [X,Y,Z,plot_data,caxis_min,caxis_max] = mycsa.get_3d_data('mag_db',scale=5,rotation=mhrm+np.array([0,0,0]))
       #[X,Y,Z,plot_data,caxis_min,caxis_max] = mycsa.get_3d_data('mag_db',scale=5,rotation=mhrm+np.array([0,0,0]))
       #X = mhm[0]+X; Y = mhm[1]+Z; Z = mhm[2]+Y
       Yt = Y.copy(); Y = Z; Z = Yt #switch axes to correct values
       X += mhm[0]; Y+=mhm[1]; Z+=mhm[2]
       mp = mysp.metafile.plotter.matlab #get the MatlabPlotter
       mp.surf(X,Y,Z,plot_data,DisplayName='Beamformed Data')
       mycsa.mp = mp
       #mp.surf(-X+mhm[0],Z+mhm[1],Y+mhm[2],plot_data,DisplayName='Beamformed Data')
       #mp.surf(Z+mhm[0],-X+mhm[1],Y+mhm[2],plot_data,DisplayName='Beamformed Data')
       mp.shading('interp')
       mp.xlabel('X')
       mp.ylabel('Y')
       mp.zlabel('Z')
       num_increments = 3 #(number of label increments)
       db_range = caxis_max-caxis_min
       mp.colorbar('XTickLabel',tuple([str(np.round(i,2)) for i in np.linspace(caxis_min,caxis_max,num_increments)]),'XTick',np.linspace(0,db_range,num_increments))
       tx_loc  = np.array([1643.37,-287.4565,696.7996])
       txl = tx_loc
       lx,ly,lz = np.split(np.stack([txl,mhm]),3,axis=1)
       mp.plot3(lx,ly,lz)
       
    if(testf):
       #monte carlos on USC measurements
       pass
        
        
        
        
        
        
        
        
        
        
        
       
       
    