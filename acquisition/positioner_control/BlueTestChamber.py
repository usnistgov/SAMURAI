# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:44:56 2019

@author: rdj
"""
path = r"Q:/public/Reverb Measurements Wireless/Labview code/Config files/Blue Test Config/09_20_BT_1.17_btc_update"


import subprocess
import os
import re
from samurai.acquisition.support.BislideController import BislideController

class BlueTestChamber:
     def __init__(self,velmex_com_port,**arg_options):
         '''
         @Initializes the BlueTest chamber as well as the Velmex slides
         @param[in] velmex_com_port - COM# that communicates with velmex slides. BlueTest chamber does not have a COM port that needs to be declared (check .btc file)
         '''
         self.options = {}
         self.options['chamber_directory'] = r"Q:/public/Reverb Measurements Wireless/Labview code/Config files/Blue Test Config/09_20_BT_1.17_btc_update"
         for k,v in arg_options.items():
            self.options[k] = v
         self.com_port = velmex_com_port
         self.initialize()
        
     def init_linear_slides(self,com_port):
          '''
          @Initializes the vertical and linear slides
          @param[in] com_port - COM# that communicates to the Velmex Controller
          '''
          #com_port = 'COM4'
          self.lin_slides = BislideController(com_port)
          self.lin_slides.connect()
          self.lin_slides.zero(motor_num=1) #Horizontal
          self.lin_slides.zero(motor_num=2) #Vertical
     
     def hslide_move_to_dist(self,distance):
         '''
         @Moves the horziontal BiSlide to specified distance in cm
         @param[in] distance - distance in mm from zero the slide will move to
         '''
         limit = 303
         if distance <= limit:
             self.lin_slides.set_position(distance,motor_num = 1)
         elif distance > limit:
             raise Exception("Horizontal slide maxes out at %d mm, %d mm exceeds this" %(limit, distance))
         
     def vslide_move_to_dist(self,distance):
         '''
         @Moves the horziontal BiSlide to specified distance in cm
         @param[in] distance - distance in mm from zero the slide will move to
         '''
         limit = 309
         if distance <= limit:
             self.lin_slides.set_position(distance,motor_num = 2)
             
         elif distance > limit:
             raise Exception("Vertical slide maxes out at %d mm, %d mm exceeds this" %(limit, distance))
         
     def run_chamber_command(self,command):
        '''
        @Function that changes directory temporarily, runs the chamber_control_server.exe commands, and then switches back
        @param[in] command - string that corresponds to the specific commands available for use in chamber_control_Server.exe
        '''
        old_dir = os.getcwd()
        out_str = None
        try:
            os.chdir(self.options['chamber_directory'])
            out_str = subprocess.check_output(['chamber_control ',command])
            os.chdir(old_dir)
        except Exception as e:
            os.chdir(old_dir)
            raise e
        return out_str
    
     
     def initialize(self):
         '''
         @Re-Inititalizes the BlueTest chamber and the Linear Slides
         '''
         self.run_chamber_command('init')
         self.init_linear_slides(self.com_port)

     
     def tt_move_to_angle(self,desired_angle):
         '''
         @FIXME THIS IS A MESS. WAITING ON TT CONVERSION, ALSO NEED TO CHANGE IT TO SET POSITION AND MAKE IT PADDLE AND TT FRIENDLY
         @Function that takes in an angle to go to, converts to steps, then calls run_chamber_command to move the turntable
         @param[in] desired_angle - angle, in degrees, the turntable needs to turn to
         '''
         if desired_angle <= 339: #was 350.8, 338.705
             #angle_in_steps = desired_angle * (70000/339)
            angle_in_steps = desired_angle * 207
            command_string ='goto:3:%d' % (angle_in_steps)
            self.run_chamber_command(command_string)
            self.run_chamber_command('wait')

         elif desired_angle > 339: #was 339
            raise Exception("Turn table only turn from 0 to 339, %d exceeds this",desired_angle)
         #//FIXME ADD PADDLE CASE AND CHANGE TO set_position
     
     def tt_zero(self):
         '''
         @Function that brings the turn table back to starting position
         '''
         self.tt_move_to_angle(0)
         
     def deinitialize(self):
         '''
         @Exits out of the BlueTest server as well as disconnects the bislides
         '''
         self.run_chamber_command('exit')
         self.lin_slides.disconnect()
         
     def stirrer_get_position(self,stirrer):
         '''
         @Grabs the position of a/all stirring mechanism(s) in the BlueTest Chamber
         @param[in] stirrer - can be either 'tt' for turn table, 'paddle#' for paddle#,or 'all' for all stirrers 
         @param[out] returns the encoder value of each of the mechanisms. FOR TT IT IS THE ANGLE
         '''
         #FIXME need to add the eoncoder to distance conversion for the paddles
         #Regular Expression
         v= self.run_chamber_command('report?').decode()
         listre = re.compile('\d+ */ *\d+')
         stirrer_return = listre.findall(v)
         encode_search = re.compile('\d+')
         padd_1_pos = encode_search.findall(stirrer_return[0])
         padd_2_pos = encode_search.findall(stirrer_return[1])
         tt_pos = encode_search.findall(stirrer_return[2])
         if stirrer == 'tt':
             tt_angle = int(tt_pos[0]) / 207 #Conversion to degrees
             tt_max_angle = int(tt_pos[1]) / 207
             return tt_angle
             #FIXME NEED TO ADD TT FUNCTIONALITY, also remeber to cast to int
         elif stirrer == 'paddle1':
             return padd_1_pos
             #FIXME NEED TO ADD PADDLE FUNCTIONALITY
         elif stirrer == 'paddle2':
             return padd_2_pos
         elif stirrer == 'all':
             #FIXME NEED TO ADD ALL FUNCTIONALITY
             pass
         
     def get_position(self):
         '''
         @Returns an array of the positions [V slide, H slide, TurnTable]
         @ V slide and H slide are in mm's. TurnTable is in degrees
         @Need to add functionality for returning paddle positions
         '''
         #Grab BlueTest Chamber parameters
         tt_angle = self.stirrer_get_position('tt')
         
         #Grab linear slider information (mm)
         h_dist = self.lin_slides.get_position(1)
         v_dist = self.lin_slides.get_position(2)
         position_array = [v_dist,h_dist,tt_angle]
         
         return position_array
    
     def set_position(self,set_position_array):
         '''
         @Function that moves vslide, hslide and tt to a set mm/angular position
         @param[in] set_position_array
         '''
         self.vslide_move_to_dist(set_position_array[0])
         self.hslide_move_to_dist(set_position_array[1])
         self.tt_move_to_angle(set_position_array[2])
    
     def set_position_no_tt(self,set_position_array):
         '''
         @Function that moves vslide, hslide. No TT becuase it take forever
         @param[in] set_position_array
         '''
         self.vslide_move_to_dist(set_position_array[0])
         self.hslide_move_to_dist(set_position_array[1])