# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 13:47:17 2018
Full High level system controls for samurai
@author: ajw5
"""

from samurai.acquisition.support import autoPNAGrabber as pnag    #for running pnagrabber
from samurai.acquisition.support import samurai_metaFile as smf     #for keeping track of data
from samurai.acquisition.support.Meca500  import Meca500       #our posisioner
import samurai.acquisition.support.samurai_support  as ss      #some other functions
import samurai.acquisition.support.samurai_optitrack as samurai_optitrack  #import optitrack tracking

import six
import json

import numpy as np

import time
import os

#these are default values. These seem to change with the system realatively often so they are placed here at the top
pnagrabber_template_path = './template.pnagrabber'
vna_visa_addr = 'TCPIP0::10.0.0.2::inst0::INSTR'
rx_positioner_address = '10.0.0.5'

class SAMURAI_System():
    """
    @brief - Class to control the entire SAMURAI system
    """
    
    #to run as simulation simply pass is_simualtion=true
    def __init__(self,is_simulation=False,**arg_options):
        '''
        @brief initialize class to control SAMURAI measurement system
        @param[in/OPT] is_simulation - whether or not to run the Meca500 in simultion mode (defaults to NO simulation)
        @param[in/OPT] arg_options - optional keyword arguments as follows:
            template_path - where the pnagrabber template is located
            vna_visa_address - visa address of the VNA
            rx_positioner_address - address of the rx positioner. for Meca500 this is a IP address
        '''
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
        '''
        @brief connect and ready our rx positioner (Meca500) for movement
        @param[in/OPT] run_simulation - whther to run in sim mode (defaults to NO)
        @return list of Meca return values as follows
            [set_sim_mode_rv,init_rx_pos_rv,set_wrf_rv,set_trf_rv,set_velocity_rv]
        '''
        if not run_simulation:
            run_simulation = self.is_simulation #set to default unless overwritten
            rv1=self.rx_positioner.set_simulation_mode=False
        else:
            print("Running in Simulation Mode")
            rv1=self.rx_positioner.set_simulation_mode=run_simulation
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
        '''
        @brief measure a synthetic aperture with the SAMURAI system using positions from a CSV (comma separated value) file
        @param[in] data_out_dir - where the data will be output 
        @param[in] csv_path - path to the comma separated value (CSV) file
        @param[in/OPT] run_vna - whether or not to run the VNA when sweeping (default to true=run the vna)
        @param[in/OPT] arg_options - keyword arguments as follows:
            note - note to put in the metafile  (defaults to '')
            output_name - name of the output files (defaults to 'meas')
            template_path - location of pnagrabber template to run from (default './template.pnagrabber')
            settling time - time in seconds to let robot settle (default 0.1s)
            metafile_header_values - dictionary of values to overwrite or append to in metafile header (defaults to nothing)
            external_position_measurements - configuration of external measurement device (e.g. optitrack)
                OPTITRACK - provide {name:id} pairs for markers xyz components or {name:None} for rigid bodies x,y,z,alpha,beta,gamma
                    A set of measurements will be provided for each of these (e.g [{'tx_antenna':50336},{'meca_head':None},{'origin':None},{'cyl_1':50123}]).
                    For each of these points, n=num_samples (default=10) measurements are taken and the stdev, covariance matrix, and mean values are provided
        @return sweep time
        '''
        if not self.is_connected:
            print("Positioner Not Connected")
            return
        
        #output_file_type should match that of pnagrabber
        defaults = {'note':'none','output_directory':'./','output_name':'meas','output_file_type':'s2p','template_path':'./template.pnagrabber'}
        defaults['settling_time'] = .1 #settling time in seconds
        defaults['info_string_var'] = None #be able to set outside stringvar for update info
        defaults['metafile_header_values'] = {}
        defaults['external_position_measurements'] = None
        options = {}
        for key, value in six.iteritems(defaults):
            options[key] = value
        for key, value in six.iteritems(arg_options):
            options[key] = value
         
        if run_vna:
        #open PNAGrabber instance
            #pnag_out_path = os.path.join(os.path.split(options['output_directory'])[0],'unnamed.'+options['output_file_type'])
            pnagrab = pnag.pnaGrabber(pnagrabber_template_path=options['template_path'])
        mf = smf.metaFile(csv_path,self.options['vna_visa_address'],wdir=data_out_dir)
        mf.init(**options['metafile_header_values'])
        
        if(defaults['info_string_var']):
            defaults['info_string_var'].set('Metafile Initilialized')
        
        #zero positioner (always start from zero positoin to ensure everything is safe)
        self.rx_positioner.zero()
    
        #start our external positioner if in use
        if options['external_position_measurements'] is not None:
            my_ext_pos = samurai_optitrack.MotiveInterface()

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
                #get positions from external measurement if available
                meas_dict_data = None
                if options['external_position_measurements'] is not None:
                    ext_pos = my_ext_pos.get_position_data(options['external_position_measurements'],**arg_options)
                    meas_dict_data = {'external_position_measurements':ext_pos}
                #get the positoin from the positoiner
                posn_vals = self.rx_positioner.get_position()
                if(run_vna):
                    [pnaTime,newPath] = pnagrab.run(newPath)
                else:
                    pnaTime = -3.14159
                    newPath = 'VNA NOT USED'
                mf.update(newPath,posn_vals,note='PNA Time : '+str(pnaTime),dict_data=meas_dict_data)
                ltr.end_point(pnaTime)
                n+=1
            
        print("All positions in CSV file completed")
        mf.finalize()
        return time.time()-run_time_start
    
    def csv_position_sweep(self,out_dir,out_name,external_position_measurements,csv_path,num_reps=1,**arg_options):
        '''
        @brief sweep positions and generate positional info on this data.
            - this does not have the same data overwrite protection as the typical metafile
        @param[in] out_dir - directory to write out to
        @param[in] out_name - output name (no extension)
        @param[in] csv_path - path to csv file
        @param[in] external_position_measurements - configuration of external measurement device (e.g. optitrack)
                OPTITRACK - provide {name:id} pairs for markers xyz components or {name:None} for rigid bodies x,y,z,alpha,beta,gamma
                    A set of measurements will be provided for each of these (e.g [{'tx_antenna':50336},{'meca_head':None},{'origin':None},{'cyl_1':50123}]).
                    For each of these points, n=num_samples (default=10) measurements are taken and the stdev, covariance matrix, and mean values are provided
        @param[in] num_reps - number of times to repeat the sweep (default to 1)
        @param[in] arg_options - keyword arguments as follows:
            settling_time - time for positioner to settle (default 0.1)
            num_samples   - number of samples to take per marker per location
            Look at samurai_optitrack for more options
        @return file path that the data is written to 
        '''
        options = {}
        options['settling_time'] = 0.1
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        tmp_name = os.path.join(out_dir,out_name+'.tmp') #create a temporary file
        fp = open(tmp_name,'w+') #temp file
        my_ext_pos = samurai_optitrack.MotiveInterface() #init optitrack
        
        #loop through csv
        self.rx_positioner.zero()
        for rep in range(num_reps):
            csvfp = open(csv_path)
            #for timing
            numLines = ss.countLinesInFile(csvfp)
            ltr = pnag.LoopTimeReport(numLines)
            
            for idx,line in enumerate(csvfp): #read each line
                print("Repeat: %2d of %2d, Position: %2d of %2d" %(rep+1,num_reps,idx+1,numLines))
                if(line.split()):
                    ltr.start_point()
                    strVals = line.split(',') #separate by csv
                    fvals = [float(i) for i in strVals]
                    self.set_position(fvals)
                    time.sleep(options['settling_time']) #sleep
                    pos_vals = self.rx_positioner.get_position()
                    ext_pos_vals = my_ext_pos.get_position_data(external_position_measurements,include_raw_data=True)
                    loc_dict = {'rep':rep,'pos_idx':idx,'robot_position':pos_vals,'external_position':ext_pos_vals}
                    fp.write(json.dumps(loc_dict)+'\n') #write the line
                    ltr.end_point()
            csvfp.close()
        
        fp.close()
        json_data = []
        with open(tmp_name,'r') as fp:
            for line in fp:
                if(line): #make sure there is stuff on the line
                    json_data.append(json.loads(line))
        with open(os.path.join(out_dir,out_name+'.json'),'w+') as fp:
            json.dump(json_data,fp,indent=2) #write out
                
    #move robot to side of table for easy mounting
    #looking from the back we have left and right
    #left is close to vna
    #right is close to sink (BE CAREFUL NOT TO PULL CABLE ON RIGHT)
    def move_to_mounting_position(self,side='left',rotation=-120):
        '''
        @brief move the Meca500 to a predetermined moutning position. 
        @param[in/OPT] side - what side of the table to move to looking from behind the meca. (defaults 'left') CAUTION: 'right' MAY BE DANGEROUS
        @param[in/OPT] rotation - how much to rotate the arm at the mounting position (default -120 degrees) CAUTION: UNTESTED ANGLES MAY BE DANGEROUS
        @return the return of set_position() (I believe it is nothing right now)
        '''
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
        '''
        @brief set the position of our Meca500 robot (or other positioner if changed)
        @param[in] pos_vals - position of robot. For meca this is in [x,y,z,alpha,beta,gamma] in mm and degrees
        @param[in/OPT] software_limits - whether or not to software limit the robot (defaults to true. These limits have been pre-tested and are hardcoded)
        @return nothing
        '''
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
        '''
        @brief bring the rx_positioner to its zero position
        '''
        self.rx_positioner.zero()
        
    
if __name__=='__main__':
    #csv_path = r"C:\SAMURAI\software\samurai\acquisition\support\sweep_files\positions_sparse.csv"
    csv_path = r"C:\SAMURAI\software\samurai\acquisition\support\sweep_files\positions_SAMURAI_planar.csv"
    wdir = r"C:\Users\ajw5\Documents\test"
    os.chdir(wdir)
    mysam = SAMURAI_System()
    mysam.connect_rx_positioner() #connect
    
    id_dict = {}
    #rigid bodies
    id_dict['meca_head'] = None
    id_dict['origin']    = None
    #labeled markers
    id_dict['tx_antenna']      = 50488
    id_dict['cyl_bislide']     = 50480
    id_dict['cyl_static']      = 50481
    mysam.csv_position_sweep('./','position_test',id_dict,csv_path,num_reps=3)
    mysam.disconnect_rx_positioner()
    
    
      
        