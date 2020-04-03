# -*- coding: utf-8 -*-
"""
@date Wed Oct 31 13:47:17 2018
@brief Full High level system controls for samurai
@author: ajw5
"""

from samurai.acquisition.instrument_control import AutoPnaGrabber as pnag    #for running pnagrabber
from samurai.acquisition.instrument_control.PnaController import PnaController
from samurai.acquisition.support import samurai_metaFile as smf     #for keeping track of data
from samurai.acquisition.instrument_control.Meca500  import Meca500       #our posisioner
import samurai.acquisition.support.samurai_support  as ss      #some other functions
import samurai.acquisition.instrument_control.SamuraiMotive as samurai_optitrack  #import optitrack tracking

from samurai.base.SamuraiDict import SamuraiDict

import six
import json

import numpy as np

import time
import os

#these are default values. These seem to change with the system realatively often so they are placed here at the top
pnagrabber_template_path = './template.pnagrabber'
vna_visa_addr = 'TCPIP0::192.168.0.2::inst0::INSTR'
rx_positioner_address = '192.168.0.5'

class SamuraiSystem():
    '''
    @brief initialize class to control SAMURAI measurement system  
    @note This class is also aliased as samurai.analysis.SAMURAI_System.SAMURAI_System
    @param[in/OPT] is_simulation - whether or not to run the Meca500 in simultion mode (defaults to NO simulation)  
    @param[in/OPT] arg_options - optional keyword arguments as follows:   
        - vna_visa_address - visa address of the VNA  
        - rx_positioner_address - address of the rx positioner. for Meca500 this is a IP address  
        - trf_pos - Tool reference frame position of the robot. This is automatically set on connection to the Meca and checked against the CSV file header
        - wrf_pos - World reference frame position of the robot. This is automatically set on connection to the Meca and checked against the CSV file header
    '''
    #to run as simulation simply pass is_simualtion=true
    def __init__(self,is_simulation=False,**arg_options):
        '''@brief Constructor'''
        tool_length = 131 #length of tool off face in mm. Change for weird tools
        #THIS IS A NEW REFERENCE FRAME AS OF 5/10/2019. This is checked to match in the csv file
        #this reference frame makes x left/right, y up/down, and z in/out (propogation direction) when looking from behind the robot
        self.options = {}
        self.options['vna_visa_address'] = vna_visa_addr
        self.options['rx_positioner_address'] = rx_positioner_address
        self.options['trf_pos'] = [0,0,tool_length,0,0,90] #tool reference frame (-90 to align axes with wrf). THE frame here is different and seems to be in ([z,y,z,gamma,beta,alpha]) compared to world frame
        self.options['wrf_pos'] = [tool_length+190,0,0,0,90,90] #world reference frame at robot base z but x of tool (+190 for base to tip at zeroed postiion)
        for key, value in six.iteritems(arg_options):
            self.options[key] = value
        self.vna_visa_addr = self.options['vna_visa_address']
        self.is_connected = False
        self.set_simulation_mode(is_simulation)
        #self.connect_rx_positioner();
        self.rx_positioner = Meca500(rx_positioner_address) #meca500 positioner

        
    def connect_rx_positioner(self,run_simulation=None):
        '''
        @brief Connect and initialize the rx positioner (Meca500) for movement
        @param[in/OPT] run_simulation - whether to run in simulation mode (default: False)  
        @return list of Meca return values [set_sim_mode_rv,init_rx_pos_rv,set_wrf_rv,set_trf_rv,set_velocity_rv]  
        '''
        if not run_simulation:
            run_simulation = self.is_simulation #set to default unless overwritten
            rv1=self.rx_positioner.set_simulation_mode=run_simulation
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
        '''@brief Alias for self.rx_positioner.get_status()'''
        return self.rx_positioner.get_status() #get the status list
    
    def disconnect_rx_positioner(self,zero_flg=True):
        '''@brief run self.rx_positioner.close()'''
        self.rx_positioner.close(zero_flg)
        self.is_connected = False
        
    def set_simulation_mode(self,on_off):
        """
        @brief Set whether the robot operations in simulation mode.
            This can only be done when disconnected, so we will check that  
        @param[in] on_off - True to turn on Simulation, False to turn off Simulation  
        @return 0 for success, -1 if value cannot be set (because we are connected currently)  
        """
        #if(self.is_connected):
        #    return -1 #we can only change the flag while disconnected
        #else we return success after setting simulation
        self.is_simulation = on_off
        return 0 #success
    
    def set_options(self,**arg_options):
        '''@brief easy way to set options'''
        for key, value in six.iteritems(arg_options):
            self.options[key] = value
        
    def csv_sweep(self,data_out_dir,csv_path,run_vna=True,**arg_options):
        '''
        @brief measure a synthetic aperture with the SAMURAI system using positions from a CSV (comma separated value) file  
        @param[in] data_out_dir - where the data will be output   
        @param[in] csv_path - path to the comma separated value (CSV) file  
        @param[in/OPT] run_vna - whether or not to run the VNA when sweeping (default to true=run the vna)  
        @param[in/OPT] arg_options - keyword arguments as follows:  
            - note - note to put in the metafile  (defaults to '')
            - output_name - name of the output files (defaults to 'meas')  
            - settling time - time in seconds to let robot settle (default 0.1s)  
            - metafile_header_values - dictionary of values to overwrite or append to in metafile header (defaults to nothing)  
            - comment_character - character or list of characters for comments (default #)  
            - external_position_measurements - configuration of external measurement device (e.g. optitrack). 
			@note For OPTITRACK provide {name:id} pairs for markers xyz components or {name:None} for rigid bodies x,y,z,alpha,beta,gamma
				A set of measurements will be provided for each of these (e.g [{'tx_antenna':50336},{'meca_head':None},{'origin':None},{'cyl_1':50123}]).
                For each of these points, n=num_samples (default=10) measurements are taken and the stdev, covariance matrix, and mean values are provided
            - meas_obj - class to use as a measure tool just needs a .measure method  
            - meas_obj_init_args - arguments for the class __init__() method  
            - meas_obj_meas_args - arguments for the class .measure() method  
        @return sweep time
        '''
        if not self.is_connected:
            print("Positioner Not Connected")
            return

        #output_file_type should match that of pnagrabber
        options = {'note':'none','output_directory':'./','output_name':'meas','output_file_type':'s2p',}
        options['settling_time'] = .1 #settling time in seconds
        options['info_string_var'] = None #be able to set outside stringvar for update info
        options['metafile_header_values'] = {}
        options['external_position_measurements'] = None
        options['comment_character'] = '#'
        options['meas_obj'] = PnaController #object for measurement besides pnagrabber
        options['meas_obj_init_args'] = (self.options['vna_visa_address'],) #tuple of args for __init__ of external_measure_obj
        options['meas_obj_meas_args'] = ({3:2},) #tuple of args for __init__ of external_measure_obj (default port map 3 to 2)

        for key, value in six.iteritems(arg_options):
            options[key] = value
         
        if run_vna:
            pna_measure = options['meas_obj'](*options['meas_obj_init_args'])
            
        mf = smf.metaFile(csv_path,self.options['vna_visa_address'],root_dir=data_out_dir)
        mf.init(**options['metafile_header_values'])
        
        if(options['info_string_var']):
            options['info_string_var'].set('Metafile Initilialized')
        
        #zero positioner (always start from zero positoin to ensure everything is safe)
        self.rx_positioner.zero()
    
        #start our external positioner if in use
        if options['external_position_measurements'] is not None:
            my_ext_pos = samurai_optitrack.MotiveInterface()

        #verify csv file
        self.verify_position_file(csv_path,options['comment_character'])
        
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
                if any(line.strip()[0]==np.array([options['comment_character']])): #then its a comment
                   continue
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
                    [pnaTime,newPath] = pna_measure.measure(newPath,*options['meas_obj_meas_args'])
                else:
                    pnaTime = -3.14159
                    newPath = 'VNA NOT USED'
                mf.update(newPath,posn_vals,note='PNA Time : '+str(pnaTime),dict_data=SamuraiDict(meas_dict_data))
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
        @param[in/OPT] external_position_measurements - configuration of external measurement device (e.g. optitrack)  
        @note For OPTITRACK provide {name:id} pairs for markers xyz components or {name:None} for rigid bodies x,y,z,alpha,beta,gamma
				A set of measurements will be provided for each of these (e.g [{'tx_antenna':50336},{'meca_head':None},{'origin':None},{'cyl_1':50123}]).
                For each of these points, n=num_samples (default=10) measurements are taken and the stdev, covariance matrix, and mean values are provided
        @param[in/OPT] num_reps - number of times to repeat the sweep (default to 1)  
        @param[in/OPT] arg_options - keyword arguments as follows:  
            - settling_time - time for positioner to settle (default 0.1)  
            - num_samples   - number of samples to take per marker per location  
            - comment_character - character or list of characters for comments (default #)  
            - Look at samurai_optitrack for more options
        @return file path that the data is written to   
        '''
        options = {}
        options['settling_time'] = 0.1
        options['comment_character'] = '#'
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        tmp_name = os.path.join(out_dir,out_name+'.tmp') #create a temporary file
        fp = open(tmp_name,'w+') #temp file
        my_ext_pos = samurai_optitrack.MotiveInterface() #init optitrack
        
        #verify csv file
        self.verify_position_file(csv_path,options['comment_character'])
        
        #loop through csv
        self.rx_positioner.zero()
        for rep in range(num_reps):
            csvfp = open(csv_path)
            #for timing
            numLines = ss.countLinesInFile(csvfp)
            ltr = pnag.LoopTimeReport(numLines)
            idx = 0
            for line in (csvfp): #read each line
                if any(line.strip()[0]==np.array(options['comment_character'])):
                   continue
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
                    idx+=1
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
            #mounting_position = [-250,445,140,0,rotation,90] #trf v1
            mounting_position = [445,140,-250,0,90,rotation] #trf v2
        if(side.lower()=='right'):
            #mounting_position = [-250,-445,140,0,rotation,-90]
            mounting_position = [-445,140,-250,0,-90,-1*rotation]
            
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
            np_lower_bound = np.array([-1e3,25,-1e3,-360,-360,-360]) #just limit y axis
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
    
    def get_positioner_status(self):
        '''
        @brief get and print the status of the positioner  
        '''
        [_,_,s] = self.rx_positioner.get_status() #get the status string
        print(s)
        
    def zero(self):
        '''
        @brief bring the rx_positioner to its zero position  
        '''
        self.rx_positioner.zero()
        
    def verify_position_file(self,file_path,comment_char = '#'):
        '''
        @brief verify that the file of positions is for the correct reference frames
                just raise an exception if the file is not value for the current reference frame.
                The verification looks for the following values to check against:  
                    - #WRF (or world reference frame or with _) = [x,y,z,alpha,beta,gamma]  
                    - #TRF (or tool reference frame or with _) = [x,y,z,alpha,beta,gamma]  
        @param[in] file_path - the path to the position file (e.g. *.csv,etc)  
        @param[in/OPT] comment_char - character or list of characters for comments  
        '''
        reference_value_strings = np.array(['X','Y','Z','ALPHA','BETA','GAMMA'])
        comment_lines = []
        with open(file_path) as fp:  #open the file
            for line in fp: # go through each line
                if all(line.strip()[0] != np.array([comment_char])):
                    continue #not a comment line
                comment_lines.append(line.strip()[1:]) #all except the first character
        #now parse the comments for 
        trf_read = None
        wrf_read = None
        for cl in comment_lines:
            split_line = cl.split('=')
            if len(split_line)!=2: #then we dont have an equal sign (or too many)
                continue
            #now massage the input values
            var_name = split_line[0].strip().lower().replace(' ','_') #this is our variable name (e.g. TRF)
            var_val = [float(i) for i in split_line[1].replace('[','').replace(']','').strip().split(',')] #list of float values
            if(var_name=='tool_reference_frame' or var_name=='trf'):
                trf_read = np.array(var_val)
            if(var_name=='world_reference_frame' or var_name=='wrf'):
                wrf_read = np.array(var_val)
        #now check these values
        if  np.array(trf_read).shape==() or np.array(wrf_read).shape==(): #make sure these are both provided
            raise(Exception("No world or tool reference frame values provided in the position file.\n"
                            "These should be in the format as follows (both are required)\n\n"
                            "# TRF = [X_trf,Y_trf,Z_trf,ALPHA_trf,BETA_trf,GAMMA_trf]\n"
                            "# WRF = [X_wrf,Y_wrf,Z_wrf,ALPHA_wrf,BETA_wrf,GAMMA_wrf]\n"))
        if any(self.options['trf_pos']!=trf_read):
            raise(Exception("Tool reference frame does not match at %s" 
                            %('['+','.join(reference_value_strings[self.options['trf_pos']!=trf_read])+']')))
        if any(self.options['wrf_pos']!=wrf_read):
            raise(Exception("World reference frame does not match at %s" 
                            %('['+','.join(reference_value_strings[self.options['wrf_pos']!=wrf_read])+']')))
        
# Alias for backward compatability
SAMURAI_System = SamuraiSystem

    
if __name__=='__main__':
    #csv_path = r"C:\SAMURAI\software\samurai\acquisition\support\sweep_files\positions_sparse.csv"
    
    #trf/wrf v2 testing
    #mysam = SAMURAI_System(True)
    mysam = SAMURAI_System(False)
    mysam.connect_rx_positioner()
    [stat,_,_] = mysam.rx_positioner.get_status()
    #if not stat[2]:
    #    raise Exception("Not in simulation mode")
    mysam.csv_sweep('./test/','sweep_files/samurai_planar_dp.csv',run_vna=False)
    mysam.disconnect_rx_positioner()
    
    
    ##positional testing
    #csv_path = r"C:\SAMURAI\software\samurai\acquisition\support\sweep_files\positions_SAMURAI_planar.csv"
    #wdir = r"C:\Users\ajw5\Documents\test"
    #os.chdir(wdir)
    #mysam = SAMURAI_System()
    #mysam.connect_rx_positioner() #connect
    
    #id_dict = {}
    #rigid bodies
    #id_dict['meca_head'] = None
    #id_dict['origin']    = None
    ##labeled markers
    #id_dict['tx_antenna']      = 50488
    #id_dict['cyl_bislide']     = 50480
    #id_dict['cyl_static']      = 50481
    #mysam.csv_position_sweep('./','position_test',id_dict,csv_path,num_reps=3)
    #mysam.disconnect_rx_positioner()
    
    
    
      
        