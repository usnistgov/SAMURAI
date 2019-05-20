# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 10:14:04 2019

@author: bfj
"""
import os.path
import json
import numpy as np
import matplotlib.pyplot as plt
from steeringVectors import steeringVectors
import sys
sys.path.insert(0, '../patterns')
import antenna as antenna

from matplotlib import rc
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as patches

from mpl_toolkits.mplot3d import Axes3D
def scatterPointsWithOrientation(points, orientation):
    """
    points: array of 3d positions
    orientation: can be either a constant vector or a vector for each point
    """
    # numPoints = points.shape[0]
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.quiver(points[:,0], points[:,1], points[:,2], orientation[:,0], orientation[:,1], orientation[:,2])
    
    minX = np.min(points[:,0])
    maxX = np.max(points[:,0])
    minY = np.min(points[:,1])
    minY = np.max(points[:,1])
    minZ = -.1
    maxZ = 1.0
    #ax.set_xlim([minX, maxX])
    #ax.set_ylim([minY, maxY])
    ax.set_zlim([minZ, maxZ])
    plt.show()

def readS21(measFolder, filename, getFreqs=False):
    freqs = None
    if getFreqs:
        useCols = (0,3,4)
    else:
        useCols = (3,4)
        
    sData = np.loadtxt(os.path.join(measFolder, filename.split()[0]), usecols=useCols)
    if getFreqs:
        freqs = sData[:, 0]
        sData = sData[:, 1:].copy()
    #print sData.shape
    cData = sData.view(dtype=np.complex128)
    return cData[:,0], freqs
    

def packagePos(positionList):
    return positionList[0:3] # Do we need to convert to meters?



# Create uv grid
numPointsUV = 200;
u = np.linspace(-1, 1, numPointsUV)
v = np.linspace(-1, 1, numPointsUV)
[uu,vv] = np.meshgrid(u,v)
mask = uu**2 + vv**2 > 1

# Now find the angles...
azVals = np.arcsin(uu)
elVals = np.arcsin(vv)
mm = mask.ravel()
angles = np.zeros((np.sum(~mm),2), dtype=np.float64)
angles[:,0] = elVals.ravel()[~mm]
angles[:,1] = azVals.ravel()[~mm]

anglesUV = np.zeros((uu.shape[0]*uu.shape[1], 2))
anglesUV[~mm, :] = angles[:,:]
anglesUV[mm, :] = np.nan


# Tapering
import scipy.signal
import scipy.interpolate

taperAmplitude = 20
# Data locations:

dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\3-1-2019\\"

expList = [
    "aperture_0",
#    "aperture_1",
#    "aperture_2",
#    "aperture_3",
#    "aperture_4",
#    "aperture_5"
]
jsonFilename = 'metafile.json'

for iE, experiment in enumerate(expList):
    jsonFile = os.path.join(os.path.join(dataDir, experiment), jsonFilename)
    fid = open(jsonFile, 'r')
    measDict = json.load(fid)
    fid.close()
    measFolder = measDict['working_directory']

    
    # Get number of measurements
    numMeas = measDict['completed_measurements'] 
    
    # Get number of frequencies
    numFreqs = measDict['vna_info']['num_pts']
    
    # Allocate data [numFreqs, numMeas]
    measS21 = np.zeros((numMeas, numFreqs), dtype=np.complex128)
    
    # Allocate spatial location
    measPosRead = np.zeros((numMeas, 3))
    
    freqs = None
    
    for iMeas, meas in enumerate(measDict['measurements']):
        #measS21[iMeas, :] = readS21(measFolder, meas['filename'])
        #measPos[iMeas, :] = packagePos(meas['position'])
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
    numPoints = measPos.shape[0]    
    
    if iE == 0:

        # Assumes square array
        numPointsX = np.int(np.sqrt(numPoints))
        numPointsY = np.int(np.sqrt(numPoints))
        dcWin = scipy.signal.chebwin(numPointsX, at=taperAmplitude) # What value for attenuation?
        lengthX = np.max(measPos[:,0]) - np.min(measPos[:,0])
        lengthY = np.max(measPos[:,1]) - np.min(measPos[:,1])
        xLocs = np.linspace(np.min(measPos[:,0]), np.max(measPos[:,0]), numPointsX)
        yLocs = np.linspace(np.min(measPos[:,1]), np.max(measPos[:,1]), numPointsY)
        
        
        # Now get the x and y taper response - we must interpolate
        xInterp = scipy.interpolate.interp1d(xLocs, dcWin, kind='cubic')
        xTapers = xInterp(measPos[:,0])
        yInterp = scipy.interpolate.interp1d(yLocs, dcWin, kind='cubic')
        yTapers = yInterp(measPos[:,1])
        taper = xTapers*yTapers


    taperedS21 = np.zeros(measS21.shape, dtype=np.complex128)
    for iF in range(numFreqs):
        taperedS21[:,iF] = measS21[:,iF]*taper
        
    #taperedS21 = measS21*taper
    taperedBF_small = steeringVectors(measPos, angles, freqs[[0,-1]], taperedS21[:,[0,-1]], newImp=True);
    taperedBF = np.zeros((taperedBF_small.shape[0], anglesUV.shape[0]), dtype=np.complex128)
    taperedBF[:,mm] = np.nan
    taperedBF[:,~mm] = taperedBF_small[:,:]
    
    hThetaF = steeringVectors(measPos, angles, freqs[[0,-1]], measS21[:,[0,-1]], newImp=True); 
    hThetaFUV = np.zeros((hThetaF.shape[0], anglesUV.shape[0]), dtype=np.complex128)
    hThetaFUV[:,mm] = np.nan
    hThetaFUV[:,~mm] = hThetaF[:,:]
    
    fig = plt.figure()
    plt.imshow(20*np.log10(np.abs(taperedBF[0,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    plt.colorbar()
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title('Tapered Beamforming')
    plt.tight_layout()
    plt.savefig('taperedBF_'+experiment+'_taper_'+str(taperAmplitude)+'_26.5.png')
    #plt.show()
    
    fig = plt.figure()
    plt.imshow(20*np.log10(np.abs(hThetaFUV[0,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    plt.colorbar()
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title('Beamforming')
    plt.tight_layout()
    plt.savefig('beamforming_'+experiment+'_taper_'+str(taperAmplitude)+'_26.5.png')
    #plt.show()

    fig = plt.figure()
    plt.imshow(20*np.log10(np.abs(taperedBF[1,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    plt.colorbar()
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title('Tapered Beamforming')
    plt.tight_layout()
    plt.savefig('taperedBF_'+experiment+'_taper_'+str(taperAmplitude)+'_40.0.png')
    #plt.show()
    
    fig = plt.figure()
    plt.imshow(20*np.log10(np.abs(hThetaFUV[1,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    plt.colorbar()
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title('Beamforming')
    plt.tight_layout()
    plt.savefig('beamforming_'+experiment+'_taper_'+str(taperAmplitude)+'_40.0.png')
    #plt.show()

    fig = plt.figure()
    plt.contourf(xLocs, yLocs, taper.reshape(numPointsX, numPointsY))
    plt.colorbar()
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Taper Values')
    plt.savefig('taper.png')
    plt.show()
    
    # Let's take some cuts
    yIndex = uu.shape[0]/2
    taper1d = 20*np.log10(np.abs(taperedBF[0,:])).reshape(uu.shape)[yIndex,:]
    nonTaper1d = 20*np.log10(np.abs(hThetaFUV[0,:])).reshape(uu.shape)[yIndex,:]
    fig = plt.figure()
    plt.plot(uu[yIndex,:], nonTaper1d, '--b', label='Not tapered')
    plt.plot(uu[yIndex,:], taper1d, '-k', label='DC tapered')
    plt.legend(loc='upper right')
    plt.xlabel('U')
    plt.title('Azimuthal Beamforming Cut')
    plt.tight_layout()
    plt.savefig('taperedCut_'+experiment+'_taper_'+str(taperAmplitude)+'_26.5.png')
    #plt.show()
    
    taper1d = 20*np.log10(np.abs(taperedBF[1,:])).reshape(uu.shape)[yIndex,:]
    nonTaper1d = 20*np.log10(np.abs(hThetaFUV[1,:])).reshape(uu.shape)[yIndex,:]
    fig = plt.figure()
    plt.plot(uu[yIndex,:], nonTaper1d, '--b', label='Not tapered')
    plt.plot(uu[yIndex,:], taper1d, '-k', label='DC tapered')
    plt.legend(loc='upper right')
    plt.xlabel('U')
    plt.title('Azimuthal Beamforming Cut')
    plt.tight_layout()
    plt.savefig('taperedCut_'+experiment+'_taper_'+str(taperAmplitude)+'_40.0.png')
    #plt.show()