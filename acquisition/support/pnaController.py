# -*- coding: utf-8 -*-
"""
Created on Fri May 11 13:23:47 2018

@author: ajw5
"""

import pyvisa as visa
import numpy as np
import time

#chain for changing list of tuples into 1d list
from itertools import chain

#>>> import visa
#>>> rm = visa.ResourceManager()
#>>> rm.list_resources()
#('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
#>>> inst = rm.open_resource('GPIB0::12::INSTR')
#>>> print(inst.query("*IDN?"))

class pnaController():
    
    #default set to address when taking initial samurai measurements
    #def __init__(self,visa_address='USB0::0x0957::0x0118::SG49151009::0::INSTR'):
    def __init__(self,visa_address):#='TCPIP0::10.0.0.2::inst0::INSTR')
        #damirs vna is USB0::0x0957::0x0118::SG49151009::0::INSTR
        #dylans vna USB0::0x0957::0x0118::US49150144::INSTR
        self.visa_addr = visa_address
        
        #init our pna info 
        self.info        = -1
        self.ifbw        = -1.
        self.freq_start  = -1.
        self.freq_stop   = -1.
        self.freq_step   = -1.
        self.freq_span   = -1.
        self.freq_cent   = -1.
        self.num_pts     =  0 
        self.dwell_time  = -1.
        self.sdelay_time = -1.
        self.power       = -1e32
        self.sweep_type  = 'NO READ'
        self.sweep_time  = 0
        
        self.info = 'NO INFO'
        
        self.is_connected = False
        
        self.vrm = visa.ResourceManager()
        
        
        self.connect()
        
    def __del__(self):
        if(self.is_connected):
            self.disconnect()
        
    def connect(self):
        if(not self.is_connected):
            try:
                self.pna = self.vrm.open_resource(self.visa_addr)
                self.info = self.pna.query('*IDN?')
                self.pna.timeout = 60000; #timeout wasnt working at 3 or 10
            except:
                print("Unable to connect to PNA")
                return
            #if it worked were connected;
            self.is_connected = True
            
    def write(self,msg):
        
        #not my favorite way to do this but prevents timeouts when writing 100 values to segment table for source
        #i wish there was a :LIST command for segment source like there is for segment recievers
        #seems to work though regardless
        ready = False
        self.pna.write('*WAI')
       # while(not ready):
       #     try:
       #         self.pna.query('*OPC?');
       #         ready = True;
       #     except:
       #         ready = False;
            
       # try:
       #     self.pna.query('*OPC?');
       # except:
       #     print('Query Timed out when sending '+msg)
        #self.pna.write('*WAI')
        self.pna.write(msg)
        self.pna.query('*OPC?')        
        #time.sleep(0.10);
        
    def query(self,msg):
        #self.pna.write('*OPC?')
        return self.pna.query(msg)
    
    def disconnect(self):
        self.pna.close()
        self.is_connected = False
        
    def getParams(self):
        
        #connect to pna
        self.connect()
        
        #now get all of our values
        self.info        = self.pna.query('*IDN?')
        self.ifbw        = float(self.pna.query('SENS:BAND?'))
        self.freq_start  = float(self.pna.query('SENS:FREQ:STAR?'))
        self.freq_stop   = float(self.pna.query('SENS:FREQ:STOP?'))
        self.num_pts     = int  (self.pna.query('SENS:SWE:POIN?'))
        #gives timeout error self.freq_step   = float(pna.query('SENS:FREQ:CENT:STEP:SIZE?'));
        self.freq_span   = float(self.pna.query('SENS:FREQ:SPAN?'))
        self.freq_cent   = float(self.pna.query('SENS:FREQ:CENT?'))
        self.dwell_time  = float(self.pna.query('SENS:SWE:DWEL?'))
        self.sdelay_time = float(self.pna.query('SENS:SWE:DWEL:SDEL?'))
        self.power       = float(self.pna.query('SOUR:POW?'))
        self.sweep_type  = self.pna.query('SENS:SWE:TYPE?')
        self.sweep_time  = float(self.pna.query('SENS:SWE:TIME?'))
        
        #close our visa connection
        self.disconnect()
        
        #calculate values
        self.freq_step = self.freq_span/float(self.num_pts-1)
            
        #set our frequencies in hz
    def set_freq_sweep(self,start_freq,stop_freq,freq_step=-1,num_pts=-1,chan=1):
         
        if(freq_step==-1 & num_pts==-1):
            print("Please specify either frequency step or number of points")
            return
            
        if(freq_step!=-1): #calculate points from step
            num_pts = int((start_freq-stop_freq)/freq_step)+1
            
        #connect
        self.connect()
        
        #format strings
        start_str = "SENS%d:FREQ:STAR %e" % (chan,start_freq)
        stop_str  = "SENS%d:FREQ:STOP %e" % (chan,stop_freq)
        pts_str   = "SENS%d:SWE:POIN %d" % (chan,num_pts)
        type_str  = "SENS:FOM:RANG:SWE:TYPE LIN"
        
        #now write
        self.write(start_str)
        self.write(stop_str)
        self.write(pts_str)
        self.write(type_str)
        
        #close connection
        #self.disconnect();
        
        
    def set_start_freq(self,start_freq):
        self.connect()
        self.write()
        #self.disconnect();
        
    def get_start_freq(self):
        return float(self.pna.query('SENS:FREQ:STAR?'))
    
    
    def set_num_pts(self,num_pts):
        pts_str   = "SENS:SWE:POIN %d" % num_pts
        self.write(pts_str)
        
    def get_num_pts(self):
        self.connect()
        rv = int(self.pna.query('SENS:SWE:POIN?'))
        #self.disconnect();
        return rv
    
  #  def get_s_param_data():
  #      self.connect();
  #      self.write('FORM:DATA REAL,64'); #set the data format
  #      dat_str = self.query(')
    
    #give 'ON' or 'OFF' to on/off (or 1/0);
    def set_port_power_on_off(self,port_num,on_off_auto="AUTO"):
        
        possible_ports = [1,2,3,4]
        if port_num not in possible_ports:
            print("Port not in range")
            return -1
        
        pow_com = "SOUR:POW"+str(port_num)+":MODE "+str(on_off_auto).upper()
        self.write(pow_com)
        return
        
        
    #set source n on vna to cw with frequency freq
    def set_source_cw(self,src_num,freq):
        
        if(src_num!=1 and src_num!=2):
            print("Please select source 1 or 2")
            return -1
            
        #turn on frequency offset mode
        fom_on_com = "SENS:FOM ON"
        self.write(fom_on_com)
        
        #connect to the reader if not already done
        self.connect()
        
        #set our command for writing the source to CW
        #range2 = Source;
        #range4 = Source2;
        rng_val = src_num*2
        #uncouple, set to CW, set CW_Freq
        uncoup_str = "SENS:FOM:RANG%d:COUP OFF" % (rng_val)
        cw_freq_str = "SENS:FOM:RANG%d:FREQ:CW %e" % (rng_val,freq)
        type_cw_str = "SENS:FOM:RANG%d:SWE:TYPE CW" %(rng_val)
        
        self.write(uncoup_str)
        self.write(cw_freq_str)
        self.write(type_cw_str)
        
        return
        
    def set_source_coupling(self,src_num,on_off):
        
        src_nums = [1,2]
        if src_num not in src_nums:
            print("Please select source 1 or 2")
            return -1
        
        rng_num = src_num*2; #change to range number
        
        com = "SENS:FOM:RANG%d:COUP %s" % (rng_num,on_off.upper())
        self.write(com);  
        
    #freq ranges are going to be a list of tuples with [(on_off(1 or 0),num_pts,lo,hi,ifbw(optional)),...]
    #these values cannot overlap else the vna will not set them correctly
    def set_seg_list(self,seg_table,arb = True,couple = True):
        
        prev_form = self.query('FORM?')
        #change to 64 bit real
        #may not want to be used sometimes
        if(couple):
            #couple sources else pna gets mad
            self.set_source_coupling(1,'ON')
            self.set_source_coupling(2,'ON')
        
        #dat_str = [];
        
        #change to segmented sweep
        com = 'SENS:SWE:TYPE SEGM'
        self.write(com)
        
        #set arbitrary if we want
        if(arb):
            self.set_arb_seg('ON')
        
        #set the recievers here
        num_pts = len(seg_table)
        #for i in range(num_pts):
        #    dat_str.append(',%e,%e,%e,%e' % (tuple(np.round(seg_table[i]))))
        
        #data = ''.join(dat_str);
        com = 'SENS:SEGM:LIST SSTOP,'+str(num_pts)+','
        
        self.pna.write('FORM:BORD NORM')
        dat_out = list(chain(*seg_table)); #flatten list of tuples
        self.pna.write_binary_values(com,dat_out,datatype='d')
        #self.write(com);
        
        
        self.write('FORM %s' %(prev_form))

        
        
    #enable/disable arbitrary segmented sweep
    def set_arb_seg(self,on_off="ON"):
        com = 'SENS:SEGM:ARB %s' % (on_off)
        self.write(com)
        
    #set sources to segmented from
    #seg_table MUST BE THE SAME SIZE TABLE THAT THE RECIEVERS ARE SET TOO!!!
    #src num can be set to 0 to set both sources
    def set_seg_source_list(self,src_num,seg_table):
        #this new method will read the segment table, set to source table, uncouple, and set back to initial segment
        #get number of segments to start
        read_num_segs = int(self.query('SENS:SEGM:COUN?'))
        #then get the segments
        read_segs     = self.query('SENS:SEGM:LIST?')
        
        #error check
        if(read_num_segs!=len(seg_table)):
            print("ERROR: Segment tables must be the same length")
            return -1
        #now write our source segment list with no coupling
        self.set_seg_list(seg_table,couple=False)
        #now couple and uncouple the desired ports to copy the values
        if(src_num==0):
            self.set_source_coupling(1,'ON')
            self.set_source_coupling(2,'ON')
            self.set_source_coupling(1,'OFF')
            self.set_source_coupling(2,'OFF')
        else:
            self.set_source_coupling(src_num,'ON')
            self.set_source_coupling(src_num,'OFF')
            
        #now set back to our original values
        self.write('SENS:SEGM:LIST SSTOP,'+str(read_num_segs)+','+read_segs)
            
        
        
        
        
        
    def set_seg_source_list_iterating(self,src_num,seg_table):
        
        #check if were in segment mode
        #this is being dumb so its commented out
       # if(self.query('SENS:SWE:TYPE?').strip()!='SEGM'):
       #     print('ERROR: Please change sweep type to segmented');
       #     return -1;
        
        #turn on frequency offset mode
        fom_on_com = "SENS:FOM ON"
        self.write(fom_on_com)
        
        #check its a valid source
        src_nums = [1,2]
        if src_num not in src_nums:
            print("Please select source 1 or 2")
            return -1
        
        rng_num = src_num*2

        #couple then recouple to reset segment table
        self.set_source_coupling(src_num,'ON')
        self.set_source_coupling(src_num,'OFF')
        #set soruce to segment
        com = 'SENS:FOM:RANG%d:SWE:TYPE SEGM' % (rng_num)
        self.write(com)
        #print(com)
        
        #after uncouple/recouple segment table will be the same as measurement segment table
        #so just loop through this table and change the values
        #num_vals = int(mypnac.pna.query('SENS:FOM:RANG4:SEGM:COUN?'));
        num_vals = len(seg_table); #THIS MUST BE THE SAME SIZE TABLE THAT THE RECIEVERS ARE SET TOO!!! (and same numpts)
        #if seg_table is longer the end values will not be used. These values must be set carefully
        for i in range(num_vals):
            #ensure roundoff error of floats doesnt crush us
            cur_entry = tuple(np.round(seg_table[i]))
            sn = i+1 #seg number starts at 1 not 0
            #now set start,stop,points, and turn on
            on_off_com = 'SENS:FOM:RANG%d:SEGM%d %d' %(rng_num,sn,cur_entry[0])
            start_com  = 'SENS:FOM:RANG%d:SEGM%d:FREQ:STAR %e' %(rng_num,sn,cur_entry[2]) 
            stop_com   = 'SENS:FOM:RANG%d:SEGM%d:FREQ:STOP %e' %(rng_num,sn,cur_entry[3]) 
            #pts_com    = 'SENS:FOM:RANG%d:SEGM%d:SWE:POIN %e' %(rng_num,sn,cur_entry[1])
            #print(on_off_com);
            #print(start_com);
            #print(stop_com)
            #print(pts_com);
            
            self.pna.write(on_off_com)
            self.pna.write(start_com)
            self.pna.write(stop_com)
            #self.write(pts_com); #dont change points. this can cause further issues
            
    
#alias the class name to hold python standards (while also being backward compatable)
PnaController = pnaController    
        
        
        

        
            
            
            
            
        
            