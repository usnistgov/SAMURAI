# -*- coding: utf-8 -*-
"""
@date Wed Feb 12 08:43:02 2020

@brief Extract information on each measurement from the metafile, then put it
int a *.rst file. This should also try and get pictures from each day and add them
to the *.rst file

@author: ajw5
"""

import os
import shutil
import plotly.graph_objs as go
import glob

from samurai.analysis.support.MetaFileController import MetaFileController
from samurai.base.TouchstoneEditor import TouchstoneEditor
from samurai.base.SamuraiDict import SamuraiDict

from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform
import numpy as np

from metadata_templates import meas_str,image_format_str,extra_info_link_str,extra_info_page_str,fig_how_to,ext_pos_str

#%% Some flags for running
run_beamforming = False
gen_figs = False
build_extra = True


#%% function for finding metafiles
def find_metafiles(mydir):
    '''
    @brief take an input directory and search with a depth of 2 to find metafiles.
    Also remove anything with 'touchstone' in it. and only find 'metafile.json'
    '''
    d1 = glob.glob(os.path.join(mydir,'./metafile.json'))
    d2 = glob.glob(os.path.join(mydir,'./*/metafile.json'))
    d = d1+d2
    for v in d: # remove touchstone directory
        if 'touchstone' in v:
            d.remove(v)
    return d

#%% constant settings
data_root = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated'

sphinx_root = '../../'
mf_name = 'metafile.json'
image_template_path = 'external_data/pictures/setup.png' #with respect to metafile dir
local_image_dir = '/data/data_metafile_info/images/' #relative to sphinx root

meas_dirs = []

#%% 2019 Data

'''
mf_dir_list_2019  = []
mf_dir_list_2019 += ['1-30-2019']
mf_dir_list_2019 += ['2-1-2019','2-4-2019','2-6-2019','2-7-2019']
mf_dir_list_2019 += ['2-13-2019','2-14-2019','2-20-2019']
mf_dir_list_2019 += ['3-1-2019','3-4-2019']
mf_dir_list_2019 += ['6-17-2019','6-19-2019']
mf_dir_list_2019 += ['7-8-2019']
mf_dir_list_2019 = [os.path.join('2019',mfd) for mfd in mf_dir_list_2019]
meas_dirs += mf_dir_list_2019
'''
'''
## Conference Room
mf_dir_list_conf = ['5-17-2019','5-24-2019','5-31-2019']
mf_dir_list_conf = [os.path.join('Conference_Room',mfd) for mfd in mf_dir_list_conf]
meas_dirs += mf_dir_list_conf
'''

# CUP Data
mf_dir_list_cup  = ['8-7-2019','8-8-2019','8-9-2019','8-12-2019','8-13-2019','8-16-2019']
#mf_dir_list_cup  = ['8-9-2019']
mf_dir_list_cup  = [os.path.join('Central_Utility_Plant',mfd) for mfd in mf_dir_list_cup]
meas_dirs += mf_dir_list_cup

#%% 2020 Data

out_dir = './' #output directory of files

#%% now loop through each file
hidden_toctree_list = []
dname_list = []
for meas_dir in meas_dirs:
    mfd_full = os.path.join(data_root,meas_dir)
    mf_paths = find_metafiles(mfd_full) #get all 'metafile.json' from the current directory
    
    #use the first measurement for this
    if not mf_paths: #if its an empty list then write out blank
        rst_str = "NO DATA FOUND!"
        out_file_path = os.path.join(out_dir,os.path.basename(meas_dir)+'.auto.rst')
        with open(out_file_path,'w+') as f:
            f.write(rst_str)
        print("No Data Found for {}, Skipping".format(meas_dir))
        continue
        
    mf_path = mf_paths[0]
    print("Extracting info for {}".format(mf_path))
    mfc = MetaFileController(mf_path)
    
    #%% lets get the information on the measurement
    mf_dict = {k:mfc[k] for k in ['experiment','notes','vna_info']}
    unused_vna_keys = ['command_dictionary_path','connection_address']
    for k in unused_vna_keys: #remove unneeded info
        mf_dict['vna_info'].pop(k,None) 
    mf_dict['vna_info'] = mf_dict['vna_info'].get_rst_str()
    
    data_name = os.path.split(mfd_full)[1]
    dname_list.append(data_name)
    
    #and add it to the rst file
    rst_str = meas_str.format(**mf_dict)

    #%% add the image if available
    image_path = os.path.join(mfd_full,image_template_path)
    if os.path.exists(image_path): #if there is an image
        
        #copy the image from the network drive to local
        image_local_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),data_name+'.png')
        image_path_out = shutil.copy(image_path,image_local_path)
        #the image path in the rst file must be relative to sphinx root because we
        #are using the include directive on this auto generated file.
        rst_image_path = os.path.join(local_image_dir,data_name+'.png')
    
        image_str = image_format_str.format(rst_image_path.replace(os.sep,'/'))
        rst_str+=image_str

    #%% Now lets find and loop through metafiles to plot our multiple measurements
    link_str_list = []
    if build_extra:
        for i,mf_path in enumerate(mf_paths):
            
            mf_name = os.path.relpath(mf_path,os.path.join(mfd_full,'../')) #name relative to directory
            mfc = MetaFileController(mf_path)
                
            #%% Plot creation
            fig_path_dict = {}
                
            #%% Now lets create and add a plot of the aperture
            
            #update paths
            ap_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_aperture_{}'.format(data_name,i)+'.html')
            ap_fig_path_sphinx = os.path.abspath(ap_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'aperture':ap_fig_path_sphinx})
            ap_json_path = os.path.splitext(ap_fig_path)[0]+'.auto.json'
            ap_json_path_sphinx = os.path.join('/',os.path.relpath(ap_json_path,sphinx_root)).replace(os.sep,'/')
            fig_path_dict.update({'aperture_data':ap_json_path_sphinx})
            
            #and plot
            if gen_figs:
                print("Generating Aperture Position Plots")
                ap_fig = mfc.plot_aperture()
                ap_fig.write_html(ap_fig_path)
                ap_json = SamuraiDict(); ap_json.update({'how_to':fig_how_to})
                ap_json.update(ap_fig.to_dict());  ap_json.write(ap_json_path)
            
            #%% now lets plot the freq domain and time domain of the first measurement
            
            #update the paths
            fd_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_fd_{}'.format(data_name,i)+'.html')
            fd_fig_path_sphinx = os.path.abspath(fd_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'fd_meas':fd_fig_path_sphinx})
            fd_json_path = os.path.splitext(fd_fig_path)[0]+'.auto.json'
            fd_json_path_sphinx = os.path.join('/',os.path.relpath(fd_json_path,sphinx_root)).replace(os.sep,'/')
            fig_path_dict.update({'fd_meas_data':fd_json_path_sphinx})
            td_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_td_{}'.format(data_name,i)+'.html')
            td_fig_path_sphinx = os.path.abspath(td_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'td_meas':td_fig_path_sphinx})
            td_json_path = os.path.splitext(fd_fig_path)[0]+'.auto.json'
            td_json_path_sphinx = os.path.join('/',os.path.relpath(td_json_path,sphinx_root)).replace(os.sep,'/')
            fig_path_dict.update({'td_meas_data':td_json_path_sphinx})
            
            #and plot
            if gen_figs:
                print("Generating Frequency and Time domain Plots")
                sparam_data = TouchstoneEditor(mfc.get_filename(1,True))
                fd_fig = go.Figure()
                fd_fig.add_trace(go.Scatter(x=sparam_data.freqs/1e9,y=sparam_data.S[21].mag_db))
                fd_fig.update_layout(xaxis_title='Frequency (GHz)',yaxis_title='Magnitude (dB)')
                fd_fig.write_html(fd_fig_path)
                fd_json = SamuraiDict(); fd_json.update({'how_to':fig_how_to})
                fd_json.update(fd_fig.to_dict());  fd_json.write(fd_json_path)
    
                #and time domain
                td_fig = go.Figure()
                td_times,td_vals = sparam_data.S[21].calculate_time_domain_data(window='sinc2')
                td_fig.add_trace(go.Scatter(x=td_times*1e9,y=10*np.log10(np.abs(td_vals))))
                td_fig.update_layout(xaxis_title='Time (ns)',yaxis_title='Magnitude (dB)')
                td_fig.write_html(td_fig_path)
                td_json = SamuraiDict(); td_json.update({'how_to':fig_how_to})
                td_json.update(td_fig.to_dict());  td_json.write(td_json_path)
            
            
            #%% and a beamformed data at the max freq
            #now save out to the paths #doesnt need beamforming to run
            bf2d_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_2d_beamformed_{}'.format(data_name,i)+'.html')
            bf2d_fig_path_sphinx = os.path.abspath(bf2d_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'az_cut':bf2d_fig_path_sphinx})
            bf2d_json_path = os.path.splitext(bf2d_fig_path)[0]+'.auto.json'
            bf2d_json_path_sphinx = os.path.join('/',os.path.relpath(bf2d_json_path,sphinx_root)).replace(os.sep,'/')
            fig_path_dict.update({'az_cut_data':bf2d_json_path_sphinx})
            
            bf3d_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_3d_beamformed_{}'.format(data_name,i)+'.html')
            bf3d_fig_path_sphinx = os.path.abspath(bf3d_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'bf_3d':bf3d_fig_path_sphinx}) 
            bf3d_json_path = os.path.splitext(bf3d_fig_path)[0]+'.auto.json'
            bf3d_json_path_sphinx = os.path.join('/',os.path.relpath(bf3d_json_path,sphinx_root)).replace(os.sep,'/')
            fig_path_dict.update({'bf_3d_data':bf3d_json_path_sphinx})
            
            
            if gen_figs:
                if run_beamforming:
                    print("Generating Beamforming Plots")
                    #create our beamforming class
                    my_samurai_beamform = SamuraiBeamform(mf_path,verbose=True)
                    
                    #add a hamming window to reduce sidelobes
                    my_samurai_beamform.set_cosine_sum_window_by_name('hamming')
                    
                    #calulcation frequency
                    calc_freq = my_samurai_beamform.all_s_parameter_data[0].freqs[-1]
                    
                    #perform beamforming 3d
                    calc_synthetic_aperture = my_samurai_beamform.beamforming_farfield_azel(
                                                    np.arange(-90,90,1),np.arange(-90,90,1),freq_list=[calc_freq])
                    
                    #plot azimuth cut at 0 elevation
                   
                    az2d,v2d = calc_synthetic_aperture.get_azimuth_cut(0,calc_freq)
                    bf2d_fig = go.Figure()
                    bf2d_fig.add_trace(go.Scatter(x=az2d,y=v2d[:,0]))
                    bf2d_fig.update_layout(xaxis_title='Azimuth Angle (degrees)',yaxis_title='Magnitude dB')
                    bf2d_fig.write_html(bf2d_fig_path)
                    bf2d_json = SamuraiDict(); bf2d_json.update({'how_to':fig_how_to})
                    bf2d_json.update(bf2d_fig.to_dict());  bf2d_json.write(bf2d_json_path)
                    
                    #plot our data in 3D
                    bf3d_fig = calc_synthetic_aperture.plot_3d()
                    bf3d_fig.write_html(bf3d_fig_path)
                    bf3d_json = SamuraiDict(); bf3d_json.update({'how_to':fig_how_to})
                    bf3d_json.update(bf3d_fig.to_dict());  bf3d_json.write(bf3d_json_path)
                
                
            
            
            #%% External position plots
            #dont add for now
            if False: #make conditional for adding external position plots
                ext_pos = ext_pos_str.format(ext_pos='path/to/plot.html',ext_pos_data='path/to/data.json')
            else:
                ext_pos = "Not Available for this Measurement"
            fig_path_dict.update({'ext_pos_str':ext_pos})
            
            #%% add metafile info to extra info page
            fig_path_dict.update(mf_dict)
            
            #%% extra information with plots and whatnot
            
            #html 'raw' directive requires system abspath
            extra_rst_str = extra_info_page_str.format(data_name,i,name=os.path.split(mf_name)[0],**fig_path_dict)
            
            #save out the extra info
            extra_out_name = data_name+'_extra_{}.auto.rst'.format(i)
            extra_out_file_path = os.path.join(out_dir,extra_out_name)
            with open(extra_out_file_path,'w+') as f:
                f.write(extra_rst_str)
            
            #add the link to the file
            ref_str = "   - :ref:`{}`".format('data_{0}_extra_info_{1}'.format(data_name,i))
            link_str_list.append(ref_str)
        
    
    #%% now save out the regular page
    
    #add the link to rst_str
    rst_str += extra_info_link_str.format('\n'.join(link_str_list))
        
    out_file_path = os.path.join(out_dir,data_name+'.auto.rst')
    with open(out_file_path,'w+') as f:
        f.write(rst_str)
        

    
    

    
    