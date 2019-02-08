# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 15:19:22 2018

-This is a library ot control the Meca500 positioner.
Currently all of the calls are blocking. This means that every sent command
waits for the corresponding TCP response. This could be edited in the future
to have a socket server listen for tcp responses, but this is really not needed
for now so is not implemented.

-The top set of commands are basic TCP/IP commands wrapped from the socket package.
The lower set of commands are specific to the Meca500. The blocking is done by
using the query function. This could be changed by just using the send and as stated,
listening for replies on socket server (I'm not sure whether this works with 
TCP/IP communication or not).

-Errors from the meca are currently all just thrown as exceptions. No handling is done.
Execution will terminate if an error message is recieved
@author: ajw5
"""

test_position = [50,0,200,0,0,0]

import six
import socket
import re
import numpy as np
import itertools
import os

class Meca500:
    
    def __init__(self,ip_addr='10.0.0.5',simulation_mode=False,**options):
        '''
        @brief Initialize but do not connect the Meca500 positioner class

        @param[in] ip_addr - ip address of Meca500 on the network
        @param[in] simulation_mode - Whether to set the Meca500 to built in simulation mode on connection
        @param[in] options - keyword args 
                            'port' - port to connect
                            'recbv_buf_size' - socket receive buffer
        @return Class of type Meca500
        '''
        defaults = {'port':10000,'recv_buf_size':1024}
        self.options = {}
        for key, value in six.iteritems(defaults):
            self.options[key] = value
        for key, value in six.iteritems(options):
            self.options[key] = value
        self.ip_addr = ip_addr
        self.port = self.options['port']
        self.recv_buf_size = self.options['recv_buf_size']

        #initialize some flags
        self.connected = 0
        self.active    = 0
        self.homed     = 0
        self.paused    = 0
        self.err_flg = 0
        
        #is this a simulation
        self.simulation_mode = simulation_mode
        if(simulation_mode):
            print("INFO: Running in simulation mode")
      
    #just disconnect. do not deactivate.
    def __del__(self):
        '''
        @brief what to do when the object is deleted
        '''
        self.disconnect() #run close to ensure we shut down correctly
        
    def connect(self,ip_addr=None,port=None):
        '''
        @brief create the socket connection to the meca
        @param[in] ip_addr - ip address of the meca (if none use the class default)
        @param[in] port - port to connect on (if none use class default)
        @return Recieved data after connection
        '''
        if self.connected: #return error if we already connected
            return -1
        if ip_addr is None:
            ip_addr = self.ip_addr
        if port is None:
            port = self.port
        #now connect the socket
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.settimeout(30) #30 second timeout
        self.socket.connect((ip_addr,port))
        self.connected = True
        #it should return the name
        return self.recv()
    
    #wrapper for tcpip send. Will add null terminator if not there
    def send(self,msg):
        '''
        @brief send data to meca. This will check for some errors and add null terminator
        @param[in] msg - message to send
        '''
        if(self.connected):
            if msg[-1]!='\0':
                msg+='\0' #add NUL if not there
            #now send
            return self.socket.send(msg.encode())
        else:
            print("ERROR: Not connected to Meca500")
            return -1
        
    #wrapper for socket recv
    #this will separate the 
    def recv(self,buf_size=None,raw=False):
        if(self.connected):
            if buf_size is None:
                buf_size=self.recv_buf_size
            #now recieve
            recv_str = self.socket.recv(buf_size).decode()
            
            #return MecaReturnMessage class
            try: #handle the error if it occurs
                return MecaReturnMessage(recv_str)
            except MecaError:
                self.err_flg = 1 #set the error flag
                raise #raise the exception again
        else:
            print("ERROR: Not connected to Meca500")
            return -1

    #send followed by recive
    def query(self,msg,buf_size=None):
        '''
        @brief send a message then wait for a response
        @param[in] msg - message to send
        @param[in] buf_size - recieve buffer size (class default if none)
        @return -1 for error, MecaReturnMessage on success
        '''
        #check if were connected
        if(self.connected):
            #send
            self.send(msg)
            #then recive
            return self.recv(buf_size=buf_size)
        else:
            print("ERROR: Not connected to Meca500")
            return -1
        
    #wrapper of socket close
    def close(self,zero_flg=True):
        '''
        @brief clear errors, zero, deactivate, and disconnect from robot
        @param[in] zero_flg - Whether or not to zero the robot (defaults to True)
        '''

        #zero,deactivate,close socket
        if(self.connected): #only do any of this if were connected  
            self.get_status() #update the status
            if(self.err_flg): #clear errors
                self.clear_errors()
            if(self.active): #then zero and deactivate
                if(zero_flg): #then zero
                    self.zero() #zero
                self.deactivate() #deactivate
            if(self.simulation_mode): #do we run in simulation mode
               self.deactivate_sim_mode()
            self.disconnect()
        self.connected=0
        
    #close socket
    def disconnect(self):
        '''
        @brief close the socket to the robot
        '''
        self.socket.close()
    
    ##------------------------------------
    ## From here we have all our Wrappers
    ## for the Meca commands themselves
    ## these are very specific
    ## and assume we are correctly connected
    ##------------------------------------
    
    #run initialization routine. 
    #will connect,activate, then home
    def initialize(self):
        '''
        @brief initialize the robot. Connect, Activate, Home
        '''
        if not self.connected: 
            self.connect()
        if(self.simulation_mode): #do we run in simulation mode
                self.activate_sim_mode()
        self.get_status() #update the status after we connect
        if(not self.err_flg):
            if not self.active:
                self.activate()
            if not self.homed:
                self.home()
            print("Meca Ready to Move")
        else:
            print("Meca in error. Please run 'clear_errors' errors then re-run")
        #return 1;
    
    #home the meca
    def home(self):
        '''
        @brief Home the meca. Must be done after connecting and activating, but before moving
        @return MecaReturnMessage
        '''
        rv = self.query('Home')
        self.homed = 1
        return rv
    
    #turn on motors and remove brakes
    def activate(self):
        '''
        @brief activate the robots motors. Must be done after connecting but before homing and moving
        @return MecaReturnMessage
        '''
        rv = self.query('ActivateRobot')
        self.active = 1
        return rv
    
    def deactivate(self):
        '''
        @brief Deactivate the robots motors
        @return MecaReturnMessage
        '''
        rv = self.query('DeactivateRobot')
        self.active = 0
        self.homed = 0
        return rv
        
    def get_joints(self):
        '''
        @brief get the joint angles in degrees of the robot
        @return floating point list of joint angles
        '''
        rv = self.query('GetJoints')
        return rv.get_float_list()
        
    def set_joints(self,joint_angle_list):
        '''
        @brief set joints to specific angles
        @param[in] joint_angle_list - list of joint angles to set to 
        @return MecaReturnMessage
        '''
        return self.move_template('MoveJoints',joint_angle_list)
    
    def set_wrf(self,wrf_vals):
        '''
        @brief set the world reference frame
            More information on reference frames can be found in the Meca500 User manual.
        @param[in] wrf_vals - list of values to set the world reference frame to 
        @return MecaReturnMessage
        '''
        return self.move_template('SetWRF',wrf_vals)
    
    def set_trf(self,trf_vals):
        '''
        @brief set the Tool reference frame with respect to the world reference frame.
            More information on reference frames can be found in the Meca500 User manual.
        @param[in] wrf_vals - list of values to set the tool reference frame to 
        @return MecaReturnMessage
        '''
        return self.move_template('SetTRF',trf_vals)
    
    #zero joints
    def zero(self):
        '''
        @brief zero the robot
        @return MecaReturnMessage
        '''
        return self.set_joints([0,0,0,0,0,0])
    
    #com_list is command list corresponding to [x,y,z,alpha,beta,gamma] for 
    #cartesian position and angle. This command can take unreliable paths to 
    #get to the desired position so BE CAREFUL
    def set_pose(self,com_list):
        '''
        @brief set position ('pose') of robot in [x,y,z,alpha,beta,gamma] coordinates
        @param[in] com_list - position of robot in  [x,y,z,alpha,beta,gamma]
        @return MecaReturnMessage
        '''
        return self.move_template('MovePose',com_list)
    
    #alias for set_pose
    set_position = set_pose
    
    def get_pose(self):
        '''
        @brief get the positoin ('pose') in [x,y,z,alpha,beta,gamma] coordinates
        @return List of floating point values for [x,y,z,alpha,beta,gamma] position
        '''
        rv = self.query('GetPose')
        return rv.get_float_list()
    
    #alias for get_pose
    get_position = get_pose
    
    def set_velocity(self,percentage):
        '''
        @brief set the joint velocity of the robot as a percentage
        @param[in] percentage - joint velocity in percentage of maximum (10% usually used for SAMURAI)
        @return MecaReturnMessage
        '''
        rv = self.query('SetJointVel(%3.1f)'%(percentage))
        return rv
    
    #make linear motions. This command is limited in motion range because it
    #cannnot pass through singularities. if you get stuck. Try move_pos
    #com_list again is [x,y,z,alpha,beta,gamma] specifying cartesian coords and
    #euler angle at which to point
    def set_lin(self,com_list):
        return self.move_template('MoveLin',com_list)
    
    #generic template for move commands. Not long to type but got tired of repeating it
    #com_list is the arguments and command is the command (ie MovePose)
    def move_template(self,command,com_list):
        '''
        @brief template for sending move commands
        @param[in] command - string command to send to positioner
        @param[in] com_list - list of values to send with command
        @return MecaReturnMessage
        '''
        if(len(com_list)!=6): #they all seem to require 6 args
            print("ERROR: 6 positional arguments required")
            return -1
        #error checking done
        str_list = [str(c) for c in com_list]
        #and send the command
        return self.query('%s(%s)'%(command,','.join(str_list)))
    
    #clear errors
    def clear_errors(self,reset_motion=True):
        '''
        @brief Reset errors and motion on the robot. This can sometimes cause socket communication errors in the future
                so test run robot after this command is used before synthetic apertures are taken
        @param[in] reset_motion - OPTIONAL(True) whether or not to reset the motion
        '''
        rv = self.query('ResetError')
        self.get_status() #update the status
        if(self.paused and reset_motion): #unpause if we are paused
            crv = self.query('ClearMotion') #clear all motions because we were in error
            prv = self.query('ResumeMotion') #then resume our motion
        else:
            prv = "Not Paused"
            crv = "Motion Not Cleared"
        return rv,crv,prv
    
    #activate simulation mode
    def activate_sim_mode(self):
        '''
        @ brief Activate simulation mode. This must be done after ocnnection but before motors are activated
        @return MecaReturnMessage
        '''
        return self.query('ActivateSim')
    
    #deactivate simulation mode
    def deactivate_sim_mode(self,activate_motors=True):
        '''
        @ brief Activate simulation mode. This must be done after connection but before motors are activated
        @return MecaReturnMessage
        '''
        return self.query('DeactivateSim')
    
    def get_status(self):
        '''
        @brief get the status of the robot as a list of flags and set flags in class. These values are: 
            [0] - Activation state
            [1] - Homing state
            [2] - Simulation mode
            [3] - Error status
            [4] - Pause status
            [5] - end of block?
            [6] - end of movement
        @return a copy of the list recieved
        '''
        rv = self.query('GetStatusRobot')
        vals = rv.get_float_list() # get our values
        #set the ones in question
        self.active = int(vals[0])
        self.homed  = int(vals[1])
        self.err_flg= int(vals[3])
        self.paused = int(vals[4]) #this occurs after errors
        #and return the list
        return vals
    
    
    #once initialized corners of a cube
    def demo(self):
        #start_pos_1 = [250,-100,80,0,90,0];
        #with trf = [0,0,131,0,-90,0] and wrf=[321,0,0,0,0,0]
        #with trf at tool tip and wrf directly below tip at base level when zeroed
        start_pos_1 = [60,-100,80,0,0,0] #x offset here from original by -190
        size_mm_1 = [0,200,200]
        step_size_mm_1 = [1,5,5]
        vals = gen_scan_grid_planar(start_pos_1,size_mm_1,step_size_mm_1)
        for v in vals:
            self.set_pose(v)
        return vals
        #draw the upper part of the cube
        #upper_square_pos = 
  

#class to hold messages returned by meca
#this just gives a little more flexibility when handling the messages
#automatically does some parsing and storage for us
class MecaReturnMessage:
    
    err_msg_nums = range(1000,1015) #these are the same over all instances
    
    def __init__(self,raw_meca_message):
        #save the raw value
        self.raw_msg = raw_meca_message
        self.msg_num = -1 #init value
        self.msg = '' #init_value
        self.err_flg = 0
        
        #now parse
        self.parse_raw_msg(raw_meca_message)
        
    #split the message to ge the message number and the message alone as a string
    def parse_raw_msg(self,msg):
        strip_chars = '][\0'
        re_c = re.compile('[%s]*'%strip_chars) #reg expression to replace
        msg_split = msg.split('][') #spit the first and second parts
        msg_split_clean = [re_c.sub('',v) for v in msg_split] #then strip our other characters
        self.msg_num = int(msg_split_clean[0]) #save the message number
        self.msg = msg_split_clean[1] #save the message
        #check if this is an error message
        if(self.msg_num in MecaReturnMessage.err_msg_nums): #if it is an error message
            self.err_flg = 1 #this message is an error
            raise MecaError(self.msg) #raise an exception to stop execution
    
    #return the message as a list of floats 
    def get_float_list(self,delim=','):
        return [float(val) for val in self.msg.strip().split(delim)] #separate out our measured values
    
    #have the representation be the message
    def __repr__(self):
        return repr(self.msg)
    
#exception could be made one for each but easier to just do one
class MecaError(Exception):
    def __init__(self,err_msg):
        self.err_msg = err_msg
    def __str__(self):
        return repr(self.err_msg) 
    
    
    
#----------Some positionering things------------------#
        
    
def demo_planar():
    #start_pos_1 = [250,-100,80,0,90,0];
    #with trf = [0,0,131,0,-90,0] and wrf=[321,0,0,0,0,0]
    #with trf at tool tip and wrf directly below tip at base level when zeroed
    start_pos_1 = [60,-100,80,0,0,0]#x offset here from original by -190
    size_mm_1 = [0,200,200]
    step_size_mm_1 = [1,5,5]
    vals = gen_scan_grid_planar(start_pos_1,size_mm_1,step_size_mm_1)
    return vals

def demo_planar_center():
    sing_offset = 1 #offset to avoid singularity
    center_pos = [60+sing_offset,0,200+sing_offset,0,0,0]
    step       = [0,3,3]
    size       = [0,102,102]
    vals = gen_scan_grid_planar_from_center_point(center_pos,size,step)
    return vals
        
#generate from center point
def gen_scan_grid_planar_from_center_point(center_point,size_mm,step_size_mm):
    #just translate to edge position
    size_2 = np.zeros(6)
    size_2[0:3] = np.array(size_mm,dtype=float)/2
    start_position = np.array(center_point,dtype=float)-(np.array(size_2,dtype=float))
    return gen_scan_grid_planar(start_position,size_mm,step_size_mm)
        
#start position should be a 6 value location for MovePose
#this will start at start_position and move for the required step_size_mm [x,y,z]
#until it reaches the size_mm [x,y,z] values
#just generates the value
def gen_scan_grid_planar(start_position,size_mm,step_size_mm):
    if(len(start_position)!=6): #they all seem to require 6 args
        print("ERROR: Start position requires 6 elements")
        return -1
    #extract our values from inputs
    x_sp = start_position[0]
    y_sp = start_position[1]
    z_sp = start_position[2]
    alph = start_position[3]
    bet  = start_position[4]
    gam  = start_position[5]
    x_sm = size_mm[0]
    y_sm = size_mm[1]
    z_sm = size_mm[2]
    x_ssm = step_size_mm[0]
    y_ssm = step_size_mm[1]
    z_ssm = step_size_mm[2]
        #check if zero step (meaning we dont move)
    if not x_ssm:
        x_ssm=1; x_sm = 0
    if not y_ssm:
        y_ssm=1; y_sm = 0
    if not z_ssm:
        z_ssm=1; z_sm = 0
    #now build arrays for each dimension including last point
    x_pos = np.arange(x_sp,x_sp+x_sm+x_ssm,x_ssm)
    y_pos = np.arange(y_sp,y_sp+y_sm+y_ssm,y_ssm)
    z_pos = np.arange(z_sp,z_sp+z_sm+z_ssm,z_ssm)
    #now generate all of the points
    MG = np.meshgrid(x_pos,y_pos,z_pos,alph,bet,gam)
    #now reshape into an easily iterable thing
    point_list = np.transpose(MG).reshape((-1,6))
    return point_list


#shift all values by a given array of shift_value
def shift_scan_grid(vals,shift_value):
    if(len(shift_value)!=6): #they all seem to require 6 args
        print("ERROR: Start position requires 6 elements")
        return -1
    shifted_vals = vals+np.array(shift_value)
    return shifted_vals


def shift_scan_grid_csv(csv_name_in,shift_value,csv_name_out=''):
    '''
    @brief - shift values in a csv file
    @param[in] csv_name_in - name of input file to shift
    @param[in] sfhit_value - amount to shift positoins by
    @param[in] csv_name_out - output name. By default will overwrite input file
    @return - shifted values
    '''
    if(csv_name_out==''):
        csv_name_out = csv_name_in #overwrite
    pts = read_points_from_csv(csv_name_in) #read points
    shift_pts = shift_scan_grid(pts,shift_value) #shift points
    write_nparray_to_csv(csv_name_out,shift_pts)
    return shift_pts
   

def gen_offset_positions(start_plane,shift_value_list,flip_flg=True):
    '''
    @brief - This generates a set of positions with multiple planes using a list of shift values
    @param[in] - start_plane - reference plane from which everything is shifted
    @param[in] - shift_value_list - list of shift values to include in the output postitions
    @note - this function does not automatically include the start_plane in the output positions.
             [0,0,0,0,0,0] must be entered as an item in shift_value_list
    @param[in] - flip_flg - flip every other plane so we dont have to move back to the beginning
    @return - List of positoins for the robot to go to of the planes appended to one another
    '''
    shifted_planes = []
    i = 0 #shift plane count
    for shift_val in shift_value_list:
        positions = shift_scan_grid(start_plane,shift_val)
        if flip_flg: #if the flag tells, flip every other
            if i%2: #if odd plane
                positions = np.flipud(positions)
            i+=1
        shifted_planes.append(positions) #and write them to our list
        
    #now join into numpy array
    return np.concatenate(shifted_planes),shifted_planes

def minimize_point_distance(pts):
    '''
    @brief - change point order to minimize distance between each point
    @param[in] - pts - points to reorder
    @return - new_pts - copy of pts reordered to minimize distance traveled
    '''
    pts_new = pts.copy()
    return pts_new

def gen_offset_position_csv(csv_name_in, shift_value_list,flip_flg=True):
    '''
    @brief - Generate shifted csv file from input file positions. Outputs will be csv 
              files of separate shifted planes named as <csv_name_in>_shift_#.csv and all
              shifted plane positions together in <csv_name_in>_shift_full.csv
    @param[in] - csv_name_in - name of input csv positions to shift
    @param[in] - shift_value_list - list of shifts performed on the input positions
        @note - shift_value_list must inlcude [0,0,0,0,0,0] in order to include original positoins
    @param[in] - flip_flg - flip every other plane so we dont have to move back to the beginning
    '''
    start_plane = read_points_from_csv(csv_name_in) #read in data
    [shift_full,shift_list] = gen_offset_positions(start_plane,shift_value_list,flip_flg) #shifted values
    fname_no_extension = os.path.join(os.path.split(csv_name_in)[0],os.path.split(csv_name_in)[-1].split('.')[0]) #safely remove extension
    write_nparray_to_csv(fname_no_extension+'_shift_full.csv',shift_full) #write out full
    
    #now write out each shifted file in case we need it
    ind_shift_dir = os.path.join(os.path.split(csv_name_in)[0],'individual_shift_files')
    if not os.path.exists(ind_shift_dir):
        os.mkdir(ind_shift_dir) #make the directory
    for i in range(len(shift_list)):
        write_nparray_to_csv(os.path.join(ind_shift_dir,fname_no_extension)+'_shift_'+str(i)+'.csv',shift_list[i])
    return shift_full
    
        
    

#generate cylindrical scan grid around a given center point. Sweep -sweep_angle/2 to +sweep_angle/2 from origin
#sweep angle in degrees. Height in mm, radius in mm. step in degrees
#currently just for z axis
def gen_scan_grid_cylindrical(origin,radius,height,height_step_size_mm,sweep_angle,angle_step_size_degrees):
    #origin is given as [x,y,z,alpha,beta,gamma]
    if(len(origin)!=6): #they all seem to require 6 args
        print("ERROR: Origin requires 6 elements")
        return -1
    #unpack the values
    xo = float(origin[0])
    yo = float(origin[1])
    zo = float(origin[2])
    alpho = float(origin[3])
    beto  = float(origin[4])
    gamo  = float(origin[5])
    #along z axis gamma is our theta value
    #first calculate our angles
    #range is gamma+sweep/2 to gamma-sweep/2
    theta_start = gamo-float(sweep_angle)/2
    theta_end   = gamo+float(sweep_angle)/2
    theta_vals  = np.arange(theta_start,theta_end+angle_step_size_degrees,angle_step_size_degrees)
    #now calculate where our outer circle is
    #x = rcos(theta)+xo, y=rsin(theta)+yo, z=z;
    #start with the x,y values
    x = radius*np.cos(theta_vals*np.pi/180.)+xo; y = radius*np.sin(theta_vals*np.pi/180.)+yo
    #now generate z from origin to origin+height
    z = np.arange(zo,zo+height+height_step_size_mm,height_step_size_mm)
    #now combine to get all of our values
    #now tile this for the number of z locations
    x_tot     = np.tile(x,len(z))
    y_tot     = np.tile(y,len(z))
    z_tot  = np.repeat(z,len(theta_vals)) #repeat z for every theta
    theta_tot = np.tile(theta_vals,len(z))
    alph_tot  = np.repeat(alpho,theta_tot.size)
    bet_tot   = np.repeat(beto,theta_tot.size)
    #finally combine into positoins
    pos_vals = np.array([x_tot,y_tot,z_tot,alph_tot,bet_tot,theta_tot]).transpose()
    return pos_vals
    
    
def curve_planar_array_z(pts,curve_radius_mm):
    '''
    @brief - generate cylindrical array from planar array around z axis. This will curve about the center of the planar array
    @param[in] - pts - points for the planar array. Assuming a single array
    @param[in] - curve_radius - radius to curve along in millimeters
    @return - new curved cylindrical array
    '''
    planar_center = (np.max(pts,axis=0)-np.min(pts,axis=0))/2+np.min(pts,axis=0) #find the center of the points
    center_normal_angle_rad = np.arctan2(planar_center[1],planar_center[0]) #(y,x)
    pos_from_center = pts-planar_center #position relative to center
    
    #Our z wont change but we will calculate the new x and y from the old x and y
    x_pos_from_center = pos_from_center[:,0] #extract x values
    y_pos_from_center = pos_from_center[:,1] #extract y values
    dist_from_center = np.sqrt(x_pos_from_center**2+y_pos_from_center**2) #arc length along the new mapped circle
    angle_from_center_rad = dist_from_center/curve_radius_mm #angle by tracing arc length along mapped circle
    angle_sign = np.arctan2(y_pos_from_center,x_pos_from_center)+1e-20; angle_sign /= np.abs(angle_sign)
    circle_angle = (angle_from_center_rad+center_normal_angle_rad) #angle along circle for each point
    theta_vals = np.rad2deg(circle_angle) #theta angle of our robot in degrees
    x_shift = curve_radius_mm*(1-np.cos(circle_angle))
    y_shift = dist_from_center - np.sqrt(dist_from_center**2-x_shift**2)
    
    #now set the output
    pts_out = pts.copy() #make a copy of the input
    pts_out[:,5] = theta_vals*angle_sign #set the pointing of the horn
    pts_out[:,0] = pts[:,0]-x_shift #x change (ONLY WORKS FOR YZ PLANE RIGHT NOW)
    pts_out[:,1] = pts[:,1]-y_shift*angle_sign #y change
    return pts_out
    
#add points to stop at 
#def add_safety_manuever
    
#flip
def flip_alternate_rows(pts,row_length):
    '''
    @brief flip alternating rows for better pattern
    @param[in] - pts - points in aperture to flip rows
    @param[in] - row_length - number of points per aperture row (same as num columns)
    '''
    pts_new = pts.copy()
    num_rows = int(np.size(pts,0)//row_length)
    for i in range(1,num_rows,2): #every other row
        cur_row_st = i*35
        cur_row_end = ((i+1)*35)
        cur_row_vals = pts[cur_row_st:cur_row_end] #get the values of the current row
        flip_cr = np.flipud(cur_row_vals) #flip the values
        pts_new[cur_row_st:cur_row_end] = flip_cr
    return pts_new
    
#cylinder demo
def demo_cylinder():
    origin = [-50,0,100,0,0,0]
    sweep_angle = 90
    height = 100
    angle_step_size_degrees = 5
    height_step_size_mm = 20
    radius = 100
    return gen_scan_grid_cylindrical(origin,radius,height,height_step_size_mm,sweep_angle,angle_step_size_degrees)
    
#set our pose from a list of poses
#def move_pos_list
def write_nparray_to_csv(fname,np_array_vals):
    np.savetxt(fname,np_array_vals,delimiter=',')
    
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
#plot the points x,y,z,alpha,beta,gamma
def plot_points(data_points,fig_handle='default',magnitude=10):
    if(fig_handle=='default'): #if not provided, generate a figure
        fig = plt.figure()
    else:
        fig = fig_handle
    ax = fig.gca(projection='3d')
    [x,y,z] = data_points.transpose()[0:3]
    [u,v,w] = robot_to_vector(data_points,magnitude)
    ax.quiver(x,y,z,u,v,w)
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_zlabel('Z (mm)')
    ax.set_xlim(-175,175)   ; ax.set_ylim(-175,175)  ; ax.set_zlim(0,350)
    ax.scatter3D(0,0,0); ax.scatter3D(0,0,190)
    ax.text3D(0,0,190,'TCP Origin\n (Tip of antenna w/\n all joints zero)',horizontalalignment='left')
    ax.text3D(0,0,0,'WRF Origin',horizontalalignment='left')
    return fig

#load values in from CSV
def read_points_from_csv(fname):
    vals = np.loadtxt(fname,delimiter=',')
    return vals
    
#data in list of x,y,z,alpha,beta,gamma positions 
 #change robot positions to vector of antenna for plotting
def robot_to_vector(data_points,magnitude=1): #alpha beta gamma to normalized vector
    #assuming z axis is up, y is toward tx, and x is side to side. This does not calculate anything with y axis
    data = data_points.transpose() #make each direction (x,y,z,alpha,...) its own list of values
    alpha = np.array(data[3])/180.*np.pi; gamma = np.array(data[5])/180.*np.pi
    theta = gamma; phi = alpha
    u = magnitude*np.cos(phi)*np.cos(theta)
    v = magnitude*np.cos(phi)*np.sin(theta)
    w = np.sin(alpha)
    return np.array([u,v,w])
    
        
        
        
#mymeca = Meca500();
        