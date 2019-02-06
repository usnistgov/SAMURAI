# -*- coding: utf-8 -*-
"""
Created on Fri Aug 03 11:01:12 2018

@author: ajw5
"""

#GUI for samurai synthetic aperture measurements

# -*- coding: utf-8 -*-
"""
Created on Thu Aug 02 11:16:54 2018

@author: ajw5
"""

# -*- coding: utf-8 -*-
"""
Created on Mon May 14 08:34:24 2018

This script edits our metafile and moves our data and new copy of metafile to outDir
This assumes our data has been calibrated with the MUF and DUTs are within that output directory form the MUF

Before running 
 - calibrate all data with muf
 - Ensure calibrated data folder is in same folder as measurements

@author: ajw5
"""

#import matplotlib as mpl
#mpl.use('TkAgg') #use tk backend

import os
import sys
import numpy as np
#sam_control_path = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Software/SAMURAI_Control'
#sys.path.append(sam_control_path)
from SAMURAI_System import SAMURAI_System

#import my tktools
#samurai_support_libs_dir = r'U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\support';
#sys.path.append(samurai_support_libs_dir)
from support.Meca500 import plot_points
from support.samurai_tktools import FilePicker
from support.samurai_tktools import DirPicker
from support.samurai_tktools import EntryAndTitle
from support.samurai_tktools import CheckGroup

try: #backward compatability with 2.7
    import Tkinter as tk
    #import tkFileDialog
except ImportError:
    import tkinter as tk
    #from tkinter import filedialog as tkFileDialog
    


class SAMURGUI:
    def __init__(self, tkroot):
        
        self.defaults = dict()
        self.defaults['search_dir']    = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/' #working directory
        self.defaults['csv_path']      = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\test/positions.csv"
        self.defaults['template_path'] = r"U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\support/template.pnagrabber"
        self.defaults['output_dir']    = self.defaults['search_dir']
        self.defaults['vna_addr']      = "TCPIP::10.0.0.2::inst0::INSTR"
        self.defaults['robot_addr']    = "10.0.0.5"
        # self.cal
        self.tkroot = tkroot
        self.tkroot.title("SAMURAI Measurement tool")
        
        self.runButton = tk.Button(tkroot,text='Measure',command=self.measure)
        self.runButton.pack(side=tk.TOP)
        
        self.setupOptions = tk.LabelFrame(self.tkroot,text='Setup')
        self.setupOptions.pack(side= tk.LEFT)
        
        self.wdir = self.defaults['search_dir']

        #--- output directory ---#
        self.output_picker = DirPicker(self.tkroot,"Output Directory",self.defaults['output_dir'],bd=5,highlightbackground="gray",highlightcolor="black",highlightthickness=5)
        self.output_picker.pack()

        #---csv input ---#
        ftypes = (("Position List","*.csv"),)
        self.csv_frame = tk.Frame(self.tkroot,bd=5,highlightbackground="gray",highlightcolor="black",highlightthickness=5,width=100)
        self.csv_picker = FilePicker(self.csv_frame,"CSV File",self.defaults['csv_path'],filetypes=ftypes,width=90)
        self.csv_picker.pack(side=tk.LEFT)
        self.csv_plot_button = tk.Button(self.csv_frame,text='Plot Points',command=self.plot_points)
        self.csv_plot_button.pack(side=tk.RIGHT)
        self.csv_frame.pack()
        
        #---template input---#
        ftypes = (("PNA Grabber Menu","*.pnagrabber"),)
        self.template_picker = FilePicker(self.tkroot,"Template File",self.defaults['template_path'],filetypes=ftypes,bd=5,highlightbackground="gray",highlightcolor="black",highlightthickness=5)
        self.template_picker.pack()
        
        self.addr_frame = tk.Frame(self.tkroot)
        self.addr_frame.pack()
        #visa address input
        self.visa_addr_textbox = EntryAndTitle(self.addr_frame,"VNA Visa Address",self.defaults['vna_addr'],width=50)
        self.visa_addr_textbox.pack(side=tk.LEFT)
        
         #meca address input
        self.robot_addr_textbox = EntryAndTitle(self.addr_frame,"Robot IP Address",self.defaults['robot_addr'],width=50)
        self.robot_addr_textbox.pack(side=tk.RIGHT)
        
        #now build checkboxes for w2p select and binary select and whether or not to simulate
        button_list = ['Simulation?','Run VNA?']
        self.check_menu = CheckGroup(self.tkroot,'Options',button_list)
        self.check_menu.pack()
        
        
        note_width = 100;note_height=5
        self.meas_note_box = tk.Text(self.tkroot,width = note_width,height=note_height,bd=10)
        self.meas_note_box.insert(tk.END,"Put information on the measurement here.")
        self.meas_note_box.pack()
        

        #vna menu
        self.vnaMenu = []
        
        self.my_run_sam = RunSamurai()
        
        
    def measure(self):
        wdir = self.output_picker.get()
        template_file = self.template_picker.get()
        csv_file = self.csv_picker.get()
        note = self.meas_note_box.get("1.0",tk.END)
        visa_addr = self.visa_addr_textbox.get()
        robot_addr = self.robot_addr_textbox.get()
        is_sim = self.check_menu.get_button_state('Simulation?')
        run_vna = self.check_menu.get_button_state('Run VNA?')

        self.check_menu.print_debug()
        #update working directoyr and run
        self.my_run_sam.set_directory(wdir)
        print("Measuring and saving to "+os.getcwd())
        self.my_run_sam.measure(wdir,visa_addr,robot_addr,template_file,csv_file,note,is_sim,run_vna)
        
    def plot_points(self):
        print("Plotting CSV Points")
        csv_file = self.csv_picker.get()
        #csv_data = read_points_from_csv(csv_file);
        csv_data = np.loadtxt(csv_file,delimiter=',')
        plot_points(csv_data)
        #return fig; 
        
    
         

class RunSamurai:
    
    def __init__(self):
        next
        #where our template is
        #elf.template_path = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/USC/software/template.pnagrabber'
        #self.set_directory(wdir);
        
        
    def measure(self,wdir,visa_addr,robot_addr,temp_file,csv_file,note,is_sim,run_vna):   
        self.set_directory(wdir)
        #mpc must be local because many things are directory based when it is initialized
        print(is_sim)
        mysam = SAMURAI_System(is_simulation=is_sim,vna_visa_address=visa_addr,template_path=temp_file,rx_positioner_address=robot_addr)
        print(mysam.is_simulation)
        mysam.connect_rx_positioner() #connect positioner
        rt = mysam.csv_sweep(wdir,csv_file,run_vna)
        print("Ran in "+str(rt)+" seconds, Results in "+wdir)
        mysam.disconnect_rx_positioner()
        
    def set_directory(self,dir_path):
        self.wdir = dir_path
        os.chdir(dir_path)
        


       
root = tk.Tk()
cdg = SAMURGUI(root)
root.mainloop()
