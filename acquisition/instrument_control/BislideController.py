# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:25:02 2019  
Class to control bislide  
@author: ajw5  
"""
from collections import OrderedDict
import six
import serial
import time

default_info = OrderedDict()
default_info['manufacturer'] = 'Velmex'
default_info['baudrate'] = 9600
default_info['timeout'] = 5 #in seconds

#some values for rotation
default_info['inch_per_rotation'] = 0.1;
default_info['mm_per_rotation'] = default_info['inch_per_rotation']*25.4
default_info['steps_per_rotation'] = 400

#typically on com 22

class BislideController():
    '''
    @brief class to abstract bislide control. THIS IS ONLY FOR VELMEX BISLIDES  
    '''
    
    def __init__(self,com_port,**options):
        '''
        @brief initialize the controller  
        @param[in] com_port - com port (ie 'COM22') to connect to  
        @param[in] options  - dictionary of options  
        '''
        #com port
        self.com_port = com_port
        #serial connection 
        self.ser = serial.Serial();
        
        self.options = {} #set our options
        for key,value in six.iteritems(default_info):
            self.options[key] = value
        for key,value in six.iteritems(options):
            self.options[key] = value
            
    
    def connect(self):
        '''
        @brief open the bislide serial port  
        '''
        #set options
        self.ser.port = self.com_port
        self.set_options() #write options to serial values
        self.ser.open() #open the connection
        return"Bislide Connected : %s" % self.ser.is_open
        
    def disconnect(self):
        '''
        @brief close the bislide serial port  
        '''
        self.ser.close()
        return "Bislide Connected : %s" % self.ser.is_open
    
    def zero(self,direction='-',motor_num=1,zero_position_reg=True):
        '''
        @brief zero to limit switch  
        @param[in] direction '+' for positive '-' for negative   
        @param[in/OPT] zero_position_reg - do we reset our position to zero?
            defaults to true, but if we zero to the + direction should probably
            be false otherwise all position values will be negative  
        '''
        if direction=='-':
            com = "I%dM-0\r" %(motor_num)
        else:
            com = "I%dM0\r" %(motor_num)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        if zero_position_reg:
            self.zero_position_reg()
        self.clear_commands()
    
    def move_steps(self,num_steps,motor_num):
        '''
        @brief move a motor a given number of steps  
        @param[in] num_steps - number of steps to move  
        @param[in] motor_num - which motor number to move  
        '''
        com = "I%dM%d\r" %(motor_num,num_steps)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        self.clear_commands()
        
    def move_mm(self,distance_mm,motor_num=1):
        '''
        @brief move a motor a given number of mm  
        @param[in] num_steps - number of steps to move  
        @param[in/OPT] motor_num - which motor number to move (default 1)  
        '''
        steps = self.mm_to_steps(distance_mm)
        self.move_steps(steps,motor_num)
        return self.get_position()
    
    def set_position_steps(self,num_steps,motor_num):
        '''
        @brief set the position of the bislide in steps  
        @param[in] num_steps - how many steps from 0 to move to  
        @param[in] motor_num - which motor to move  
        '''
        com = "IA%dM%d\r" %(motor_num,num_steps)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        self.clear_commands()
    
    def set_position(self,location_mm,motor_num=1):
        '''
        @brief move a motor a given location from zero in mm  
        @param[in] num_steps - number of steps to move  
        @param[in/OPT] motor_num - which motor number to move (default 1)  
        '''
        steps = self.mm_to_steps(location_mm)
        self.set_position_steps(steps,motor_num)
        return self.get_position()
        
        
    def get_limit_status(self):
        '''
        @brief get the status of the limit switches  
        @return a dictionary with entries 1-,1+,2-,2+ 
            which shows whehter the limit switches are activated  
        '''
        self.enable_online_mode()
        lim_val = self.query('?')
        motor_bits = get_bits(lim_val.encode())
        motor_lims = {}
        motor_lims['1-'] = motor_bits[0]
        motor_lims['1+'] = motor_bits[1]
        motor_lims['2-'] = motor_bits[2]
        motor_lims['2+'] = motor_bits[3]
        return motor_lims
        
    def read_current_program(self):
        '''
        @brief get the current program the slide is running  
        '''
        prog = self.query('lst',terminator=b'\r')
        return prog
        
    def enable_online_mode(self):
        '''
        @brief enable the ability to control interactively 
            (one command at a time)  
        '''
        self.write('F')
        return self.get_controller_status()
    
    def zero_position_reg(self):
        '''
        @brief dont move the slider, but zero the position registers  
        '''
        self.write('N')
        return self.get_position()
    
    def clear_commands(self):
        '''
        @brief clear all commands in the queue  
        '''
        self.write('C')
        
    def interactive_write(self,msg):
        '''
        @brief interactively write commands Should probably be DEPRECATED. 
            Not commonly used because we zero the position regs here.  
        '''
        #interactive command as shown in the manual
        self.write('F') #put the VXM online
        self.write('N') #zero position registers
        self.write(msg)
        self.clear_commands()
        
        
    def wait_motor_ready(self,ready_character='^'):
        '''
        @brief wait until our motor returns a ready character (blocking)  
        '''
        while(self.read() != ready_character):
            pass
    
    def get_position_steps(self,motor_num):
        '''
        @brief get our position in steps of a motor  
        @param[in] motor_num - which motor to get the steps of  
        '''
        motor_dict = {}
        motor_dict[1] = 'X'
        motor_dict[2] = 'Y'
        motor_dict[3] = 'Z'
        motor_dict[4] = 'T'
        rv = self.query(motor_dict[motor_num],terminator=b'\r')
        return int(rv)
    
    def get_position(self,motor_num=1):
        '''
        @brief get the position of our motor in mm  
        @param[in/OPT] motor_num - which motor to query (default 1)  
        '''
        steps = self.get_position_steps(motor_num)
        return self.steps_to_mm(steps)
        
    def get_controller_status(self):
        '''
        @brief get and unpack the status of the controller  
        '''
        qv =  self.query('V')
        #now change to a message
        status_dict = {}
        status_dict['B'] = 'Host busy'
        status_dict['R'] = 'Host ready'
        status_dict['J'] = 'Host in jog/slew mode'
        status_dict['b'] = 'Host jogging/slewing'
        #and return the message and value
        return status_dict[qv],qv
    
    def set_step_speed(self,steps_per_second=2000,motor_num=1):
        '''
        @brief set the speed of the motor. Default is 2000 Steps per second  
        @param[in/OPT] steps_per_second - number of steps per second (default 2000)
            2000 is also the value the controller starts up at  
        @param[in/OPT] motor_num - which motor to set the speed for (default 1)  
        @note This is set for 70% power (SmMx command) This can be changed
            To use 100% power using the SAmMx command (m is motor#, x is steps_per_second)  
        '''
        sps_int = int(steps_per_second) #convert to integer
        command = "S%dM%d\r" %(int(motor_num),sps_int) #generate the command
        self.write(command) #write to the controller
        
    def set_options(self,**options):
        '''
        @brief quick method to set options outside of init  
        '''
        for key,value in six.iteritems(options):
            self.options[key] = value
        #now set the options
        self.ser.baudrate = self.options['baudrate']
        self.ser.timeout  = self.options['timeout']
        
    def write(self,msg):
        '''
        @brief write a message to the bislide  
        @param[in] msg - message to write  
        '''
        self.ser.write(msg.encode())
        
    def read(self,terminator=None):
        '''
        @brief reads all data in buffer from a command  
        @param[in] OPTIONAL terminator - if provided, read_until(terminator) will be used  
        @return message read  
        '''
        if terminator:
            rv = self.ser.read_until(terminator)
        else:
            rv = self.ser.read_all().decode()
            while(rv==''): #block until we get a message
                time.sleep(0.01) #need this for slow communication
                rv = self.ser.read_all().decode()
        return rv
        
    def query(self,msg,terminator=None):
        '''
        @brief send followed by recieve  
        @param[in] msg - message to send  
        @param[in] read_bytes - number of bytes to read from the buffer (this is blocking)  
        @return bytes read from controller  
        '''
        self.write(msg)
        rv = self.read(terminator)
        return rv
    
    def steps_to_mm(self,steps):
        '''
        @brief convert # of steps to millimeters  
        @param[in] steps - number of steps to convert  
        @return converted value in millimeters  
        '''
        return steps*self.options['mm_per_rotation']/self.options['steps_per_rotation']
    
    def mm_to_steps(self,mm): 
        '''
        @brief convert millimeters to # of steps  
        @param[in] mm - number of millimeters to convert  
        @return converted value in steps rounded to the nearest whole number  
        '''
        return round(mm*self.options['steps_per_rotation']/self.options['mm_per_rotation'])

def get_bits(val):
    '''
    @brief unpack bits from a given value in LSB order  
    @param[in] val - value to unpack to bits  
    @return array of unpacked bits  
    '''
    ba = bytearray(val)
    len_ba = len(ba)
    mybits = [0]*8*len_ba #get zeros
    bit_num=0 #bit to select
    for byte in ba: #loop through each byte
        for i in range(7): #mask out each bit
            mybits[bit_num] = int(bool(byte&(1<<i)))
            bit_num+=1 #increment bit we are on
    return mybits
        
        
        
        

