# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 11:53:42 2019

@author: bfj
"""
import numpy as np

speedOfLight = 299792458.0

def steeringVectors( coords, angles, freqsInHz, s21data, antenna=ant, newImp=False):
    
    
    #% coords assumed to have centroid 0
    numFreqs = len(freqsInHz)
    numPoints = coords.shape[0]
    numAngles = angles.shape[0]
    
    lambdaVec = speedOfLight / (freqsInHz)
    kVec = 2 * np.pi / lambdaVec
    
    dirs = np.zeros((numAngles,3))
    #dirs[:,0] = np.sin(angles[:,0])*np.sin(angles[:,1])
    #dirs[:,1] = np.sin(angles[:,0])*np.cos(angles[:,1])
    #dirs[:,2] = np.cos(angles[:,0])
    dirs[:,0] = np.sin(angles[:,1])
    dirs[:,1] = np.sin(angles[:,0])
    dirs[:,2] = np.sqrt(1.0 - dirs[:,0]**2 + dirs[:,1]**2)

    hThetaF = np.zeros((numFreqs, numAngles), dtype=np.complex128);

    if newImp:
        s21dataT = s21data.copy().transpose()

    ###########################################################################
    # Note the following only works for uniformly oriented arrays
    ###########################################################################
    
    #% Could be much faster...
    for iF in range(numFreqs):
        print(iF)
        kDir = kVec[iF]*dirs
        steeringVectorsData = np.exp(-1j * np.dot(kDir,coords.transpose()))
        
        ################################################################
        # Efficient implementation - needs to be verified
        ################################################################
        if newImp:
            #num = np.dot(steeringVectorsData, s21dataT[iF,:])
            ## Tensor notation - calculate the diagonal 
            #denom = np.einsum('ij,ji->i', steeringVectorsData, steeringVectorsData.transpose().conj())
            #denom = numPoints
            #hThetaF[iF, :] = num/np.sqrt(denom)
            hThetaF[iF, :] = np.dot(steeringVectorsData, s21dataT[iF,:])/np.sqrt(numPoints)
            
            ################################################################
            
        else:
            ################################################################
            
            ################################################################
            for iA in range(numAngles):
                #num = np.dot(np.reshape(s21data[:,iF], -1).transpose() ,np.reshape(steeringVectorsData[iA,:], -1))
                #denom = np.dot(np.conj(np.reshape(steeringVectorsData[iA,:], -1)).transpose(),np.reshape(steeringVectorsData[iA,:], -1))
                #print denom
                #hThetaF[iF, iA] = num/np.sqrt(denom)
                hThetaF[iF, iA] = np.dot(np.reshape(s21data[:,iF], -1).transpose() ,np.reshape(steeringVectorsData[iA,:], -1))/np.sqrt(numPoints)
    return hThetaF
    