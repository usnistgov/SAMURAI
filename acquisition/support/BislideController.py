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
    @brief class to abstract bislide control
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
        #set options
        self.ser.port = self.com_port
        self.set_options() #write options to serial values
        self.ser.open() #open the connection
        return"Bislide Connected : %s" % self.ser.is_open
        
    def disconnect(self):
        self.ser.close()
        return "Bislide Connected : %s" % self.ser.is_open
    
    def zero(self,direction='-',motor_num=1):
        '''
        @brief zero to limit switch
        @param[in] direction '+' for positive '-' for negative 
        '''
        if direction=='-':
            com = "I%dM-0\r" %(motor_num)
        else:
            com = "I%dM0\r" %(motor_num)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        self.zero_position_reg()
        self.clear_commands()
    
    def move_steps(self,num_steps,motor_num=1):
        com = "I%dM%d\r" %(motor_num,num_steps)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        self.clear_commands()
        
    def move_mm(self,distance_mm,motor_num=1):
        steps = self.mm_to_steps(distance_mm)
        self.move_steps(steps,motor_num)
        return self.get_position()
    
    def set_position_steps(self,num_steps,motor_num):
        com = "IA%dM%d\r" %(motor_num,num_steps)
        self.enable_online_mode()
        self.write(com)
        self.write('R')
        self.wait_motor_ready()
        self.clear_commands()
    
    def set_position(self,location_mm,motor_num=1):
        steps = self.mm_to_steps(location_mm)
        self.set_position_steps(steps,motor_num)
        return self.get_position()
        
        
    def get_limit_status(self):
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
        prog = self.query('lst',terminator=b'\r')
        return prog
        
    def enable_online_mode(self):
        self.write('F')
        return self.get_controller_status()
    
    def zero_position_reg(self):
        '''
        @brief dont move the slider, but zero the position registers
        '''
        self.write('N')
        return self.get_position()
    
    def clear_commands(self):
        self.write('C')
        
    def interactive_write(self,msg):
        #interactive command as shown in the manual
        self.write('F') #put the VXM online
        self.write('N') #zero position registers
        self.write(msg)
        self.clear_commands()
        
        
    def wait_motor_ready(self,ready_character='^'):
        while(self.read() != ready_character):
            pass
    
    def get_position_steps(self,motor_num=1):
        motor_dict = {}
        motor_dict[1] = 'X'
        motor_dict[2] = 'Y'
        motor_dict[3] = 'Z'
        motor_dict[4] = 'T'
        rv = self.query(motor_dict[motor_num],terminator=b'\r')
        return int(rv)
    
    def get_position(self,motor_num=1):
        steps = self.get_position_steps(motor_num)
        return self.steps_to_mm(steps)
        
    def get_controller_status(self):
        qv =  self.query('V')
        #now change to a message
        status_dict = {}
        status_dict['B'] = 'Host busy'
        status_dict['R'] = 'Host ready'
        status_dict['J'] = 'Host in jog/slew mode'
        status_dict['b'] = 'Host jogging/slewing'
        #and return the message and value
        return status_dict[qv],qv
        
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
        return steps*self.options['mm_per_rotation']/self.options['steps_per_rotation']
    
    def mm_to_steps(self,mm): 
        return round(mm*self.options['steps_per_rotation']/self.options['mm_per_rotation'])

def get_bits(val):
    ba = bytearray(val)
    len_ba = len(ba)
    mybits = [0]*8*len_ba #get zeros
    bit_num=0 #bit to select
    for byte in ba: #loop through each byte
        for i in range(7): #mask out each bit
            mybits[bit_num] = int(bool(byte&(1<<i)))
            bit_num+=1 #increment bit we are on
    return mybits
        
        
        
        

