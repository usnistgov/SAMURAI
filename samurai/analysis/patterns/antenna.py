# -*- coding: utf-8 -*-
"""
Created on Thu Apr 04 16:02:49 2019

@author: bfj
"""

import numpy as np
import scipy.special
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

speedOfLight = 299792458.0 # m / s
#mu0 = 4.0*np.pi * 10**(-7)
#epsilon0 = 

class Antenna(object):
    def __init__(self):
        pass
    
    """
    @param translate 3d vector of traslation values [x,y,z]
    @param rotation 3d vector of orientations [azi, ele, rho]
           azimuthal rotation
           elevation rotation
           polarization rotation
    """
    def translateAndRotate(self, translation, rotation):
        pass
    
class RectangularHorn(Antenna):
    def __init__(self, hornDict):
        self.a = hornDict["a"]
        self.b = hornDict["b"]
        self.a1 = hornDict["a1"]
        self.b1 = hornDict["b1"]
        if "psie" in hornDict and "psih" in hornDict:
            self.psie = hornDict["psie"]
            self.psih = hornDict["psih"]
            self.rho1 = 0.5*self.b1/np.tan(np.pi/180*self.psie)
            self.rho2 = 0.5*self.a1/np.tan(np.pi/180*self.psih)
        else:
            self.rho1 = hornDict["rho1"]
            self.rho2 = hornDict["rho2"]
#        self.eta = 377.0
        
#        lamb = speedOfLight/(26.5*10**9)
#        self.a1 = 5.5*lamb
#        self.b1 = 2.75*lamb
#        #self.psie = hornDict["psie"]
#        #self.psih = hornDict["psih"]
#        self.rho1 = 6*lamb
#        self.rho2 = 6*lamb
#        self.eta = 377.0
    """
    @param azimuthVals azimuthal values
    @param eleVals 
    """
    def evalGain(self, theta, phi, freqs, r=1):
        """
        take an angle of arrival and return the complex gain
        This follow formulas in Balanis "Antenna Theory: ..."
        """
        theta = theta*np.pi/180.0
        phi = phi*np.pi/180.0
        
        freqs = freqs*10**9 # Convert to Hz
        kVals = 2.0*np.pi*freqs/speedOfLight
        kyVals = kVals*np.sin(theta)*np.sin(phi)
        kxpVals = kVals*np.sin(theta)*np.cos(phi) + np.pi/self.a1
        kxppVals = kVals*np.sin(theta)*np.cos(phi) - np.pi/self.a1
        
        t1Vals = np.sqrt(1.0/(np.pi*kVals*self.rho1))*(-kVals*self.b1/2.0 - kyVals*self.rho1)
        t2Vals = np.sqrt(1.0/(np.pi*kVals*self.rho1))*( kVals*self.b1/2.0 - kyVals*self.rho1)
        
        t1pVals = np.sqrt(1.0/(np.pi*kVals*self.rho2))*(-kVals*self.a1/2.0 - kxpVals*self.rho2)
        t2pVals = np.sqrt(1.0/(np.pi*kVals*self.rho2))*( kVals*self.a1/2.0 - kxpVals*self.rho2)
        
        t1ppVals = np.sqrt(1.0/(np.pi*kVals*self.rho2))*(-kVals*self.a1/2.0 - kxppVals*self.rho2)
        t2ppVals = np.sqrt(1.0/(np.pi*kVals*self.rho2))*( kVals*self.a1/2.0 - kxppVals*self.rho2)
        
        # Evaluate sine and cosine Fresnel integrals
        st1, ct1 = scipy.special.fresnel(t1Vals)
        st1p, ct1p = scipy.special.fresnel(t1pVals)
        st1pp, ct1pp = scipy.special.fresnel(t1ppVals)
        
        st2, ct2 = scipy.special.fresnel(t2Vals)
        st2p, ct2p = scipy.special.fresnel(t2pVals)
        st2pp, ct2pp = scipy.special.fresnel(t2ppVals)
        
        
        
        i1 = 0.5*np.sqrt(np.pi*self.rho2/kVals)*( np.exp(1j*(kxpVals**2*self.rho2/(2.0*kVals)))*((ct2p-ct1p) - 1j*(st2p - st1p)) \
                                                + np.exp(1j*(kxppVals**2*self.rho2/(2.0*kVals)))*((ct2pp-ct1pp) - 1j*(st2pp - st1pp)))
        
        i2 = np.sqrt((np.pi*self.rho1)/kVals)*np.exp(1j*(kyVals**2*self.rho1/(2.0*kVals)))*((ct2 - ct1) - 1j*(st2-st1))
        #print i1, i2
        #nTheta = -1.0/self.eta*np.cos(theta)*np.sin(phi)*i1*i2
        #nPhi = -1.0/self.eta*np.cos(phi)*i1*i2
        
        #lTheta = np.cos(theta)*np.cos(phi)*i1*i2
        #lPhi = np.sin(phi)*i1*i2
        
        eFieldTheta = -1j*kVals*np.exp(-1j*kVals*r)/(4.0*np.pi*r)*(np.sin(phi)*(1+np.cos(theta))*i1*i2)
        eFieldPhi = 1j*kVals*np.exp(-1j*kVals*r)/(4.0*np.pi*r)*(np.cos(phi)*(np.cos(theta)+1)*i1*i2)
        
        return eFieldTheta, eFieldPhi
        
def getXYZPolarizations(antResponse, tt, pp):
    antResponseXYZ = np.zeros((3,) + antResponse.shape[1:], dtype=np.complex128)
    for iF in range(antResponse.shape[1]):
        # Ex component
        antResponseXYZ[0,iF,:,:] = antResponse[0,iF,:,:]*np.cos(tt*np.pi/180.)*np.cos(pp*np.pi/180.) \
                                - antResponse[1,iF,:,:]*np.sin(pp*np.pi/180.)
        # Ey component
        antResponseXYZ[1,iF,:,:] = antResponse[0,iF,:,:]*np.cos(tt*np.pi/180.)*np.sin(pp*np.pi/180.) \
                                + antResponse[1,iF,:,:]*np.cos(pp*np.pi/180.)
        # Ez component
        antResponseXYZ[2,iF,:,:] = -antResponse[0,iF,:,:]*np.sin(tt*np.pi/180.)
                              
        #antResponseXY[0,iF,:,:] = np.cos(tt*np.pi/180.)*np.cos(pp*np.pi/180.) \
        #                        - np.sin(pp*np.pi/180.)
        #antResponseXY[1,iF,:,:] = np.cos(tt*np.pi/180.)*np.sin(pp*np.pi/180.) \
        #                        + np.cos(pp*np.pi/180.)
                
    ###########################################################################################################
    ## Ex component
    #antResponseXY[0,:,:,:] = np.multiply(antResponse[0,:,:,:], np.cos(tt*np.pi/180.)*np.cos(pp*np.pi/180.)) \
    #                   - np.multiply(antResponse[1,:,:,:], np.sin(pp*np.pi/180.))
    ## Ey component
    #antResponseXY[1,:,:,:] = np.multiply(antResponse[0,:,:,:], np.cos(tt*np.pi/180.)*np.sin(pp*np.pi/180.)) \
    #                   + np.multiply(antResponse[1,:,:,:], np.cos(pp*np.pi/180.))
    ###########################################################################################################
    return antResponseXYZ

if __name__=="__main__":    
    
    numFreqs = 1351
    numFreqs = 2
    freqStart = 26.5
    freqStop = 40
    freqs = np.linspace(freqStart, freqStop, numFreqs)
    
    # Lowest frequency for Balanis comparison
    lambda0 = speedOfLight/(freqs[0]*10**9)
    
    balanisPyramidal = {
        "a": .5*lambda0,
        "b": .25*lambda0,
        "a1": 5.5*lambda0, 
        "b1": 2.75*lambda0,
        "rho1": 6.0*lambda0,
        "rho2": 6.0*lambda0 
    }
            
        
    sage17 = {}
    # Convert to meters
    sage17["a"] =  7.112*10**(-3)
    sage17["b"] =  3.556*10**(-3)
    sage17["a1"] = 25.400*10**(-3)
    sage17["b1"] = 19.812*10**(-3)
    sage17["psie"] = 33.4
    sage17["psih"] = 37.3
    
    
    sage23 = {}
    # Convert to meters
    sage23["a"] =  7.112*10**(-3)
    sage23["b"] =  3.556*10**(-3)
    sage23["a1"] = 56.134*10**(-3)
    sage23["b1"] = 44.958*10**(-3)
    sage23["psie"] = 23.4
    sage23["psih"] = 27.6
    
    sageHorn17 = RectangularHorn(sage17)
    sageHorn23 = RectangularHorn(sage23)
    balanisHorn = RectangularHorn(balanisPyramidal)
    
    # Create angular grid:
    #   Theta is angle off of boresight of antenna
    # Phi is azimuthal
    deltaPhi = 1
    deltaTheta = 1
    phiVals = np.arange(0,360+deltaPhi,deltaPhi) 
    thetaVals = np.arange(0,180, deltaTheta) 
    
    #rPrimeVals = np.sin(thetaVals/2.0*np.pi/180.)
    R, P = np.meshgrid(thetaVals, phiVals)
    
    # Now determine the 
    
    numPhiVals = len(phiVals)
    numThetaVals = len(thetaVals)
    
    
    antResponse = np.zeros((2, numFreqs, numThetaVals, numPhiVals), dtype=np.complex128)
    for iPhi in range(numPhiVals):
        for iTheta in range(numThetaVals):
            antResponse[0, 0, iTheta, iPhi], antResponse[1, 0, iTheta, iPhi] = sageHorn23.evalGain(thetaVals[iTheta], phiVals[iPhi], freqs[0])
    
    
    antStr='sage23'
    X, Y = R*np.cos(P*np.pi/180.), R*np.sin(P*np.pi/180.)
    #X, Y = R, P
    tt, pp = np.meshgrid(thetaVals, phiVals)
    
    antResponseXYZ = getXYZPolarizations(antResponse, tt.transpose(), pp.transpose())
    
    gainPattern = np.sqrt(np.abs(antResponse[0,:,:,:])**2 + np.abs(antResponse[1,:,:,:])**2)
    gainPatternCart = np.sqrt(np.abs(antResponseXYZ[0,:,:,:])**2 + np.abs(antResponseXYZ[1,:,:,:])**2 + np.abs(antResponseXYZ[2,:,:,:]**2))
    
    xP = tt*np.cos(pp*np.pi/180.)
    yP = tt*np.sin(pp*np.pi/180.)
    
    myFigSize=(10,3)
    
    ###############################################################################
    # Gain comparison
    ###############################################################################
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    ax = axs[0]
    im = ax.contourf(X, Y, gainPattern[0,:,:].transpose(), color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    ax.set_title('Directivity Spherical')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    im = ax.contourf(X, Y, gainPatternCart[0,:,:].transpose(), color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    ax.set_title('Directivity Cartesian')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[2]
    im = ax.contourf(X, Y, (gainPattern[0,:,:] - gainPatternCart[0,:,:]).transpose(), color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title('Difference')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('cartVsSphereDirectivity_'+antStr+'.png')
    
    ###############################################################################
    # Spherical E fields - linear
    ###############################################################################
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    ax = axs[0]
    plotGain = gainPattern[0,:,:]/np.max(gainPattern[0,:,:])
    plotData = plotGain.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title('Gain Linear')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEx = np.abs(antResponse[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEx.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_\theta|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[2]
    plotEy = np.abs(antResponse[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_\phi|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('sphereELinear_'+antStr+'.png')
    
    ###############################################################################
    # Spherical E fields - dB
    ###############################################################################
    cutoff = -100 # dB
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    ax = axs[0]
    plotGain = gainPattern[0,:,:]/np.max(gainPattern[0,:,:])
    plotData = 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title('Gain dB')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEx = np.abs(antResponse[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = 20*np.log10(plotEx.transpose()) # 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_\theta|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[2]
    plotEy = np.abs(antResponseXYZ[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = 20*np.log10(plotEy.transpose()) # 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_\phi|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('sphereEdB_'+antStr+'.png')
    
    ###############################################################################
    # Cartesian E fields - linear
    ###############################################################################
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    
    ax = axs[0]
    plotEx = np.abs(antResponseXYZ[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEx.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_x|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEy = np.abs(antResponseXYZ[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_y|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    
    ax = axs[2]
    plotEy = np.abs(antResponseXYZ[2,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_z|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('cartELinear_'+antStr+'.png')
    
    ###############################################################################
    # Cartesian E fields - dB
    ###############################################################################
    cutoff = -100 # dB
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    
    ax = axs[0]
    plotEx = np.abs(antResponseXYZ[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = 20*np.log10(plotEx.transpose()) # 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_x|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEy = np.abs(antResponseXYZ[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = 20*np.log10(plotEy.transpose()) # 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_y|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    
    ax = axs[2]
    plotEy = np.abs(antResponseXYZ[2,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = 20*np.log10(plotEy.transpose()) # 20*np.log10(plotGain.transpose())
    mask = plotData < cutoff
    plotData[mask] = np.nan
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1, vmin=cutoff) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'$|E_z|$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('cartEdB_'+antStr+'.png')
    
    ###############################################################################
    # Spherical E fields - linear
    ###############################################################################
    myFigSize2 = (6.66,3)
    fig, axs = plt.subplots(1,2, figsize=myFigSize2)
    
    ax = axs[0]
    plotEx = 180./np.pi*np.angle(antResponse[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEx.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_\theta$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEy = 180./np.pi*np.angle(antResponse[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_\phi$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('sphereEPhase_'+antStr+'.png')
    
    ###############################################################################
    # Cartesian E fields - phase
    ###############################################################################
    fig, axs = plt.subplots(1,3, figsize=myFigSize)
    
    ax = axs[0]
    plotEx = 180./np.pi*np.angle(antResponseXYZ[0,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEx.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_x$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEy = 180./np.pi*np.angle(antResponseXYZ[1,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_y$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    
    ax = axs[2]
    plotEy = 180./np.pi*np.angle(antResponseXYZ[2,0,:,:]) #/np.max(np.abs(antResponseXYZ[1,0,:,:]))
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_z$')
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-180, -90, 0, 90, 180])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    plt.tight_layout()
    plt.savefig('cartEPhase_'+antStr+'.png')
    
    sys.exit(0)
    
    fig, axs = plt.subplots(1,3)
    ax = axs[0]
    plotGain = gainPattern[0,:,:]/np.max(gainPattern[0,:,:])
    plotData = plotGain.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title('Gain Linear')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[1]
    plotEx = np.angle(antResponseXYZ[0,0,:,:])
    plotData = plotEx.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase $E_x$')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    
    ax = axs[2]
    plotEy = np.angle(antResponseXYZ[1,0,:,:])
    plotData = plotEy.transpose() # 20*np.log10(plotGain.transpose())
    im = ax.contourf(X, Y, plotData) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_title(r'Phase of $E_y$')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    plt.show()
    
    sys.exit(0)
    
    
    
    
    fig, axs = plt.subplots(3,1)
    ax = fig.add_subplot(111, projection='3d')
    #Z = ((R**2 - 1)**2)
    axs[0].contourf(X, Y, np.transpose(np.abs(antResponse[0,0,:,:])))
    axs[1].contourf(X, Y, np.transpose(np.abs(antResponse[1,0,:,:])))
    axs[2].contourf(X, Y, np.transpose(np.abs(gainPattern[0,:,:])))
    #plt.contourf(X, Y, np.transpose(gainPattern[0,:,:]))
    #fig.colorbar()
    plt.show()
    
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    plotGain = gainPattern[0,:,:]/np.max(gainPattern[0,:,:])
    plotData = 20*np.log10(plotGain.transpose())
    maskVal = -40
    mask = plotData < maskVal
    plotData[mask] = maskVal
    surf = ax.plot_surface(X, Y, plotData, cmap=cm.coolwarm) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    # Customize the z axis.
    #ax.set_zlim(bottom=maskVal, top=-60)
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.title('Gain in dB')
    plt.show()
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    plotGain = gainPattern[0,:,:]/np.max(gainPattern[0,:,:])
    plotData = plotGain.transpose() # 20*np.log10(plotGain.transpose())
    #maskVal = -40
    #mask = plotData < maskVal
    #plotData[mask] = maskVal
    surf = ax.plot_surface(X, Y, plotData, color='white', shade=True, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    # Customize the z axis.
    #ax.set_zlim(bottom=maskVal, top=-60)
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    # Add a color bar which maps values to colors.
    #fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.title('Gain in linear')
    plt.show()
    
    # 
    fig = plt.figure()
    plt.contourf(X, Y, np.transpose(np.log10(gainPattern[0,:,:]))) #, levels=100)
    plt.show()
    
    ey = np.cos(pp*np.pi/180.)*np.transpose(antResponse[1,0,:,:]) - np.cos(tt*np.pi/180.)*np.sin(pp*np.pi/180.)*np.transpose(antResponse[0,0,:,:])
    plt.show()
    
    fig = plt.figure()
    plt.contourf(X, Y, 20*np.log10(np.abs(ey)), levels=range(-60,10,10), vmax=0.0, vmin=-60, extend='both')
    plt.colorbar()
    ax = plt.gca()
    #ax.zlim([-8, 0])
    plt.show()
    fig = plt.figure()
    plt.contourf(X, Y, np.angle(ey, deg=True)) #, vmax=0.0, vmin=-60)
    plt.colorbar()
    ax = plt.gca()
    #ax.zlim([-8, 0])
    plt.show()
    
    ###############################################################################
    # Balanis style plot
    ###############################################################################
    sys.exit(0)
    
    
    # Specify X and Y mesh
    numPoints = 301
    xVals = np.linspace(-180, 180, numPoints, endpoint=True)
    yVals = np.linspace(-180, 180, numPoints, endpoint=True)
    xx, yy = np.meshgrid(xVals, yVals)
    rVals = np.sqrt(xx**2 + yy**2)
    angVals = np.arctan2(yy*np.pi/180., xx*np.pi/180.)/np.pi*180.0
    
    mask = rVals > 180
    rVals[mask] = np.nan
    
    thetaVals = rVals
    phiVals = angVals
    # Now determine the 
    
    
    
    #numPhiVals = len(phiVals)
    #numThetaVals = len(thetaVals)
    
    # First index: E_theta, E_phi
    antResponse = np.zeros((2, numFreqs) + rVals.shape, dtype=np.complex128)
    for i1 in range(thetaVals.shape[0]):
        for i2 in range(thetaVals.shape[1]):
            if np.isnan(thetaVals[i1,i2]):
                antResponse[:,:, i1, i2] = np.nan
                continue
            antResponse[0, 0, i1, i2], antResponse[1, 0, i1, i2] = sageHorn17.evalGain(thetaVals[i1,i2], phiVals[i1,i2], freqs[0])
        
    gainPattern = np.sqrt(np.abs(antResponse[0,:,:,:])**2 + np.abs(antResponse[1,:,:,:])**2)
        
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    plotGain = gainPattern[0,:,:]/np.nanmax(gainPattern[0,:,:])
    plotData = plotGain.transpose() # 20*np.log10(plotGain.transpose())
    #plotData2 = np.where(thetaVals > 180, plotData, -1)
    #maskVal = -40
    #mask = plotData < maskVal
    #plotData[mask] = maskVal
    surf = ax.plot_surface(xx, yy, plotData, color='grey', shade=False, edgecolor='black', linewidths=0.1) #, vmin=-120, vmax=-60) #=False) #,                      cmap=cm.coolwarm, linewidth=0, antialiased=False)
    # Customize the z axis.
    plt.xticks([0]) # labels 
    plt.yticks([0])
    ax.xaxis.set_ticks_position('none') # tick markers
    ax.yaxis.set_ticks_position('none')
    ax.zaxis.set_ticks_position('none')
    #ax.zticks([])
    #ax.set_zlim(bottom=maskVal, top=-60)
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    plt.xlabel('x')
    plt.ylabel('y')
    # Add a color bar which maps values to colors.
    #fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.title('Gain in linear')
    plt.show()
    
    import scipy.io as sio
    sio.savemat('antPatternSage17.mat', {'xx': xx, 'yy': yy, 'plotData': plotData})