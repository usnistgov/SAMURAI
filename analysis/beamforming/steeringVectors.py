# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 11:53:42 2019

@author: bfj
"""
import numpy as np

speedOfLight = 299792458.0

def steeringVectors( coords, angles, freqsInHz, s21data):
    #return hThetaF

    
    #% coords assumed to have centroid 0
    numFreqs = len(freqsInHz)
    numPoints = coords.shape[0]
    numAngles = angles.shape[0]
    
    
    lambdaVec = speedOfLight / (freqsInHz)
    kVec = 2 * np.pi / lambdaVec
    
    #%steeringVectors = zeros(numAngles, numPoints);
    
    dirs = np.zeros((numAngles,3))
    #dirs[:,0] = np.sin(angles[:,0])*np.sin(angles[:,1])
    #dirs[:,1] = np.sin(angles[:,0])*np.cos(angles[:,1])
    #dirs[:,2] = np.cos(angles[:,0])
    dirs[:,0] = np.sin(angles[:,1])
    dirs[:,1] = np.sin(angles[:,0])
    dirs[:,2] = np.sqrt(1.0 - dirs[:,0]**2 + dirs[:,1]**2)
    hThetaF = np.zeros((numAngles, numFreqs), dtype=np.complex128)
    
    #% Could be much faster...
    for iF in range(numFreqs):
        print(iF)
        kDir = kVec[iF]*dirs
        steeringVectorsData = np.exp(-1j * np.dot(kDir,coords.transpose()))
        
        ################################################################
        # Efficient implementation - needs to be verified
        ################################################################
        #num = np.dot(steeringVectorsData, s21data[:,iF])
        ## Tensor notation - calculate the diagonal 
        #denom = np.einsum('ij,ji->i', steeringVectorsData, steeringVectorsData.transpose().conj())
        #hThetaF[:, iF] = num/denom
        ################################################################
        
        ################################################################
        
        ################################################################
        for iA in range(numAngles):
            num = np.dot(np.reshape(s21data[:,iF], -1).transpose() ,np.reshape(steeringVectorsData[iA,:], -1))
            denom = np.dot(np.conj(np.reshape(steeringVectorsData[iA,:], -1)).transpose(),np.reshape(steeringVectorsData[iA,:], -1))
            hThetaF[iA, iF] = num/np.sqrt(denom)
        #end
        
        #% The next line works well...
        #%hThetaF(:,iF) = exp(1j*kVec(iF)*dirs*coords')*conj(s21data(:,iF)); %reshape(s21data(:,iF), [], 1)'*conj(reshape(steeringVectors(iA,:), [], 1));
        #%denom = sum(abs(steeringVectors).^2,2); %    sum(conj(reshape(steeringVectors(iA,:), [], 1)).*reshape(steeringVectors(iA,:), [], 1),1);
        #%hThetaF(:, iF) = num ; num./sqrt(denom);
    #end
    
    #%hThetaF = hThetaF/numPoints;
        
       
    return hThetaF
    