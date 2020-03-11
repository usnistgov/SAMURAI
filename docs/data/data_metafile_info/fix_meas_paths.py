"""
@date Wed Feb 12 08:43:02 2020

@brief Correct *.meas paths to have the correct paths. 
Currently they use absolute paths that are pointing to the wrong location

@author: ajw5
"""

import os
import glob

from samurai.analysis.support.MetaFileController import MetaFileController,set_metafile_meas_relative
from samurai.analysis.support.MUFResult import MUFResult
from samurai.base.generic import ProgressCounter

#%% function for finding our metafiles
def find_metafiles(mydir):
    '''
    @brief take an input directory and search with a depth of 2 to find metafiles.
    '''
    d1 = glob.glob(os.path.join(mydir,'./metafile.json'))
    d2 = glob.glob(os.path.join(mydir,'./*/metafile.json'))
    d = d1+d2
    return d

#%% Now lets actually fix them

wdir = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated"

test_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\2019\7-8-2019\meas_relative.meas"

mf_dirs = []
mf_2019 = [os.path.join(wdir,'2019',d) for d in 
                  ['7-8-2019']]
#mf_cup = [os.path.join(wdir,'Central_Utility_Plant',d) for d in 
#                  ['8-7-2019','8-8-2019','8-9-2019','8-12-2019','8-13-2019','8-16-2019']]
#mf_conf= [os.path.join(wdir,'Conference_Room',d) for d in 
#                  ['5-17-2019','5-24-2019','5-31-2019']]
#mf_dirs += mf_cup   #CUP
#mf_dirs += mf_conf  #Conference room
mf_dirs += mf_2019

for mf_dir in mf_dirs: #go through each directory
    print("Correcting {}".format(mf_dir))
    mf_paths = find_metafiles(mf_dir)
    for i,mf_path in enumerate(mf_paths): #go through each metafile found
        print("   Metafile {}".format(i))
        # Load the metafile without loading any data
        set_metafile_meas_relative(mf_path)
        '''
        mf = MetaFileController(mf_path,verify=True)
        fpaths = mf.filenames #get the filenames
        fpaths = [fpath for fpath in fpaths if '.meas' in fpath]
        mypc = ProgressCounter(len(fpaths),'    Correcting Path - ')
        for i,fpath in enumerate(fpaths): #now loop through each meas file
            set_meas_path_relative(fpath)
            mypc.update()
        mypc.finalize()
        '''
    
    
