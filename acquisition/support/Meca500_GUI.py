# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 10:15:14 2019

@brief: This is a class for a Simple GUI to control the Meca500 robot

@author: ajw5
"""

import numpy as np
import signal
import atexit

from Meca500 import Meca500
from samurai_tktools import NotificationGroup
from samurai_tktools import ButtonGroup
from samurai_tktools import EntryAndTitle
from samurai_tktools import CheckGroup

import sched, time, threading

try: #backward compatability with 2.7
    import Tkinter as tk
    #import tkFileDialog
except ImportError:
    import tkinter as tk
    #from tkinter import filedialog as tkFileDialog
import six

class Meca500_GUI:
    
    def __init__(self,tkroot,**options):
        
        defaults={'robot_addr':'10.0.0.5','status_update_interval':1}
        #take in our values
        self.options = {}
        for key, value in six.iteritems(defaults):
            self.options[key] = value
        for key, value in six.iteritems(options):
            self.options[key] = value
            
        #positioner class
        self.meca = Meca500()
        
        #notifications
        meca_status_list = ['Activated','Homed','Simulation','Error','Paused','EOB','EOM','Connected']
        meca_status_init = list(np.zeros(len(meca_status_list)))
        
        self.meca_status = NotificationGroup(tkroot,'Meca Status',meca_status_list,meca_status_init)
        self.meca_status.pack()

    
        #self.sv = tk.StringVar()
        #self.test_text = tk.Label(tkroot,textvariable=self.sv);
        #self.test_text.pack()
        #self.sv.set("Testing")
        
        #connection buttons
        self.connect_button_group = ButtonGroup(tkroot,'Connection',['Connect','Disconnect'],[self.connect,self.disconnect])
        self.connect_button_group.pack()
        
        #activate/deactivate buttons
        self.activation_button_group = ButtonGroup(tkroot,'Activation',['Activate','Deactivate'],[self.activate,self.deactivate])
        self.activation_button_group.pack()
        
        #moving buttons
        self.location_button_group = ButtonGroup(tkroot,'Movement',['Home','Mounting Position'],[self.home,self.move_to_mounting_position])
        self.location_button_group.pack()

        #sim buttons
        self.location_button_group = ButtonGroup(tkroot,'Movement',['Simulation On','Simulation Off'],[self.activate_sim,self.deactivate_sim])
        self.location_button_group.pack()
        
        #meca address input
        self.robot_addr_textbox = EntryAndTitle(tkroot,"Robot IP Address",self.options['robot_addr'],width=50)
        self.robot_addr_textbox.pack(side=tk.BOTTOM)
        
        # meca return value
        self.meca_rv_sv = tk.StringVar()
        self.meca_rv_sv.set("No Return Value")
        self.meca_rv_frame = tk.LabelFrame(tkroot,text='Meca Return Message')
        self.meca_rv_text = tk.Label(self.meca_rv_frame,textvariable=self.meca_rv_sv,width=100)
        self.meca_rv_text.pack()
        self.meca_rv_frame.pack(side=tk.BOTTOM)
        
        #register sigterm to kill status thread
        signal.signal(signal.SIGTERM,self.exit_function) #CTRL-C
        atexit.register(self.exit_function) #regular exit
        self.run_thread = True
        
         #schedule for status update
        #self.sch = sched.scheduler(time.time,time.sleep) #initialize scheduler
        #self.sch.enter(self.options['status_update_interval'],1,self.update_meca_status,())
        #self.status_update_thread = threading.Thread(target=self.sch.run)
        self.status_update_thread = threading.Thread(target=self.update_meca_status)
        self.status_update_thread.daemon = True
        self.status_update_thread.start()
 
        
    def update_rv(self,val_str):
        self.meca_rv_sv.set(val_str)
        
    def connect(self):
        rv = self.meca.connect(ip_addr=self.robot_addr_textbox.get()) #connect to ip address
        rv2 = self.meca.set_default_frames_and_velocity() #ensure we set defaults so nothing breaks
        self.meca_rv_sv.set(str([rv,rv2]))
        
    def disconnect(self):
        rv = self.meca.disconnect_socket() #connect to ip address
        self.meca_rv_sv.set(str(rv))
        
    def update_meca_status(self):
        #self.meca_status.update
        #if(self.run_thread):
        #    self.sch.enter(self.options['status_update_interval'],1,self.update_meca_status,())
        while self.run_thread:
            [status_list,_] = self.meca.get_status() #get the status list
            self.meca_status.update_from_list(status_list)
            time.sleep(self.options['status_update_interval'])
        return
        
        
    def home(self):
        rv=self.meca.home()
        self.meca_rv_sv.set(str(rv))

    def zero(self):
        rv=self.meca.zero()
        self.meca_rv_sv.set(str(rv))
        
    def move_to_mounting_position(self):
        rv=self.meca.move_to_mounting_position()
        self.meca_rv_sv.set(str(rv))
        
    def activate(self):
        rv=self.meca.activate()
        self.meca_rv_sv.set(str(rv))
        
    def deactivate(self):
        rv=self.meca.deactivate()
        self.meca_rv_sv.set(str(rv))

    def activate_sim(self):
        rv=self.meca.activate_sim_mode()
        self.meca_rv_sv.set(str(rv))
        
    def deactivate_sim(self):
        rv=self.meca.deactivate_sim_mode()
        self.meca_rv_sv.set(str(rv))
        
    def exit_function(self):
        self.run_thread=False #stop our threads
        self.status_update_thread.join()
        exit(0)
        
        
        
        
        
root = tk.Tk()
cdg = Meca500_GUI(root)
root.mainloop()
