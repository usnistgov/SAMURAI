"""
Created on Tue Jul 30 11:32:39 2019
This is a template script to test the approximate response of the channel
This will give a PDP at a single point, and a beamformed set at a signle frequency
PLEASE DO NOT COMMIT EXPERIMENT SPECIFIC CHANGES TO THIS SCRIPT.
@author: ajw5
"""
###############################################################################
gather_flg = True  #whether or not to gather the data
process_flg = True #whether or not to process the data
aoa_flg = True     #do we do aoa measurements (if process_flag=True)
pdp_flg = True     #do we do pdp measurements (if process_flag=True)
###############################################################################

##############################################################################
#first lets gather the data
if gather_flg:
        from samurai.acquisition.SAMURAI_System import SAMURAI_System
        from samurai.acquisition.instrument_control.PnaController import PnaController

        mysam = SAMURAI_System()
        mysam.connect_rx_positioner()

        pna_visa_addr ='TCPIP0::192.168.0.2::inst0::INSTR'
        mypna = PnaController(pna_visa_addr)

        if aoa_flg:

                #set the location of our CSV file containing our sweep points
                position_file = '../synthetic_aperture/raw/position_templates/samurai_planar_vp.csv'
                output_dir = './' #data output directory
                meas_freq = 40e9  #single frequency to measure at

                #info to put into metafile
                metafile_info_dict = {}
                metafile_info_dict["experiment"] = 'preliminary channel testing measurements'
                metafile_info_dict["notes"] = None

                #setup the vna for single frequency sweep
                mypna.setup_s_param_measurement([31])
                mypna.set_freq_sweep(meas_freq,meas_freq,num_pts=1)
                mypna.write('if_bandwidth',100)
                mypna.write('power',0)
                mypna.set_continuous_trigger('OFF')

                #now run the system
                mysam.csv_sweep(output_dir,position_file,
                            metafile_header_values=metafile_info_dict,
                            external_meas_obj=PnaController,
                            external_meas_obj_init_args=(pna_visa_addr,),
                            external_meas_obj_meas_args=({3:2},))

        if pdp_flg:
                mysam.set_position([0,80,60,0,0,0])
                mypna.setup_s_param_measurement([31])
                mypna.set_freq_sweep(26.5e9,40e9,num_pts=1351)
                mypna.write('if_bandwidth',100)
                mypna.measure_s_params('meas_all_freqs.s2p',{3:2})

        mysam.disconnect_rx_positioner()

#now lets process it
if process_flg:
        from samurai.base.SamuraiPlotter import SamuraiPlotter
        import numpy as np

        sp = SamuraiPlotter('matplotlib')

        if aoa_flg:
                from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform
                metafile_path = './metafile.json'

                mysp = SamuraiBeamform(metafile_path,verbose=True)
                mysp.set_cosine_sum_window_by_name('hamming')
                mycsa = mysp.beamforming_farfield_azel(np.arange(-90,90,1),
                                                         np.arange(-90,90,1),[meas_freq],
                                                         verbose=True) #beamform
                fig = mycsa.plot_3d()
                fig.layout['scene']['aspectmode']='cube'
                fig.show(renderer='browser')

        if pdp_flg:
                from samurai.base.TouchstoneEditor import SnpEditor
                file_path = './meas_all_freqs.s2p'
                snp = SnpEditor(file_path)
                times,td_data = snp.S[21].calculate_time_domain_data()
                sp.plot(times,20.*np.log10(np.abs(td_data)))