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

from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform
import numpy as np

#%% Some flags for running
run_beamforming = True
build_extra = True

#%% Strings for different parts of the rst file

#format with (**metafile_kwargs)
meas_str = '''
Experiment Information
^^^^^^^^^^^^^^^^^^^^^^^^^

{experiment}

*{notes}*


VNA Sweep Settings
^^^^^^^^^^^^^^^^^^^^^

{vna_info}


'''

#format with (image_location)
image_format_str = '''

Setup Image
^^^^^^^^^^^^^^^^^^

.. image:: {0}


'''

#format with ('- :ref:`<data_dir_name_1>\n- :ref:`<data_dir_name_2>,...)
extra_info_link_str = '''

Extra Information
^^^^^^^^^^^^^^^^^^^^

Extra plots and information on each of the specific sweeps take during the measurement and their data can be found at the link below.

{0}

'''

#format with (data_dir_name,enumerated value,**plot_path_dict,**metafile_kwargs)
extra_info_page_str = ('''
                       
:orphan:

.. _data_{0}_extra_info_{1}:

#####################################################################################
Additional Information for :code:`{name}`
#####################################################################################

Experiment Information
----------------------------

{experiment}

*{notes}*


VNA Sweep Settings
--------------------------

{vna_info}


Aperture Positions (mm)
---------------------------

.. raw:: html
   :file: {aperture}

Measurement at first position
----------------------------------

.. raw:: html
    :file: {fd_meas}
    
Time Domain Result
-----------------------------

.. raw:: html
    :file: {td_meas}
    
Azimuth cut at 0 Degrees Elevation
--------------------------------------

.. raw:: html
    :file: {az_cut}

Beamformed 3D Data Plot at highest frequency
----------------------------------------------------

.. raw:: html
    :file: {bf_3d}
    
Externally Measured Positions
---------------------------------------------

.. raw:: html
    :file: {ext_pos}

''')


#%% function for finding metafiles
def find_metafiles(mydir):
    '''
    @brief take an input directory and search with a depth of 2 to find metafiles.
    Also remove anything with 'touchstone' in it. and only find 'metafile.json'
    '''
    d1 = glob.glob(os.path.join(mydir,'./metafile.json'))
    d2 = glob.glob(os.path.join(mydir,'./*/metafile.json'))
    return d1+d2

#%% constant settings
data_root = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated'

sphinx_root = '../../'
mf_name = 'metafile.json'
image_template_path = 'external_data/pictures/setup.png' #with respect to metafile dir
local_image_dir = '/data/data_metafile_info/images/' #relative to sphinx root

meas_dirs = []

#%% 2019 Data
#this should be only be a single folder (no dir1/dir2 only dir1) for nameing ease in docs. copy first of the multiple measurements metafile into root and rename to 
## optical table
mf_dir_list_2019  = []
#mf_dir_list_2019 += ['1-3-2019','2-1-2019','2-4-2019','2-6-2019','2-7-2019','2-13-2019']
#mf_dir_list_2019 += ['2-14-2019','2-20-2019','3-1-2019','3-4-2019','3-20-2019']
#mf_dir_list_2019 += ['6-17-2019','6-19-2019','7-8-2019']
## Conference Room
#mf_dir_list_2019+= ['5-17-2019','5-24-2019','5-31-2019']
# CUP Data
#mf_dir_list_2019+= ['8-7-2019','8-8-2019','8-9-2019','8-12-2019','8-13-2019','8-16-2019']
## TEST ##
#mf_dir_list_2019 += ['6-17-2019']
#mf_dir_list_2019 += ['7-8-2019']
mf_dir_list_2019 += ['1-30-2019']
##########

mf_dir_list_2019 = [os.path.join('2019',mfd) for mfd in mf_dir_list_2019]

#COMMENT THIS LINE BELOW OUT TO NOT GENERATE 2019 THINGS
meas_dirs += mf_dir_list_2019

#%% 2020 Data

out_dir = './' #output directory of files

#%% now loop through each file
hidden_toctree_list = []
dname_list = []
for meas_dir in meas_dirs:
    mfd_full = os.path.join(data_root,meas_dir)
    mf_paths = find_metafiles(mfd_full) #get all 'metafile.json' from the current directory
    
    #use the first measurement for this
    mf_path = mf_paths[0]
    print("Extracting info for {}".format(mf_path))
    mfc = MetaFileController(mf_path)
    
    #%% lets get the information on the measurement
    mf_dict = {k:mfc[k] for k in ['experiment','notes','vna_info']}
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
                
            #%% Plot creation
            fig_path_dict = {}
                
            #%% Now lets create and add a plot of the aperture
            print("Generating Aperture Position Plots")
            ap_fig = mfc.plot_aperture()
            ap_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_aperture_{}'.format(data_name,i)+'.html')
            ap_fig.write_html(ap_fig_path)
            ap_fig_path_sphinx = os.path.abspath(ap_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'aperture':ap_fig_path_sphinx})
            
            #%% now lets plot the freq domain and time domain of the first measurement
            print("Generating Frequency and Time domain Plots")
            sparam_data = TouchstoneEditor(mfc.get_filename(1,True))
            fd_fig = go.Figure()
            fd_fig.add_trace(go.Scatter(x=sparam_data.freqs,y=sparam_data.S[21].mag_db))
            fd_fig.update_layout(xaxis_title='Frequency (GHz)',yaxis_title='Magnitude (dB)')
            fd_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_fd_{}'.format(data_name,i)+'.html')
            fd_fig.write_html(fd_fig_path)
            fd_fig_path_sphinx = os.path.abspath(fd_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'fd_meas':fd_fig_path_sphinx})
            #and time domain
            td_fig = go.Figure()
            td_times,td_vals = sparam_data.S[21].calculate_time_domain_data()
            td_fig.add_trace(go.Scatter(x=td_times*1e9,y=10*np.log10(np.abs(td_vals))))
            td_fig.update_layout(xaxis_title='Time (ns)',yaxis_title='Magnitude (dB)')
            td_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_td_{}'.format(data_name,i)+'.html')
            td_fig.write_html(td_fig_path)
            td_fig_path_sphinx = os.path.abspath(td_fig_path).replace(os.sep,'/')
            fig_path_dict.update({'td_meas':td_fig_path_sphinx})
            
            #%% and a beamformed data at the max freq
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
                bf2d_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_2d_beamformed_{}'.format(data_name,i)+'.html')
                bf2d_fig.write_html(bf2d_fig_path)
                bf2d_fig_path_sphinx = os.path.abspath(bf2d_fig_path).replace(os.sep,'/')
                fig_path_dict.update({'az_cut':bf2d_fig_path_sphinx})
                
                #plot our data in 3D
                bf3d_fig = calc_synthetic_aperture.plot_3d()
                bf3d_fig_path = os.path.join(sphinx_root,local_image_dir.lstrip('/'),'{}_3d_beamformed_{}'.format(data_name,i)+'.html')
                bf3d_fig.write_html(bf3d_fig_path)
                bf3d_fig_path_sphinx = os.path.abspath(bf3d_fig_path).replace(os.sep,'/')
                fig_path_dict.update({'bf_3d':bf3d_fig_path_sphinx}) 
                
            else:
                fig_path_dict.update({'bf_3d':"N/A"}) 
                fig_path_dict.update({'az_cut':"N/A"})
            
            
            #%% External position plots
            #dont add for now
            fig_path_dict.update({'ext_pos':"Not Available for this Measurement"})
            
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
        

    
    

    
    