# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 10:15:14 2019

@brief: This is a class for a Simple GUI to control the Meca500 robot

@author: ajw5
"""

import numpy as np

from Meca500 import Meca500;
from samurai_tktools import NotificationGroup
from samurai_tktools import ButtonGroup
from samurai_tktools import EntryAndTitle
from samurai_tktools import CheckGroup

try: #backward compatability with 2.7
    import Tkinter as tk
    #import tkFileDialog
except ImportError:
    import tkinter as tk
    #from tkinter import filedialog as tkFileDialog
import six

class Meca500_GUI:
    
    def __init__(self,tkroot,**options):
        
        defaults={'robot_addr':'10.0.0.5'}
        #take in our values
        self.options = {}
        for key, value in six.iteritems(defaults):
            self.options[key] = value
        for key, value in six.iteritems(options):
            self.options[key] = value
            
        self.meca = Meca500();
        
        meca_status_list = ['Activated','Homed','Simulation','Error','Paused','EOB','EOM','Connected']
        meca_status_init = list(np.zeros(len(meca_status_list)))
        
        self.meca_status = NotificationGroup(tkroot,'Meca Status',meca_status_list,meca_status_init)
        self.meca_status.pack()
        print(self.meca_status.get())
    
        #self.sv = tk.StringVar()
        #self.test_text = tk.Label(tkroot,textvariable=self.sv);
        #self.test_text.pack()
        #self.sv.set("Testing")
            
        self.connect_button_group = ButtonGroup(tkroot,'Connection',['Connect','Disconnect'],[self.connect,self.disconnect])
        self.connect_button_group.pack();
            
        #meca address input
        self.robot_addr_textbox = EntryAndTitle(tkroot,"Robot IP Address",self.options['robot_addr'],width=50);
        self.robot_addr_textbox.pack(side=tk.RIGHT);
        
    def connect(self):
        print('Connected')
        self.meca_status.update_from_list([1,0,1,0,1,0,1,0])
        
    def disconnect(self):
        print('Disconnected')
        
    def update_meca_status():
        self.meca_status.update
        
        
        
        
root = tk.Tk()
cdg = Meca500_GUI(root)
root.mainloop()
