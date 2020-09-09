# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 10:14:04 2019

@author: bfj
"""
import os.path
import json
import numpy as np
import matplotlib.pyplot as plt
from steeringVectors import steeringVectors, steeringVectorsWithAntenna
import sys
sys.path.insert(0, '../patterns')
import antenna as antenna

from matplotlib import rc
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as patches

from mpl_toolkits.mplot3d import Axes3D

speedOfLight = 299792458.0


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

def readSamuraiData(jsonFile):
    relativeDirectory = os.path.dirname(jsonFile)
    
    fid = open(jsonFile, 'r')
    measDict = json.load(fid)
    fid.close()
    
    # If the file has been moved then take the relative directory of the json file
    #   as the location that the data files are in.
    measFolder = measDict['working_directory']
    if not os.path.exists(measFolder):
        measFolder = relativeDirectory


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
    return freqs, measPos, measS21

class PlaneWave(object):
    def __init__(self, amplitude, elevationAngle, azimuthAngle, polarizationAngle=0.0, units='radians'):
        self.amplitude = amplitude
        self.elAngle = elevationAngle
        self.azAngle = azimuthAngle
        self.polAngle = polarizationAngle
        if units.lower()[0:3] == 'deg':
            self.elAngle *= np.pi/180.0
            self.azAngle *= np.pi/180.0
            self.polAngle *= np.pi/180.0
        self.kVec = np.zeros((3,))
        self.kVec[0] = np.sin(self.elAngle)*np.cos(self.azAngle)
        self.kVec[1] = np.sin(self.elAngle)*np.sin(self.azAngle)
        self.kVec[2] = np.cos(self.elAngle)
        
    def evalAt(self, pos, freq):
        # Return two components theta and phi
        val = self.amplitude*np.exp(1j*2.0*np.pi*freq/speedOfLight*np.dot(self.kVec, pos.transpose()).transpose())
        vecResponse = np.array([np.cos(self.polAngle)*val, np.sin(self.polAngle)*val])
        return vecResponse

def uvGrid(numPointsU, numPointsV):
    
    u = np.linspace(-1, 1, numPointsU)
    v = np.linspace(-1, 1, numPointsU)
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
    return angles, anglesUV, uu, vv, mm

# get synthetic shapes
def createSynthData(measPos, antIn, freqs, planeWaveList):
    # First figure out polarizations
    
    numFreqs = len(freqs)
    numMeasIn = measPos.shape[0]
    
    numPlaneWaves = 2
    numMeasOut = numPlaneWaves*numMeasIn
    
    polarization1 = 0.0
    polarization2 = np.pi/2.0
    
    measPosSynth = np.zeros((numMeasOut, 3))
    polarization = np.zeros((numMeasOut,))
    
    measPosSynth[:numMeasIn,:] = measPos
    measPosSynth[numMeasIn:,:] = measPos
    polarization[:numMeasIn] = polarization1
    polarization[:numMeasIn] = polarization2
    
    synthS21 = np.zeros((numMeasOut, numFreqs), dtype=np.complex128)
    
    antResponse = np.zeros((2, numFreqs, numPlaneWaves), dtype=np.complex128)
    realizedAntResponse = np.zeros((2, numFreqs, numMeasOut, numPlaneWaves), dtype=np.complex128)
    for iP, pWave in enumerate(planeWaveList):
        # E_theta, E_phi
        antResponse[0, :, iP], antResponse[1, :, iP] = antIn.evalGain(pWave.elAngle, pWave.azAngle, freqs)
    
        for iM in range(numMeasOut):
            realizedAntResponse[0,:,iM,iP] = np.cos(polarization[iM])*antResponse[0,:,iP] - np.sin(polarization[iM])*antResponse[1,:,iP]
            realizedAntResponse[1,:,iM,iP] = np.sin(polarization[iM])*antResponse[0,:,iP] + np.cos(polarization[iM])*antResponse[1,:,iP]
        
    for iF, freq in enumerate(freqs):
        for iP, pWave in enumerate(planeWaveList):
            for iM in range(numMeasOut):
            
                # Now get the planeWaveResponse - this includes the polarization of the wave
                planeWaveResponse = pWave.evalAt(measPosSynth[iM], freqs[iF])  # Theta and Phi
                # now dot onto the realized antenna response...
                synthS21[iM, iF] += np.dot(realizedAntResponse[:,iF,iM,iP].transpose().conj(), planeWaveResponse)
                
    return measPosSynth, polarization, synthS21  

###############################################################################
# Specify two plane waves
###############################################################################

planeWave1 = PlaneWave(1.0, 20, 0, polarizationAngle=110, units='degrees')
planeWave2 = PlaneWave(1.0, 10, 130, polarizationAngle=20, units='degrees')
planeWaveList = [planeWave1, planeWave2]

numPointsUV = 40;
angles, anglesUV, uu, vv, mm = uvGrid(numPointsUV, numPointsUV)

# Get antenna pattern
sage17 = {}
# Convert to meters
sage17["a"] =  7.112*10**(-3)
sage17["b"] =  3.556*10**(-3)
sage17["a1"] = 25.400*10**(-3)
sage17["b1"] = 19.812*10**(-3)
sage17["psie"] = 33.4
sage17["psih"] = 37.3

sageHorn17 = antenna.RectangularHorn(sage17)

numGammaVals = 18
gammaValsDegrees = np.linspace(0, 360, numGammaVals, endpoint=False)
gammaVals = gammaValsDegrees*np.pi/180.0

numGammaValsS = 3
gammaValsS = np.array([0, 2.0*np.pi/3.0, 4.0*np.pi/3])
gammaValsDegreesS = gammaValsS*180.0/np.pi

#dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\3-1-2019\\"
dataDir = r"S:\Measurements\Synthetic_Aperture\calibrated\3-1-2019\\"
expList = [
    "aperture_0",
#    "aperture_1",
#    "aperture_2",
#    "aperture_3",
#    "aperture_4",
#    "aperture_5"
]
jsonFilename = 'metafile.json'

experiment = expList[0]

jsonFile = os.path.join(os.path.join(dataDir, experiment), jsonFilename)

#print(jsonFile)
freqs, measPos, measS21 = readSamuraiData(jsonFile)

numMeasOrig = measPos.shape[0]
freqs = freqs[[0,-1]]
numFreqs = len(freqs)


synthPos, synthPolarizations, synthS21 = createSynthData(measPos, sageHorn17, freqs, planeWaveList)

numMeas = synthPos.shape[0]    

fig, axs = plt.subplots(2,1, figsize=(3,7))
ax = axs[0]
im = ax.scatter(synthPos[:numMeas/2,0], synthPos[:numMeas/2,1], c=np.abs(synthS21[:numMeas/2,0]))
ax.set_title(r'Magnitude at orientation $0^\circ$')
ax.set_xlabel('x position [m]')
ax.set_ylabel('y position [m]')
fig.colorbar(im, ax=ax)
#ax.colorbar()
#ax.show()
ax = axs[1]
im = ax.scatter(synthPos[numMeas/2:,0], synthPos[numMeas/2:,1], c=np.abs(synthS21[numMeas/2:,0]))
ax.set_xlabel('x position [m]')
ax.set_ylabel('y position [m]')
ax.set_title(r'Magnitude at orientation $90^\circ$')
fig.colorbar(im, ax=ax)
plt.tight_layout()
#ax.colorbar()
#ax.show()

###############################################################################
# Music decomp
###############################################################################\
covMat = np.zeros((numMeas,numMeas,numFreqs), dtype=np.complex128)
numMusicPaths = 2
musicEn = []
for iF in range(numFreqs):
    covMat = np.dot(synthS21[:,iF].reshape(-1, 1), synthS21[:,iF].reshape(1, -1).conj())
    [uI,sI,vI] = np.linalg.svd(covMat)
    unI = uI[:,numMusicPaths:]
    snI = sI[numMusicPaths:]
    enI = np.dot(unI, unI.transpose().conj())
    musicEn.append(enI)

hThetaF, musicData = steeringVectorsWithAntenna(synthPos, synthPolarizations, freqs[[0,-1]], synthS21[:,[0,-1]], angles, gammaVals, sageHorn17, musicEn, newImp=True) 
hThetaFS, musicDataS = steeringVectorsWithAntenna(synthPos, synthPolarizations, freqs[[0,-1]], synthS21[:,[0,-1]], angles, gammaValsS, sageHorn17, musicEn, newImp=True) 
#hThetaF, musicData = steeringVectorsWithAntenna(synthPos[:numMeasOrig], synthPolarizations[:numMeasOrig], freqs[[0,-1]], synthS21[:numMeasOrig,[0,-1]], angles, gammaVals, sageHorn17, musicEn, newImp=True) 

hThetaFUV = np.zeros((hThetaF.shape[0], anglesUV.shape[0], numGammaVals), dtype=np.complex128)
musicDataUV = hThetaFUV.copy()
hThetaFUV[:,mm, :] = np.nan
hThetaFUV[:,~mm, :] = hThetaF[:,:,:]

musicDataUV[:,mm, :] = np.nan
musicDataUV[:,~mm, :] = musicData[:,:,:]

hThetaFUVS = np.zeros((hThetaFS.shape[0], anglesUV.shape[0], numGammaValsS), dtype=np.complex128)
musicDataUVS = hThetaFUVS.copy()
hThetaFUVS[:,mm, :] = np.nan
hThetaFUVS[:,~mm, :] = hThetaFS[:,:,:]

musicDataUVS[:,mm, :] = np.nan
musicDataUVS[:,~mm, :] = musicDataS[:,:,:]

polarMat = np.zeros((3,3), dtype=np.float64)
polarMat[:,0] = 1.0
polarMat[:,1] = np.cos(2*gammaValsS)
polarMat[:,2] = np.sin(2*gammaValsS)

invPolarMat = np.linalg.inv(polarMat)

hThetaFUVS = np.abs(hThetaFUVS)**2
musicDataUVS = np.abs(musicDataUVS)
aVals = np.tensordot(invPolarMat, hThetaFUVS, axes=(1, 2))
aMusicVals = np.tensordot(invPolarMat, musicDataUVS, axes=(1, 2))
tVals = np.zeros((3,len(gammaVals)))
tVals[0,:] = 1.0
tVals[1,:] = np.cos(2*gammaVals)
tVals[2,:] = np.sin(2*gammaVals)


pVals = np.tensordot(aVals, tVals, axes=(0,0))
mVals = np.tensordot(aMusicVals, tVals, axes=(0,0))

#dataS = pVals[1,500,:]
#dataO = np.abs(hThetaFUV[1,500,:])**2
dataS = mVals[1,500,:]
dataO = np.abs(musicDataUV[1,500,:])
fig = plt.figure()
plt.plot(dataO)
plt.plot(dataS)
plt.show()

plotBeamforming = False
plotMusic = True
#sys.exit(0)
# Now compare ...
for iG in range(numGammaVals):
    if plotBeamforming:
        plotDataO = 20*np.log10(np.abs(hThetaFUV[1,:,iG]))
        plotDataS = 10*np.log10(pVals[1,:,iG])
        title=r'Beamforming $\gamma = $' + str(gammaValsDegrees[iG])
    
    # Music Plots
    if plotMusic:
        plotDataO = 10*np.log10(np.abs(musicDataUV[1,:,iG]))
        plotDataS = 10*np.log10(mVals[1,:,iG])
        title=r'MUSIC $\gamma = $' + str(gammaValsDegrees[iG])
    
    fig, axs = plt.subplots(3,1, figsize=(4,10))
    im0 = axs[0].imshow(plotDataO.reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet)
    cMin = np.nanmin(plotDataO)
    cMax = np.nanmax(plotDataO)
    cVals = np.linspace(cMin, cMax, 5)
    plt.colorbar(im0, ax=axs[0], ticks=cVals)
    im1 = axs[1].imshow(plotDataS.reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet)
    cMin = np.nanmin(plotDataS)
    cMax = np.nanmax(plotDataS)
    cVals = np.linspace(cMin, cMax, 5)
    plt.colorbar(im1, ax=axs[1], ticks=cVals)
    plotDataD = plotDataO - plotDataS
    im2 = axs[2].imshow(plotDataD.reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet)
    cMin = np.nanmin(plotDataD)
    cMax = np.nanmax(plotDataD)
    cVals = np.linspace(cMin, cMax, 5)
    plt.colorbar(im2, ax=axs[2], ticks=cVals)
        

sys.exit(0)

for iG in range(numGammaVals):
    #fig = plt.figure()
    #plotData = 20*np.log10(np.abs(hThetaFUV[1,:,iG]))
    #im = plt.imshow(plotData.reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    #cMin = np.nanmin(plotData)
    #cMax = np.nanmax(plotData)
    #cVals = np.linspace(cMin, cMax, 5)
    #
    #cbar = plt.colorbar(im, ticks=cVals)
    #
    #plt.xlabel('U')
    #plt.ylabel('V')
    #plt.title(r'Beamforming $\gamma$ = ' + str(gammaVals[iG]*180./np.pi))
    #plt.tight_layout()
    #plt.savefig('beamforming_'+experiment+'_vPolar_'+str(gammaValsDegrees[iG])+'_40.0.png')

    fig = plt.figure()
    plotData = 10*np.log10(np.abs(musicDataUV[1,:,iG]))
    im = plt.imshow(plotData.reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    cMin = np.nanmin(plotData)
    cMax = np.nanmax(plotData)
    cVals = np.linspace(cMin, cMax, 5)
    
    cbar = plt.colorbar(im, ticks=cVals)
    
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title(r'MUSIC $\gamma$ = ' + str(gammaVals[iG]*180./np.pi))
    plt.tight_layout()
    plt.savefig('music_'+experiment+'_vPolar_'+str(gammaValsDegrees[iG])+'_40.0.png')


sys.exit(0)

        


hThetaF = steeringVectorsWithAntenna(measPos, synthPolarizations, freqs[[0,-1]], measS21[:,[0,-1]], angles, gammaVals, sageHorn17, newImp=True) 

hThetaFUV = np.zeros((hThetaF.shape[0], anglesUV.shape[0], numGammaVals), dtype=np.complex128)
hThetaFUV[:,mm, :] = np.nan
hThetaFUV[:,~mm, :] = hThetaF[:,:,:]


for iG in range(numGammaVals):
    fig = plt.figure()
    plt.imshow(20*np.log10(np.abs(hThetaFUV[1,:,iG])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
    plt.colorbar()
    plt.xlabel('U')
    plt.ylabel('V')
    plt.title('Beamforming')
    plt.tight_layout()
    plt.savefig('beamforming_'+experiment+'_polar_'+str(gammaVals[iG])+'_40.0.png')
    #plt.show()
    
loc1 = 20090
fig = plt.figure()
plt.plot(gammaVals, 20*np.log10(np.abs(hThetaFUV[1,loc1,:])), 'o-k')
plt.xlabel(r'$\gamma$')
plt.ylabel('Power [dB]')
#plt.title('Beamforming')
plt.tight_layout()
plt.savefig('mainBeamVsGamma1aF2.png')

fig = plt.figure()
plt.plot(gammaVals, np.abs(hThetaFUV[1,loc1,:]), 'o-k')
plt.xlabel(r'$\gamma$')
plt.ylabel('Power [linear]')
#plt.title('Beamforming')
plt.tight_layout()
plt.savefig('mainBeamVsGammaLinear1aF2.png')

loc2 = 19055
fig = plt.figure()
plt.plot(gammaVals, 20*np.log10(np.abs(hThetaFUV[1,loc2,:])), 'o-k')
plt.xlabel(r'$\gamma$')
plt.ylabel('Power [dB]')
#plt.title('Beamforming')
plt.tight_layout()
plt.savefig('mainBeamVsGamma2aF2.png')

fig = plt.figure()
plt.plot(gammaVals, np.abs(hThetaFUV[1,loc2,:]), 'o-k')
plt.xlabel(r'$\gamma$')
plt.ylabel('Power [linear]')
#plt.title('Beamforming')
plt.tight_layout()
plt.savefig('mainBeamVsGammaLinear2aF2.png')

fig = plt.figure()
plt.imshow(20*np.log10(np.abs(hThetaFUV[1,:,0])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.title('Beamforming')
plt.tight_layout()
plt.savefig('beamforming_'+experiment+'_taper_'+str(taperAmplitude)+'_40.0.png')
#plt.show()



sys.exit(0)

"""
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
"""
