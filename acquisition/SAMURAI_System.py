# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 13:47:17 2018
Full High level system controls for samurai
@author: ajw5
"""
import sys
#include our support libs
#samurai_support_libs_dir = './support'
#sys.path.append(samurai_support_libs_dir)
import support.autoPNAGrabber   as pnag    #for running pnagrabber
import support.pnaController    as pnac    #for getting and setting settings on pna
import support.samurai_metaFile as smf     #for keeping track of data
from support.Meca500  import Meca500       #our posisioner
import support.samurai_support  as ss      #some other functions

import six

import numpy as np

import time
import os

#default values
#pnagrabber_template_path = r'U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\support\template.pnagrabber'
pnagrabber_template_path = './template.pnagrabber'
vna_visa_addr = 'TCPIP0::10.0.0.2::inst0::INSTR'
rx_positioner_address = '10.0.0.5'

class SAMURAI_System():
    """
    @brief - Class to control the entire SAMURAI system
    """
    
    #to run as simulation simply pass is_simualtion=true
    def __init__(self,is_simulation=False,**arg_options):
        defaults = {'template_path':pnagrabber_template_path,'vna_visa_address':vna_visa_addr,'rx_positioner_address':rx_positioner_address}
        tool_length = 131 #length of tool off face in mm. Change for weird tools
        defaults['trf_pos'] = [0,0,tool_length,0,-90,0] #tool reference frame (-90 to align axes with wrf). THE frame here is different and seems to be in ([z,y,z,gamma,beta,alpha]) compared to world frame
        defaults['wrf_pos'] = [tool_length+190,0,0,0,0,0] #world reference frame at robot base z but x of tool (+190 for base to tip at zeroed postiion)
        self.options = {}
        for key, value in six.iteritems(defaults):
            self.options[key] = value
        for key, value in six.iteritems(arg_options):
            self.options[key] = value
        self.pnagrabber_template_path = self.options['template_path']
        self.vna_visa_addr = self.options['vna_visa_address']
        self.is_connected = False
        self.set_simulation_mode(is_simulation)
        #self.connect_rx_positioner();
        self.rx_positioner = Meca500() #meca500 positioner

        
    def connect_rx_positioner(self,run_simulation=None):
        if not run_simulation:
            run_simulation = self.is_simulation #set to default unless overwritten
            rv1=self.rx_positioner.set_simulation_mode=False
        else:
            print("Running in Simulation Mode")
            rv1=self.rx_positioner.set_simulation_mode=True
        self.is_connected = True
        rv2=self.rx_positioner.initialize(ip_addr=self.options['rx_positioner_address']) #start up the meca
        #SETTING REFERENCE PLANES IS A MUST!!! DO NOT SKIP THIS STEP
        rv3=self.rx_positioner.set_wrf(self.options['wrf_pos']) #set reference frames (VERY IMPORTANT)
        rv4=self.rx_positioner.set_trf(self.options['trf_pos'])
        rv5=self.rx_positioner.set_velocity(10)
        self.is_connected = True
        return [rv1,rv2,rv3,rv4,rv5]
        
    def get_rx_positioner_status(self):
        #self.meca_status.update
        return self.rx_positioner.get_status() #get the status list
    
    def disconnect_rx_positioner(self,zero_flg=True):
        self.rx_positioner.close(zero_flg)
        self.is_connected = False
        
    def set_simulation_mode(self,on_off):
        """
        @brief - set whether the robot operations in simulation mode.
            This can only be done when disconnected, so we will check that
        @param[in] - on_off - True to turn on Simulation, False to turn off Simulation
        @return - 0 for success, -1 if value cannot be set (because we are connected currently)
        """
        if(self.is_connected):
            return -1 #we can only change the flag while disconnected
        #else we return success after setting simulation
        self.is_simulation = on_off
        return 0 #success
    
    def set_options(self,**arg_options):
        '''
        @brief easy way to set options
        '''
        for key, value in six.iteritems(arg_options):
            self.options[key] = value
        
   # def __del__(self):
   #    self.disconnect_rx_positioner(False);
    
    #Here we will have various setup and run options we encounter
    #generic sweep from csv file and measure with pnagrabber 
    #need to pass arg_options as unpacked dict or named args
    def csv_sweep(self,data_out_dir,csv_path,run_vna=True,**arg_options):
        #check if connected
        if not self.is_connected:
            print("Positioner Not Connected")
            return
        
        #output_file_type should match that of pnagrabber
        defaults = {'note':'none','output_directory':'./','output_name':'meas','output_file_type':'s2p','template_path':'./template.pnagrabber'}
        defaults['settling_time'] = .1 #settling time in seconds
        defaults['info_string_var'] = None #be able to set outside stringvar for update info
        defaults['metafile_header_values'] = {}
        options = {}
        for key, value in six.iteritems(defaults):
            options[key] = value
        for key, value in six.iteritems(arg_options):
            options[key] = value
         
        if run_vna:
        #open PNAGrabber instance
            pnag_out_path = os.path.join(os.path.split(options['output_directory'])[0],'unnamed.'+options['output_file_type'])
            pnagrab = pnag.pnaGrabber(pnagrabber_template_path=options['template_path'],pnagrabber_output_path=pnag_out_path)
        mf = smf.metaFile(csv_path,self.options['vna_visa_address'],wdir=data_out_dir)
        mf.init(**options['metafile_header_values'])
        
        if(defaults['info_string_var']):
            defaults['info_string_var'].set('Metafile Initilialized')
        
        #zero positioner (always start from zero positoin to ensure everything is safe)
        self.rx_positioner.zero()
    
        #now start running positioner    
        csvfp = open(csv_path)
        numLines = ss.countLinesInFile(csvfp)
        ltr = pnag.LoopTimeReport(numLines)
        if not run_vna:
            print("Running without VNA Measurements")
        n=0
        run_time_start = time.time()
        for line in csvfp: #read each line
            if(line.split()):
                strVals = line.split(',') #separate by csv
                fvals = [float(i) for i in strVals]
                #print("Moving Device to "+str(fvals))
                ltr.start_point()
                self.set_position(fvals)
                newPath = os.path.join(options['output_directory'],options['output_name']+'.'+options['output_file_type'].strip('.'))
                #let positioner settle
                time.sleep(options['settling_time'])
                posn_vals = self.rx_positioner.get_position()
                if(run_vna):
                    [pnaTime,newPath] = pnagrab.run(newPath)
                else:
                    pnaTime = -3.14159
                    newPath = 'VNA NOT USED'
                mf.update(newPath,posn_vals,note='PNA Time : '+str(pnaTime))
                ltr.end_point(pnaTime)
                n+=1
            
        print("All positions in CSV file completed")
        mf.finalize()
        return time.time()-run_time_start
    
    #move robot to side of table for easy mounting
    #looking from the back we have left and right
    #left is close to vna
    #right is close to sink (BE CAREFUL NOT TO PULL CABLE ON RIGHT)
    def move_to_mounting_position(self,side='left',rotation=-120):
        #check if connected
        if not self.is_connected:
            print("Positioner Not Connected")
            return
        #mounting position in [x,y,z,alpha,beta,gamma]
        #this is all done with respect to the SAMURAI reference frames (trf rotated to match wrf and wrf at base directly below trf when zerod)
        if(side.lower()=='left'):
            mounting_position = [-250,445,140,0,rotation,90]
        if(side.lower()=='right'):
            mounting_position = [-250,-445,140,0,rotation,-90]
            
        return self.set_position(mounting_position)
        
    #wrapper of rx_positioner set_position to check for bounds
    def set_position(self,pos_vals,software_limits=True):
        if(software_limits):
            np_pos_vals = np.array(pos_vals)
            np_lower_bound = np.array([-1e3,-1e3,50,-360,-360,-360]) #just limit z axis
            np_upper_bound = np.array([1e3,1e3,1e3,360,360,360]) #no upper bound
            if(any(np_pos_vals<np_lower_bound)):
                print("ERROR: Position below lower bound")
                return
            if(any(np_pos_vals>np_upper_bound)):
                print("ERROR: Position above upper bound")
                return
        #finally now set the position
        self.rx_positioner.set_position(pos_vals)
        return
        
    def zero(self):
        self.rx_positioner.zero()
        
    
        
    
    
      
      #samsys = SAMURAI_System();
      #samsys.connect_rx_positioner();
      
        