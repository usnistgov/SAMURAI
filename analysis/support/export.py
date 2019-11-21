
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 10:14:04 2019

@author: bfj
"""
import os.path
import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
 
#from steeringVectors import steeringVectors, steeringVectorsWithAntenna
import sys
sys.path.insert(0, '../patterns')
#import antenna as antenna

from matplotlib import rc
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as patches

from samurai.analysis.support.MUFResult import MUFResult

from mpl_toolkits.mplot3d import Axes3D

def readS21(measFolder, filename, getFreqs=False):
    freqs = None
    if getFreqs:
        useCols = (0,3,4)
    else:
        useCols = (3,4)
    sData = np.loadtxt(os.path.join(measFolder, filename.split()[0]), usecols=useCols, comments=['!', '#'])
    if getFreqs:
        freqs = sData[:, 0]
        sData = sData[:, 1:].copy()
    #print sData.shape
    cData = sData.view(dtype=np.complex128)
    return cData[:,0], freqs
    

def packagePos(positionList):
    return positionList[0:3] # Do we need to convert to meters?

def readSamuraiData(jsonFile):
    fid = open(jsonFile, 'r')
    measDict = json.load(fid)
    fid.close()
    measFolder = measDict['working_directory']


    # Get number of measurements
    numMeas = measDict['completed_measurements'] 

    # Get number of frequencies
    numFreqs = int(measDict['vna_info']['num_pts'])

    # Allocate data [numFreqs, numMeas]
    measS21 = np.zeros((numMeas, numFreqs), dtype=np.complex128)

    # Allocate spatial location
    measPosRead = np.zeros((numMeas, 3))

    freqs = None

    for iMeas, meas in enumerate(measDict['measurements']):
        if iMeas == 0:
            measS21[iMeas, :], freqs = readS21(measFolder, meas['filename'], getFreqs=True)
        else:
            measS21[iMeas, :], _ = readS21(measFolder, meas['filename'], getFreqs=False)
            measPosRead[iMeas, :] = packagePos(meas['position'])
                
                
    measPos = measPosRead.copy()

    # Reorder (x, y, z) -> (y,z,x) since the x is the propagation direction (const for synthetic array)
    xVals = measPos[:,0].copy()
    yVals = measPos[:,1].copy()
    zVals = measPos[:,2].copy()
    measPos[:,0] = yVals
    measPos[:,1] = zVals
    measPos[:,2] = xVals

    measPos = measPos * (10.0**(-3)) # Convert mm to m
    measPos = measPos - np.average(measPos, axis=0)

    freqs = freqs*(10**9) # Convert GHz to Hz
    return freqs, measPos, measS21


def readSamuraiDataMeas(jsonFile):
    fid = open(jsonFile, 'r')
    measDict = json.load(fid)
    fid.close()
    measFolder = measDict['working_directory']


    # Get number of measurements
    numMeas = measDict['completed_measurements'] 

    # Get number of frequencies
    numFreqs = int(measDict['vna_info']['num_pts'])

    # Allocate data [numFreqs, numMeas]
    measS21 = np.zeros((numMeas, numFreqs, 9), dtype=np.complex128)

    # Allocate spatial location
    measPosRead = np.zeros((numMeas, 3))

    freqs = None

    loadNomDict = {}
    loadNomDict['load_nominal'] = True

    for iMeas, meas in enumerate(measDict['measurements']):
        # Now we are reading .meas files...
        #print("Measfolder {}".format(measFolder))
        #print("meas: ".format(meas['filename']))
        measFile = meas['filename']
        measPath = os.path.join(measFolder, measFile)
        myMufResult = MUFResult(measPath,**loadNomDict)
        nomVal = myMufResult.nominal
        measS21[iMeas, :] = nomVal.raw_data
        measPosRead[iMeas, :] = packagePos(meas['position'])
        if iMeas == 0:
            freqs = nomVal.freq_list
                
    measPos = measPosRead.copy()

    # Reorder (x, y, z) -> (y,z,x) since the x is the propagation direction (const for synthetic array)
    zVals = -measPos[:,0].copy()
    rVals = measPos[:,1].copy()
    thVals = measPos[:,2].copy()
    measPos[:,0] = rVals*np.cos(thVals*np.pi/180.)
    measPos[:,1] = rVals*np.sin(thVals*np.pi/180.)
    measPos[:,2] = zVals

    measPos = measPos * (10.0**(-3)) # Convert mm to m
    measPos = measPos - np.average(measPos, axis=0)

    freqs = freqs*(10**9) # Convert GHz to Hz
    return freqs, measPos, measS21

#dataDir = "/home/bfj/data/reverb/081519/calibrated_data"
#dataDir = r"C:\Users\bfj\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu18.04onWindows_79rhkp1fndgsc\LocalState\rootfs\home\bfj\data/reverb/081519/calibrated_data"
dataDir = r"Q:\public\Reverb Measurements Wireless\Rob Jones\data\bluetest_maria_synth_apert_recreate\081519\calibrated_data"

jsonFilename = 'metafile.json'

jsonFilename = os.path.join(dataDir, jsonFilename)

freqs, measPos, measS21 = readSamuraiDataMeas(jsonFilename)

sio.savemat('jonesReverb.mat', {'freqs': freqs, 'measPos': measPos, 'measS21': measS21})
