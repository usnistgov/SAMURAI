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
import os

from samurai.analysis.calibration.CalibrateSamurai import CalibrateSamurai

#tk tools
from samurai.acquisition.support.samurai_tktools import DirPicker
from samurai.acquisition.support.samurai_tktools import FilePicker
from samurai.acquisition.support.samurai_tktools import EntryAndTitle
from samurai.acquisition.support.samurai_tktools import CheckGroup
from samurai.acquisition.support.samurai_tktools import HelpButton

try:
    import Tkinter as tk
    import tkFileDialog
except:
    import tkinter as tk
    import tkinter.filedialog as tkFileDialog

#this will create a tk gui that will calibrate based on a given solution.meas file

class CalSAGui:
    def __init__(self, tkroot):
       # self.cal
        self.tkroot = tkroot
        self.tkroot.title("SAMURAI Synthetic Aperture Calibration Tool")
        
        self.runButton = tk.Button(tkroot,text='Calibrate',command=self.calData)
        self.runButton.pack(side=tk.TOP)
        
        self.moveButton = tk.Button(tkroot,text='Move Calibrated Data and Update Metafile',command=self.move_data_and_update_metafile)
        self.moveButton.pack(side=tk.TOP)

#        self.setupOptions = tk.LabelFrame(self.tkroot,text='Setup');
#        self.setupOptions.pack(side= tk.LEFT)
        
        initMetaPath = r'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Synthetic_Aperture/'
        self.wdir = initMetaPath
        self.initMetaSearchDir = r'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Synthetic_Aperture/'
        
        self.default_output_dir = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Synthetic_Aperture/calibrated'
        #template paths
        
        #our check button group
        #cb_list = ['Wave Params', 'Convert to S-Params']
        #self.check_options = CheckGroup(tkroot,'Options',cb_list)
        #self.check_options.pack(side=tk.TOP)
        
        
        
        self.raw_meas_metafile_entry = FilePicker(self.tkroot,'Measurement Metafile',default_val=self.initMetaSearchDir,filetypes=(('MetaFile','*.json'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black")
        self.cal_solution_file_entry = FilePicker(self.tkroot,'Measurement Calibration Solution',default_val=self.initMetaSearchDir,filetypes=(('Calibration Solution File','*.meas'),('Calibration Solution File','*.s4p'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black")
        self.gthru_file_entry = FilePicker(self.tkroot,'Measurement Switch Terms',default_val=self.initMetaSearchDir,filetypes=(('S2P File','*.s2p'),('Switch Terms','*.switch'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black")
        self.output_meas_directory_entry = DirPicker(self.tkroot,"Output Directory",self.default_output_dir,bd=5,highlightbackground="gray",highlightcolor="black",highlightthickness=5)
        
        self.raw_meas_metafile_entry.pack()
        self.cal_solution_file_entry.pack()
        self.gthru_file_entry.pack()
        self.output_meas_directory_entry.pack()
        
                #help button
        help_text = 'This is a GUI that will calibrate synthetic aperture data taken by the SAMURAI System. \n'
        help_text+= 'This requires a metafile to have been generated in the way used previously in the program (JSON format).\n'
        help_text+= 'In order to calibrate, simply select:\n'
        help_text+= '                    - A metafile tracking all raw measurements\n'
        help_text+= '                    - A solution (.meas or .s4p) file for the calibration\n'
        help_text+= '                    - Switch terms for calibrating (.s2p,.switch)(S-Parameters Only)\n'
        help_text+= '                    - An output directory to save the calibrated output\n'
        help_text+= 'Once these have been selected, simply click calibrate to run the calibration and results will be in the output directory\n\n'
        help_text+= 'This script relies on a few common python libraries (Tkinter,numpy,xml.dom.minidom,etc) and a few custom libraries, most of\n'
        help_text+= '  which are found in this git repo'
        self.help_button = HelpButton(tkroot,help_text,button_text='Need Help? Click Me.')
        self.help_button.pack(side=tk.BOTTOM)

        
        
    def calData(self):
        #create our calibration class
        csa = CalibrateSamurai(self.raw_meas_metafile_entry.get(),self.output_meas_directory_entry.get(),
                         self.cal_solution_file_entry.get(),self.gthru_file_entry.get())
        #convert_flg = self.check_options.get_button_state(1)
        csa.populate_post_proc_and_calibrate()
        print('DONE. Results in '+self.output_meas_directory_entry.get())
        
        
    def move_data_and_update_metafile(self):
        print("Moving Calibrated Results and Updating Metafile")
        csa = CalibrateSamurai(self.raw_meas_metafile_entry.get(),self.output_meas_directory_entry.get(),
                         self.cal_solution_file_entry.get(),self.gthru_file_entry.get())
        csa.update_metafile_and_move()
    
  

if __name__=='__main__':     
    root = tk.Tk()
    cdg = CalSAGui(root)
    root.mainloop()




