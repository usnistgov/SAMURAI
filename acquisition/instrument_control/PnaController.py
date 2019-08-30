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

from samurai.acquisition.instrument_control.InstrumentControl import SCPICommandDict, SCPIInstrument

#>>> import visa
#>>> rm = visa.ResourceManager()
#>>> rm.list_resources()
#('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
#>>> inst = rm.open_resource('GPIB0::12::INSTR')
#>>> print(inst.query("*IDN?"))

import os
script_path = os.path.dirname(os.path.realpath(__file__))
command_set_path = os.path.join(script_path,'../hardware/command_sets/PNAX_communication_dictionary.json') 


class PnaController(SCPIInstrument):
    
    def __init__(self,visa_address=None,command_dict_path=command_set_path,**other_info):
        '''
		@brief constructor for our class 
		@param[in/OPT] visa_address - pna visa address to connect to. If not provided do not connect
		'''
        super().__init__(command_dict_path)
        
        self.update({'info':'NO INFO READ'})
        
        self.setting_params = ['info','if_bandwidth','freq_start','freq_stop',
                               'freq_span','freq_cent','num_pts','dwell_time',
                               'sweep_delay_time','power','sweep_type','sweep_time'] #these values will be read when self.get_settings is read
        
        self.is_connected = False
        
        self.vrm = visa.ResourceManager()
        
        if visa_address is not None:
            self.connect(visa_address)
     
    #overrides superclass
    def _connect(self,address):
        '''
        @brief this is the disconnect that is used in self.connect() defined in superclass
        '''
        if(not self.is_connected):
            try:
                self.connection = self.vrm.open_resource(address)
                self.connection.timeout = 10000 #timeout wasnt working at 3 or 10
            except:
                raise IOError("Unable to connect to PNA")
            #if it worked were connected;
            self.is_connected = True
            
    def write(self,msg,*args,**kwargs):
        '''
        @brief write a message to the PNA
        @param[in/OPT] *args,**kwargs - args for when commands from command_dict are used
        '''
        super().write('*WAI')
        super().write(msg,*args,**kwargs)
        self.query('*OPC?',False)        
        #time.sleep(0.10);
    
    def _disconnect(self):
        '''
        @brief this is the disconnect that is used in self.disconnect() defined in superclass
        '''
        self.connection.close()
        self.is_connected = False
        
    def get_params(self):
        
        self.get_settings()
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
    def set_freq_sweep(self,start_freq,stop_freq,freq_step=-1,num_pts=-1):
         
        if(freq_step==-1 & num_pts==-1):
            print("Please specify either frequency step or number of points")
            return
            
        if(freq_step!=-1): #calculate points from step
            num_pts = int((stop_freq-start_freq)/freq_step)+1
            freq_start = num_pts*freq_step+start_freq #use correct start but adjusted stop frequency
            
        #now write
        self.write('freq_start',start_freq)
        self.write('freq_stop',stop_freq)
        self.write('num_pts',num_pts)
        self.write('sweep_type','LIN')
        
    def setup_s_param_measurement(self,parameter_list):
        '''
        @brief setup n port s parameter measurement
        @param[in] parameter_list - which parameters to measure (e.g. [11,21,22,21])
        @note help from http://na.support.keysight.com/vna/help/latest/Programming/GPIB_Example_Programs/Create_a_measurement_using_GPIB.htm
        '''
        #first reset the vna
        self.write('SYST:FPR')
        #now turn on window 1
        self.write('DISP:WIND','ON')
        #delete all other measurements
        #self.write(self.command_dict.get('CALC:PAR:DEL:ALL')())
        #define our measurements
        meas_names = ["'S_{}'".format(int(pc)) for pc in parameter_list]
        meas_types = ["S{}".format(int(pc)) for pc in parameter_list]
        #and add the measurements
        for i,mn in enumerate(meas_names):
            self.write('CALC:PAR:EXT',mn,meas_types[i])
        #and add them to the window
        for i,mn in enumerate(meas_names):
            self.write('DISP:WIND:TRAC:FEED',mn,tnum=i+1)
    
    def set_continuous_trigger(self,on_off):
        '''
        @brief set continuous trigger on or off
        '''
        self.write('INIT:CONT',on_off)
        if on_off.upper() is 'OFF':
            mode = 'SING'
        else:
            mode = 'CONT'
        self.write('SENS:SWE:MODE',mode)
        
    def trigger(self,timeout=300000):
        '''
        @brief trigger the vna when in manual mode. This will also wait for the sweep to complete
        @param[in] timeout - timeout of visa. The OPC? command hangs until the sweep is finished in single mode
            This default to 5 minutes. reset the timeout when were done
        '''
        timeout_temp = self.connection.timeout
        self.connection.timeout = timeout
        self.write('INIT:IMM')
        self.connection.timeout = timeout_temp
        
    
    def get_all_trace_data(self):
        '''
        @brief get data from all traces on a single channel
        @return [frequency_list, {trace_name:{'parameter':param,'data':[values]}]
        '''
        #self.write('FORM:DATA REAL,64'); #set the data format
        freq_list = self.get_freq_list()
        trace_dict = self.get_traces()
        data_dict = {}
        for key,val in trace_dict.items():
            self.write('CALC:PAR:SEL',"'{}'".format(key)) #select the trace
            data_str = self.query('CALC:DATA?','sdata')
            data = np.array(data_str.split(','),dtype='float64') #data as floating point
            data_cplx = data[::2]+data[1::2]*1j #change to complex
            data_dict[key] = {'parameter':val,'data':data_cplx}
        return freq_list,data_dict
    
    def measure_s_params(self,out_path,port_mapping=None):
        '''
        @brief measure s parameters of current traces and write out to out_path
        @param[in] out_path - path to write out data to 
        @param[in/OPT] port_mapping - optional dictionary of port mappings (e.g {3:2})
        '''
        #trigger the vna assume continuous trigger is off (self.set_continuous_trigger('off'))
        self.set_continuous_trigger('OFF')
        self.trigger()
        #first lets get the data of the current traces
        freqs,data_dict = self.get_all_trace_data()
        #import snp editor
        from samurai.analysis.support.snpEditor import SnpEditor,map_keys
        #now lets get the number of ports from the out_path
        num_ports = int(re.findall('(?<=s)\d+(?=p)',out_path)[0])
        #now lets create our Snp Object
        freqs = freqs/1e9 #change to GHz
        snp = SnpEditor([num_ports,freqs],header='GHz S RI 50')
        for dd in data_dict.values():
            if dd['parameter'][0].upper()=='S': #then its an s param measurement
                s_key = int(dd['parameter'][1:])
                #map ports if specified
                s_key = map_keys([s_key],port_mapping)[0]
                snp.S[s_key].raw = dd['data']
        snp.write(out_path)
        return snp
    
    def measure(self,out_path,port_mapping=None):
        '''
        @brief alias used to fit into SAMURAI_System with PNAGrabber code
        '''
        out_path = clean_file_name(out_path)
        self.measure_s_params(out_path,port_mapping)
        return 0,out_path #args match pnagrabber return
        
    def get_freq_list(self):
        '''
        @brief get a list of the frequencies from the vna
        '''
        freq_str = self.query('SENS:X?') #newer CALC:X? command doesnt work on typical VNA
        if type(freq_str) is str: #ensure we didnt already convert (single frequency)
            freq_list = [float(val) for val in freq_str.strip().split(',')]
        elif type(freq_str) is float:
            freq_list = [freq_str]
        return np.array(freq_list)
        
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
        ret_str = self.query('CALC:PAR:CAT:EXT?')
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
        
    def set_segment_sweep(self,seg_table,arb = True,couple = True):
        '''
        @brief setup a segment sweep on the vna bysetting the segment list
        @param[in] seg_table - segment table values list of tuples with [(on_off(1 or 0),num_pts,lo,hi,ifbw(optional)),...]
        @param[in/OPT] arb - arbitrary segment sweep allowed (default True)
        @param[in/OPT] couple - whether or not to couple the sources (default True)
        '''
        
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
        
        self.connection.write('FORM:BORD NORM')
        dat_out = list(chain(*seg_table)) #flatten list of tuples
        self.connection.write_binary_values(com,dat_out,datatype='d')
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
            
            self.connection.write(on_off_com)
            self.connection.write(start_com)
            self.connection.write(stop_com)
            #self.write(pts_com); #dont change points. this can cause further issues
         

#alias the class name to hold python standards (while also being backward compatable)
pnaController = PnaController    

def clean_file_name(fname):
    '''
    @brief make sure the file name doesnt exist. If it does add an ending so it doesnt overwrite
    '''
    fname_orig = fname
    i=1
    while os.path.exists(fname):
        fname = '_{}'.format(i).join(os.path.splitext(fname_orig))
        i+=1
    return fname
        
if __name__=='__main__':
    
    visa_address = 'TCPIP0::10.0.0.2::inst0::INSTR'
    mypna = PnaController(visa_address)
    #mypna.get_params()
    comd = mypna.command_dict
    mypna.query('info')
    
    mypna.get_params()
    #mypna.set_freq_sweep(40e9,40e9,num_pts=1)

    #mypna.set_settings()
    
    #mypna.set_continuous_trigger('ON')
    #ports = [1,3]
    #param_list = [i*10+j for i in ports for j in ports]
    param_list = [11,31,13,33]
    mypna.setup_s_param_measurement(param_list)
    #mypna.set_freq_sweep(26.5e9,40e9,num_pts=1351)
    mypna.write('if_bandwidth',100)
    #mypna.set_continuous_trigger('off')
    seg_list = [(1,501,27e9,28e9,1000),(1,501,30e9,31e9,1000)]
    mypna.set_segment_sweep(seg_list)
    mypna.get_params()
    print(mypna)
    #mys = mypna.measure_s_params('./test/testing.s2p',port_mapping={3:2})
    #dd = mypna.get_all_trace_data()
     

        
            
            
            
            
        
            