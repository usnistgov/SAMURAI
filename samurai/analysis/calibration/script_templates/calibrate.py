# -*- coding: utf-8 -*-
"""
@date Mon Jul 15 10:26:15 2019
@brief Script to run samurai calibration routine
@author: ajw5
"""

from samurai.analysis.calibration.CalibrateSamurai import CalibrateSamurai
from samurai.analysis.support.MetafileController import evenly_split_metafile
import os

# Get the path relative to the file
cur_path = os.path.realpath(__file__)
wdir = os.path.realpath(os.path.join(os.path.dirname(cur_path),'../'))

# REQUIRED path options. The default is for the typical SAMURAI directory structure
# Likely only the output_directory will need to be changed
input_metafile_path = os.path.join(wdir,r"synthetic_aperture\metafile.json")
cal_solution_path = os.path.join(wdir,r"cal\calibration_pre\cal_pre_vnauncert_Results\Solution.meas")
gthru_path = os.path.join(wdir,r"cal\calibration_pre\gthru.s2p")
output_directory = os.path.join(wdir,'../calibrated/<measurement-year>/<measurement-date-mm-dd-yy>/')

# Now lets split our metafile (if multiple scans were run together)
out_folder_labels = ['aperture_vertical','aperture_horizontal']
in_mf_path_list = evenly_split_metafile(input_metafile_path,len(out_folder_labels))

# Finally lets calibrate
for i,in_mf in enumerate(in_mf_path_list):
    out_dir = os.path.join(output_directory,out_folder_labels[i])
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    csa = CalibrateSamurai(in_mf,out_dir,
                 cal_solution_path,gthru_path)
    csa.populate_post_proc_and_calibrate()
    print('DONE. Results in '+out_dir)
