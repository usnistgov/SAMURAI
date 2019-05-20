# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 13:24:04 2018
This is where all of the other SAMURAI functionality is going that doesn't nicely 
fit somewhere else
@author: ajw5
"""
import time
import sys
#include our support libs
samurai_support_libs_dir = "./"
sys.path.append(samurai_support_libs_dir)
import samurai.acquisition.support.pnaController    as pnaCont    #for getting and setting settings on pna
import numpy as np

vna_visa_address = 'TCPIP0::10.0.0.2::inst0::INSTR'

def countLinesInFile(filePointer,comments='#'):
    cnt = 0
    for line in filePointer:
        if(line.strip()):
            if(any(line.strip()[0]==np.array([comments]))):
                continue #then pass the line (dont count it)
            cnt=cnt+1
    filePointer.seek(0)
    return cnt

def init_vna_usc(self,if_start=1.65e9,if_stop=2.05e9,rf_start=27.65e9,rf_stop=28.05e9,num_pts=41,source="RF"):
    
    ts = time.time()
    
    pnac = pnaCont.pnaController(vna_visa_address)
    
    if_freqs = np.linspace(if_start,if_stop,num_pts)
    rf_freqs = np.linspace(rf_start,rf_stop,num_pts)
    
    if(round(if_stop-if_start)!=round(rf_stop-rf_start)):
        print("Frequency Ranges Don't Match! ABORTING")
        print("RF_range = "+str(rf_stop-rf_start)+"    IF_range = "+str(if_stop-if_start))
        return -1
    
    #turn off port 3 power
    pnac.set_port_power_on_off(3,'OFF')
    
    seg_list = []
    seg_source_list_p1 = []
    seg_source_list_p2 = []

    #now build our list of tuples
    for i in range(len(if_freqs)):
        
        iff = if_freqs[i]; rff = rf_freqs[i]
        #first set our sources to the correct frequency
        if(source.strip().upper()=="IF"):
            sffp1 = iff
            sffp2 = rff
        elif(source.strip().upper()=="RF"):
            sffp1 = rff
            sffp2 = iff
        
        #RF must come first so PNAGrabber normalizes to measured RF value
        seg_list.append((1,2,rff,iff))
        seg_source_list_p1.append((1,2,sffp1,sffp1))
        seg_source_list_p2.append((1,2,sffp2,sffp2))
        
    #now write all of the values to the pnax
    pnac.set_seg_list(seg_list)
    pnac.set_seg_source_list(1,seg_source_list_p1)
    pnac.set_seg_source_list(2,seg_source_list_p2)
    
 
    te = time.time()
    return te-ts

  
import datetime


