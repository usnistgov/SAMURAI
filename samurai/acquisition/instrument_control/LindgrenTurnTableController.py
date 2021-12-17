# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 13:03:56 2018
Controller for ETS Lindgren Turn Table Model 2005
raw and not-raw angles are separated because it was desired to 
be able to use negative angles, but the positioner only allows
angles between 0 and 360 it seems.
The positioner always starts up at 0 degrees and this value can be changed
with the CP command. This is run in the set_origin method. The angle is then
read and everything is adjusted to this new origin when not using raw angles
@author: ajw5
"""
import time
import pyvisa as visa

class LindgrenTurnTableController:

    def __init__(self,visa_addr = 'ASRL6::INSTR',init_speed=1,init_lims=[-50,50],set_new_origin=False,origin=180):
        self.vrm = visa.ResourceManager()
        self.lims = init_lims
        try:
            self.dev = self.vrm.open_resource(visa_addr)
        except:
            print("ERROR: could not contact VISA device")
            print("(ETS LINDGREN TURN TABLE 2005)      ")
            print("------------------------------------")
            print("THIS MAY CAUSE OTHER ERRORS!!!!!!!!!")
            print("It is recommended the device is     ")
            print(" shutdown and cable is unplugged and")
            print("plugged back in                     ")
            print("Restarting python may be required to")
            print("Reset the visa driver also          ")
            print("------------------------------------")
        try:
            self.info = self.dev.query('*IDN?')
            if(set_new_origin):
                self.set_origin() #assume were at our origin at startup
            else:
                self.origin = origin
                self.set_lims(init_lims[0],init_lims[1])
            self.set_speed(init_speed)
        except:
            print("ERROR: Could not get device info.   ")
            print("This may cause other issues         ")
            print("Resetting the visa interface is     ")
            print("recommended                         ")

        
        #approach direction is the direction we must ensure we approach from
        #this prevents any terrible slop in the system. Also can specify number of degrees to go past point when reducing slop
    def set_angle(self,angle_degrees,raw=False):
        if(not raw):
            angle_degrees+=self.origin
            
        while(self.dev.query('DIR?').strip()!='N'):
            time.sleep(0.01)
        #now go to our actual angle specified
        com = 'SK %f' %(angle_degrees)
        return self.dev.query(com)
        
    #set the angle and wait for the turn table to reach its position
    def set_angle_block(self,angle_degrees,raw=False,reduce_slop=True,approach_dir='CCW',pass_angle=5):
        #move past specified angle to reduce slop if coming from a different direction
        if(reduce_slop):
            #now make sure we come from the same direction
            cur_angle = self.get_angle(raw=raw)
            if(approach_dir=='CW' and cur_angle>angle_degrees): #we would be moving in counterclockwise direction here
                self.set_angle(angle_degrees-pass_angle)
                
            elif(approach_dir=='CCW' and cur_angle<angle_degrees):
                self.set_angle(angle_degrees+pass_angle)

            while(self.dev.query('DIR?').strip()!='N'):
                time.sleep(0.01)
        #set the angle to go to
        self.set_angle(angle_degrees,raw=raw)
        #wait till we hit that angle
        while(self.dev.query('DIR?').strip()!='N'):
            time.sleep(0.01)
        
        
    def set_speed(self,speed_rpm):
        com = 'S %4.1f' %(speed_rpm)
        return self.dev.query(com)
    
    def get_speed(self):
        return float(self.dev.query('S?'))
        
    def get_angle(self,raw=False):
        #return angle adjusted to origin.
        raw_angle = float(self.dev.query('CP?'))
        if(raw):
            return raw_angle
        else:
            return raw_angle-self.origin
        
    
    def set_current_position(self,angle_degrees):
        com = 'CP %4.1f' %(angle_degrees)
        return self.dev.query(com)
    
    #set the current position as origin and move everything negative and positive from here
    def set_origin(self,center_angle=180):
        self.center_angle=center_angle
        self.set_current_position(center_angle) #use 360 degrees as our origin
        self.origin = self.get_angle(raw=True)
        self.set_lims(self.lims[0],self.lims[1])
    
    #with respect to current origin of 0. CCW is negative, CW is positive
    def set_lims(self,ccw_lim=-90,cw_lim=90,raw=False):
        #if we dont want raw values adjust to our origin
        self.lims = [ccw_lim,cw_lim]
        if(not raw):
            cw_lim+=self.origin
            ccw_lim+=self.origin
        #set clockwise
        self.dev.query('UL %4.1f' %(cw_lim))
        #set counterclockwise
        self.dev.query('LL %4.1f' %(ccw_lim))
        
        return self.dev.query('UL?'),self.dev.query('LL?')
    
    