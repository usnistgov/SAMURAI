# -*- coding: utf-8 -*-
"""
Created on Fri May 11 13:23:47 2018

@author: ajw5
"""

import pyvisa as visa
import numpy as np
import time
import re

#chain for changing list of tuples into 1d list
from itertools import chain
from collections import OrderedDict

from samurai.acquisition.support.InstrumentControl import SCPICommandDict

#>>> import visa
#>>> rm = visa.ResourceManager()
#>>> rm.list_resources()
#('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
#>>> inst = rm.open_resource('GPIB0::12::INSTR')
#>>> print(inst.query("*IDN?"))

import os
script_path = os.path.dirname(os.path.realpath(__file__))
command_set_path = os.path.join(script_path,'../hardware/command_sets/PNAX_communication_dictionary.json') 


class PnaController(OrderedDict):
    
    def __init__(self,visa_address):
        self.visa_addr = visa_address
        
        self.command_dict = SCPICommandDict(command_set_path)
        
        #init our pna info 
        self.setting_alias_dict = OrderedDict({
                'ifbw'       :'SENS:BAND',
                'freq_start' :'SENS:FREQ:STAR',
                'freq_stop'  :'SENS:FREQ:STOP',
                'freq_span'  :'SENS:FREQ:SPAN',
                'freq_cent'  :'SENS:FREQ:CENT',
                'num_pts'    :'SENS:SWE:POIN',
                'dwell_time' :'SENS:SWE:DWEL',
                'sdelay_time':'SENS:SWE:DWEL:SDEL',
                'power'      :'SOUR:POW',
                'sweep_type' :'SENS:SWE:TYPE',
                'sweep_time' :'SENS:SWE:TIME'
                })
        super().__init__()
        self.update({'info':'NO INFO READ'})
        
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
                self['info'] = self.pna.query('*IDN?')
                self.pna.timeout = 10000 #timeout wasnt working at 3 or 10
            except:
                raise IOError("Unable to connect to PNA")
            #if it worked were connected;
            self.is_connected = True
            
    def write(self,msg):
        '''
        @brief write a message to the PNA
        '''
        self.pna.write('*WAI')
        self.pna.write(msg)
        self.pna.query('*OPC?')        
        #time.sleep(0.10);
        
    def query(self,msg):
        #self.pna.write('*OPC?')
        print('QUERY: {}'.format(msg))
        return self.pna.query(msg)
    
    def disconnect(self):
        self.pna.close()
        self.is_connected = False
        
    def get_params(self):
        
        #connect to pna
        self.connect()
        print("Getting params")
        self['info'] = self.pna.query('*IDN?')
        #now get all of our values
        for k,v in self.setting_alias_dict.items():
            command = self.command_dict.get(v)('?')
            print(command)
            read_val = self.pna.query(command)
            #read_val = 'test'
            try: #try to convert to float
                read_val = float(read_val)
            except ValueError: #otherwise its fine as a string
                pass
            self[k] = read_val
        
        #close our visa connection
        self.disconnect()
        
        #calculate values
        self['freq_step'] = np.divide(self['freq_span'],float(self['num_pts']-1))
        
    def set(self,command,*args,**kwargs):
        '''
        @brief set a value from self.setting_alias_dict or try command_dict
        @param[in] command - can be an alias from setting_alias_dict, or command_dict
        @param[in] *args - arguments for the commands
        @param[in] **kwargs - keyword arguments for the command
        '''
        com = self.setting_alias_dict.get(command,None)
        if com is None: #was not in the setting alias dict
            com = self.command_dict.get(com) #assume its in the command_dict
        
            
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
        
    def setup_s_param_measurement(self,parameter_list):
        '''
        @brief setup n port s parameter measurement
        @param[in] parameter_list - which parameters to measure (e.g. [11,21,22,21])
        @note help from http://na.support.keysight.com/vna/help/latest/Programming/GPIB_Example_Programs/Create_a_measurement_using_GPIB.htm
        '''
        #first reset the vna
        #self.write(self.command_dict.get('SYST:FPR')())
        #now turn on window 1
        #self.write(self.command_dict.get('DISP:WIND')('ON'))
        #delete all other measurements
        self.write(self.command_dict.get('CALC:PAR:DEL:ALL')())
        #define our measurements
        meas_names = ["'S_{}'".format(int(pc)) for pc in parameter_list]
        meas_types = ["S{}".format(int(pc)) for pc in parameter_list]
        #and add the measurements
        for i,mn in enumerate(meas_names):
            self.write(self.command_dict.get('CALC:PAR:EXT')(mn,meas_types[i]))
        #and add them to the window
        for i,mn in enumerate(meas_names):
            self.write(self.command_dict.get('DISP:WIND:TRAC:FEED')(mn,tnum=i+1))
    
    def set_continuous_trigger(self,on_off):
        '''
        @brief set continuous trigger on or off
        '''
        self.write(self.command_dict.get('INIT:CONT')(on_off))
        
    def trigger(self):
        '''
        @brief trigger the vna when in manual mode. This will also wait for the sweep to complete
        '''
        self.write(self.command_dict('INIT:IMM')())
        
    
    def get_all_trace_data(self):
        '''
        @brief get data from all traces on a single channel
        @return [frequency_list, dict(trace_name:[values])]
        '''
        self.connect();
        #self.write('FORM:DATA REAL,64'); #set the data format
        freq_list = self.get_freq_list()
        trace_dict = self.get_traces()
        data_dict = {}
        for key in trace_dict.keys():
            self.write(self.command_dict.get('CALC:PAR:SEL')("'{}'".format(key))) #select the trace
            data_str = self.query(self.command_dict.get('CALC:DATA?')('sdata'))
            data = np.array(data_str.split(','),dtype='float64') #data as floating point
            data_cplx = data[::2]+data[1::2]*1j #change to complex
            data_dict[key] = data_cplx
        return freq_list,data_dict
        
    def get_freq_list(self):
        '''
        @brief get a list of the frequencies from the vna
        '''
        freq_str = self.query('SENS:X?') #newer CALC:X? command doesnt work on typical VNA
        freq_list = [float(val) for val in freq_str.strip().split(',')]
        return freq_list
        
    #give 'ON' or 'OFF' to on/off (or 1/0);
    def set_port_power_on_off(self,port_num,on_off_auto="AUTO"):
        
        possible_ports = [1,2,3,4]
        if port_num not in possible_ports:
            print("Port not in range")
            return -1
        
        pow_com = "SOUR:POW"+str(port_num)+":MODE "+str(on_off_auto).upper()
        self.write(pow_com)
        return
    
    def get_traces(self):
        '''
        @brief get trace name value pairs
        @return dictionary with <measurement name>/<paramter> pairs
        '''
        ret_str = self.query(self.command_dict.get('CALC:PAR:CAT:EXT?')())
        #remove quotes
        ret_str = re.sub('["\n ]+','',ret_str)
        name_val_pairs = re.findall('[^,]+,[^,]+',ret_str)
        #assume each pair is a list of 2 values with a comma in betewen
        ret_dict = {}
        for nvp in name_val_pairs:
            key,val = nvp.split(',')
            ret_dict[key] = val
        return ret_dict
        
        
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
        
        rng_num = src_num*2 #change to range number
        
        com = "SENS:FOM:RANG%d:COUP %s" % (rng_num,on_off.upper())
        self.write(com) 
        
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
        dat_out = list(chain(*seg_table)) #flatten list of tuples
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
        num_vals = len(seg_table) #THIS MUST BE THE SAME SIZE TABLE THAT THE RECIEVERS ARE SET TOO!!! (and same numpts)
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
pnaController = PnaController    

        
if __name__=='__main__':
    visa_address = 'TCPIP0::10.0.0.2::inst0::INSTR'
    mypna = PnaController(visa_address)
    #mypna.get_params()
    comd = mypna.command_dict
    mypna.connect()
    mypna.set_continuous_trigger('ON')
    mypna.set_freq_sweep(40e9,40e9,num_pts=1)
    ports = [1,3]
    param_list = [i*10+j for i in ports for j in ports]
    param_list = [11]
    #mypna.setup_s_param_measurement(param_list)
    dd = mypna.get_all_trace_data()
        

        
            
            
            
            
        
            