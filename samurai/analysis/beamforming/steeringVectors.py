# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 11:53:42 2019

@author: bfj
"""
import numpy as np

speedOfLight = 299792458.0

def steeringVectors( coords, angles, freqsInHz, s21data, newImp=False):
    
    
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

def steeringVectorsWithAntenna( coords, antPolarizations, freqsInHz, s21data, angles, gammaVals, antenna, musicEn, newImp=False):
    """
    @angles an array of angles to look in [iAng,0] is theta, [iAng,1] is phi
    @gammaVals values of polarization angle to searchv
    """
    
    #% coords assumed to have centroid 0
    numFreqs = len(freqsInHz)
    numPoints = coords.shape[0]
    numMeas = numPoints
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


    numGammaVals = gammaVals.shape[0]

    hThetaF = np.zeros((numFreqs, numAngles, numGammaVals), dtype=np.complex128);
    music = np.zeros((numFreqs, numAngles, numGammaVals), dtype=np.complex128);

    #if newImp:
    #    s21dataT = s21data.copy().transpose()
    
    # Frequency Domain Music
    #covMat = np.zeros((numMeas,numMeas,numFreqs))
    #for iF in range(numFreqs):
    #    covMat[:,:,iF] = np.dot(np.reshape(s21data[:,iF], (numMeas,1)), np.transpose(s21data[:,iF], (1, numMeas)))
    
    ###########################################################################
    # Note the following only works for uniformly oriented arrays
    ###########################################################################
    numAngles = angles.shape[0]
        
    antResponse = np.zeros((2, numFreqs, numAngles), dtype=np.complex128)
    for iAng in range(numAngles):
        # E_theta, E_phi
        antResponse[0, :, iAng], antResponse[1, :, iAng] = antenna.evalGain(angles[iAng,0], angles[iAng,1], freqsInHz)
        
    antResponseMult = np.zeros((2, numFreqs, numAngles, numMeas), dtype=np.complex128)        
    for iM in range(numMeas):
        antResponseMult[0,:,:,iM] = np.cos(antPolarizations[iM])*antResponse[0,:,:] - np.sin(antPolarizations[iM])*antResponse[1,:,:]
        antResponseMult[1,:,:,iM] = np.sin(antPolarizations[iM])*antResponse[0,:,:] + np.cos(antPolarizations[iM])*antResponse[1,:,:]
        
    for iF in range(numFreqs):
        kDir = kVec[iF]*dirs
        steeringVectorsData = np.exp(1j * np.dot(kDir,coords.transpose())) # size (numAngles,numMeas)
        
        ################################################################
        # Efficient implementation - needs to be verified
        ################################################################
        #if newImp:
        #    #num = np.dot(steeringVectorsData, s21dataT[iF,:])
        #    ## Tensor notation - calculate the diagonal 
        #    #denom = np.einsum('ij,ji->i', steeringVectorsData, steeringVectorsData.transpose().conj())
        #    #denom = numPoints
        #    #hThetaF[iF, :] = num/np.sqrt(denom)
        #    hThetaF[iF, :] = np.dot(steeringVectorsData, s21dataT[iF,:])/np.sqrt(numPoints)
        #    
        #    ################################################################
        #    
        #else:
        if 1 == 1: # to preserve indent
            ################################################################
            
            ################################################################
            for iA in range(numAngles):
                for iG in range(numGammaVals):
                    # For a uniformly facing array, the specified antenna response is the realized antenna response
                    # For arrays where the antennae have different orientations then we must 
                    #   first rotate the antenna pattern 
                    #   then apply the polarization angle
                    
                    # Get the angle...
                    polarAntResponse = np.cos(gammaVals[iG])*antResponseMult[0,iF,iA,:] + np.sin(gammaVals[iG])*antResponseMult[1,iF,iA,:]
                    svData = steeringVectorsData[iA, :]*polarAntResponse
                    #num = np.dot(np.reshape(s21data[:,iF], -1).transpose() ,np.reshape(steeringVectorsData[iA,:], -1))
                    #denom = np.dot(np.conj(np.reshape(steeringVectorsData[iA,:], -1)).transpose(),np.reshape(steeringVectorsData[iA,:], -1))
                    #print denom
                    #hThetaF[iF, iA] = num/np.sqrt(denom)
                    hThetaF[iF, iA, iG] = np.dot(np.transpose(svData).conj(), np.reshape(s21data[:,iF], numMeas ,1))/np.sqrt(np.linalg.norm(svData))
                    music[iF, iA, iG] = np.linalg.norm(svData)/np.dot(np.transpose(svData).conj(), np.dot(musicEn[iF], svData))
    return hThetaF, music
        