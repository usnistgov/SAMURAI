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

def contourPlot(x, y, exact, mask, radius = 10, title = None, filename = None, 
                db_mask=False, xlabel=None, ylabel=None, intTicks=False, vmaxIn=None):
    exact[mask] = 0.0
    if db_mask:
        maskDb = dbMask(exact)
        exact[maskDb] = 0.0
        
    fig , ax = plt.subplots(1,1, figsize=(10,10))
 
    vmin = np.nanmin(np.nanmin(exact))
    vmax = np.nanmax(np.nanmax(exact))
    if not vmaxIn is None:
        vmax = vmaxIn
    
    if intTicks:
        vmin = 0
        vmax = np.ceil(vmax)
        vmax = 3
        tickVals = np.linspace(vmin, vmax, vmax + 1, endpoint=True)
        tickStrings = [r'0', r'1', r'2', r'$> 3$']
    else:
        tickVals = np.linspace(vmin, vmax, 5)
        
    print('vmin, vmax = ', vmin, vmax)
    
    cmap = plt.get_cmap('jet')
                        
    start = vmin
    stop = vmax
    #colors = cmap(np.linspace(start, stop, cmap.N))
    # Create a new colormap from those colors
    #color_map = LinearSegmentedColormap.from_list(None , colors)
    
    #fig, ax = plt.subplots(figsize=(6, 6))
    rVal = radius * 1.05
    im = plt.imshow(np.flipud(exact), extent=[-rVal, rVal, -rVal, rVal], vmin=vmin, vmax=vmax, cmap=plt.cm.CMRmap) #plt.cm.jet)

    circle = patches.Circle((0, 0), radius,  facecolor='#EEEEEE', transform=ax.transData)
    #im.colorbar()
    #im.set_clip_path(circle)
    im.set_clip_path(circle)
    #print "ax xticks: ", ax.get_xticks()
    #ax.set_yticks(ax.get_xticks())
    xyTickVals = np.linspace(-radius, radius, 5)
    plt.xticks(xyTickVals)
    plt.yticks(xyTickVals)

    if not xlabel is None:
        ax.set_xlabel(xlabel)
    else:
        ax.set_xlabel(r'$x$ coordinate ($\eta$)')

    if not ylabel is None:
        ax.set_ylabel(ylabel)
    else:
        ax.set_ylabel(r'$y$ coordinate ($\eta$)')


    if not title is None:
        plt.title(title)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad="1%")

    cb = fig.colorbar(im, ticks=tickVals, cax=cax)
           
    if intTicks:
        #cb.ax.set_yticklabels(['%d' % (val) for val in tickVals])
        cb.ax.set_yticklabels(tickStrings)
    else:
        if not vmaxIn is None:
            #tV = cb.ax.get_yticks()
            tL = ['%0.3f' % (val) for val in tickVals]
            
            tL[-1] = r'$> $' + tL[-1]
            cb.ax.set_yticklabels(tL)
        else:
            cb.ax.set_yticklabels(['%0.3f' % (val) for val in tickVals])
    #    plt.colorbar(im, cax=cax)   

   
    #plt.colorbar()    
    if not filename is None:
        plt.savefig(filename + '.png')
        #if doPdf:
        #    plt.savefig(filename + '.pdf')



# Data locations:
exp = '020719'
    
if exp == '020719':
    dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\\"
    experimentDir = '2-7-2019'
    subdir = ''
    jsonFile = 'metaFile.json'
elif exp == '020619':
    dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\\"
    experimentDir = '2-6-2019'
    subdir = ''
    jsonFile = 'metaFile.json'
elif exp == '021319':
    dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\\"
    experimentDir = '2-13-2019'
    subdir = 'synthetic_aperture'
    jsonFile = 'metaFile_split_0.json'
    
dataDir = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\\calibrated\\"
experimentDir = '3-1-2019'
subdir = 'aperture_0'
jsonFile = 'metafile.json'


measFolder = os.path.join(os.path.join(dataDir, experimentDir), subdir)
jsonFile = os.path.join(measFolder, jsonFile)
# Load the data from json

fid = open(jsonFile, 'r')
measDict = json.load(fid)
fid.close()

# Get number of measurements
numMeas = measDict['completed_measurements'] 

# Get number of frequencies
numFreqs = measDict['vna_info']['num_pts']

# Allocate data [numFreqs, numMeas]
measS21 = np.zeros((numMeas, numFreqs), dtype=np.complex128)

# Allocate spatial location
measPosRead = np.zeros((numMeas, 3))

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

freqs = None

for iMeas, meas in enumerate(measDict['measurements']):
    #measS21[iMeas, :] = readS21(measFolder, meas['filename'])
    #measPos[iMeas, :] = packagePos(meas['position'])
    if iMeas == 0:
        measS21[iMeas, :], freqs = readS21(measFolder, meas['filename'], getFreqs=True)
    else:
        measS21[iMeas, :], _ = readS21(measFolder, meas['filename'], getFreqs=False)
    measPosRead[iMeas, :] = packagePos(meas['position'])
    #sys.exit(0)

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

# Create uv grid
numPointsUV = 100
u = np.linspace(-1, 1, numPointsUV)
v = np.linspace(-1, 1, numPointsUV)
[uu,vv] = np.meshgrid(u,v)
mask = uu**2 + vv**2 > 1

# Now find the angles...
azVals = np.arcsin(uu)
elVals = np.arcsin(vv)

# Determine number of angles
# Allocate angle grid
#dEl = 1.0 #; % Needs to be a divisor of 90
#dAz = 1.0 #; % in degrees

#dEl = dEl*np.pi/180.0
#dAz = dAz*np.pi/180.0

#elVals = np.linspace(-np.pi/2, np.pi/2, (np.pi/2)/dEl + 1)
#azVals = np.linspace(-np.pi/2, np.pi/2, (np.pi)/dAz)
#[az, el] = np.meshgrid(azVals, elVals)
mm = mask.ravel()
angles = np.zeros((np.sum(~mm),2), dtype=np.float64)
angles[:,0] = elVals.ravel()[~mm]
angles[:,1] = azVals.ravel()[~mm]

anglesUV = np.zeros((uu.shape[0]*uu.shape[1], 2))
anglesUV[~mm, :] = angles[:,:]
anglesUV[mm, :] = np.nan

freqStep = 1000
# Now call steering vector


from timeit import default_timer as timer
start = timer()
hThetaF = steeringVectors(measPos, angles, freqs[::freqStep], measS21[:,::freqStep], newImp=False); 
end1 = timer()
hThetaF2 = steeringVectors(measPos, angles, freqs[::freqStep], measS21[:,::freqStep], newImp=True); 
end2 = timer()
print(end1 - start)
print(end2 - end1)

hThetaFUV = np.zeros((hThetaF.shape[0], anglesUV.shape[0]), dtype=np.complex128)
hThetaFUV[:,mm] = np.nan
hThetaFUV[:,~mm] = hThetaF[:,:]
fig = plt.figure()
plt.contourf(uu,vv,20*np.log10(np.abs(hThetaFUV[0,:])).reshape(uu.shape))
plt.xlabel('U')
plt.ylabel('V')
plt.colorbar()
plt.savefig('naiveImp.png')
plt.show()

hThetaFUV2 = np.zeros((hThetaF2.shape[0], anglesUV.shape[0]), dtype=np.complex128)
hThetaFUV2[:,mm] = np.nan
hThetaFUV2[:,~mm] = hThetaF2[:,:]
fig = plt.figure()
plt.contourf(uu,vv,20*np.log10(np.abs(hThetaFUV2[0,:])).reshape(uu.shape))
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.savefig('tensorImp.png')
plt.show()

fig = plt.figure()
plt.contourf(uu,vv,20*np.log10(np.abs(hThetaFUV[0,:] - hThetaFUV2[0,:])).reshape(uu.shape))
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.show()
plt.savefig('diff.png')

# Tapering
import scipy.signal
import scipy.interpolate
numPoints = measPos.shape[0]
# Assumes square array
numPointsX = np.int(np.sqrt(numPoints))
numPointsY = np.int(np.sqrt(numPoints))
dcWin = scipy.signal.chebwin(numPointsX, at=30) # What value for attenuation?
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
plt.savefig('taperedBF_26.5.png')
#plt.show()

fig = plt.figure()
plt.imshow(20*np.log10(np.abs(hThetaFUV[0,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.title('Beamforming')
plt.tight_layout()
plt.savefig('beamforming_26.5.png')
#plt.show()


# Let's take some cuts
yIndex = uu.shape[0]/2
taper1d = 20*np.log10(np.abs(taperedBF[0,:])).reshape(uu.shape)[yIndex,:]
nonTaper1d = 20*np.log10(np.abs(hThetaFUV[0,:])).reshape(uu.shape)[yIndex,:]
fig = plt.figure()
plt.plot(uu[yIndex,:], nonTaper1d, '--b', label='Not tapered')
plt.plot(uu[yIndex,:], taper1d, '-k', label='DC tapered')
plt.legend(loc='upper right')
plt.xlabel('U')
plt.title('Tapered Beamforming Cut')
plt.tight_layout()
plt.ylim([-60,0])
plt.savefig('taperedCut_26.5.png')
#plt.show()

fig = plt.figure()
plt.imshow(20*np.log10(np.abs(taperedBF[1,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.title('Tapered Beamforming')
plt.tight_layout()
plt.savefig('taperedBF_40.0.png')
#plt.show()

fig = plt.figure()
plt.imshow(20*np.log10(np.abs(hThetaFUV[1,:])).reshape(uu.shape), extent=[-1.0, 1.0, -1.0, 1.0], cmap=plt.cm.jet) #plt.cm.jet)
plt.colorbar()
plt.xlabel('U')
plt.ylabel('V')
plt.title('Beamforming')
plt.tight_layout()
plt.savefig('beamforming_40.0.png')
#plt.show()


# Let's take some cuts
yIndex = uu.shape[0]/2
taper1d = 20*np.log10(np.abs(taperedBF[1,:])).reshape(uu.shape)[yIndex,:]
nonTaper1d = 20*np.log10(np.abs(hThetaFUV[1,:])).reshape(uu.shape)[yIndex,:]
fig = plt.figure()
plt.plot(uu[yIndex,:], nonTaper1d, '--b', label='Not tapered')
plt.plot(uu[yIndex,:], taper1d, '-k', label='DC tapered')
plt.legend(loc='upper right')
plt.xlabel('U')
plt.title('Tapered Beamforming Cut')
plt.ylim([-60,0])
plt.tight_layout()
plt.savefig('taperedCut_40.0.png')
#plt.show()


fig = plt.figure()
#plt.contourf(xLocs, yLocs, taper.reshape(numPointsX, numPointsY))
plt.imshow(taper.reshape(numPointsX, numPointsY), extent=[np.min(xLocs), np.max(xLocs), np.min(yLocs), np.max(yLocs)], 
           cmap=plt.cm.jet) #plt.cm.jet)
plt.colorbar()
plt.xlabel('x')
plt.ylabel('y')
plt.title('Taper Values')
plt.savefig('taper.png')
#plt.show()

# Create uv plot to compare with Peter
# We may have an angle issue - which angle is which...
#fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))
#fig, ax = plt.subplots() #subplot_kw=dict(projection='polar'))
#ax.contourf(np.cos(az), np.cos(el), np.log10(np.abs(hThetaF[:,0].reshape(az.shape))))
#
sys.exit(0)
fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))
ax.contourf(az, -(el-np.pi/2)*180./np.pi, np.log10(np.abs(hThetaF[:,0].reshape((az.shape)))))
#ax.contourf(np.cos(az), np.cos(el), np.log10(np.abs(hThetaF[:,0].reshape((az.shape)))))
#ax.contourf(np.log10(np.abs(hThetaF[:,0].reshape((az.shape[1], az.shape[0])))))
plt.show()

# Test one 
measTestOne = np.zeros((numMeas, 1), dtype=np.complex)
measTestOne[:,0] = 1.0*np.exp(-1j*2*np.pi*0.25)
hThetaF = steeringVectors(measPos, angles, freqs[0:1], measTestOne)

# Get the beamforming data

# Visualize for a particular frequency
#   Compare with Peter's plots - is this at a specific freq.?
