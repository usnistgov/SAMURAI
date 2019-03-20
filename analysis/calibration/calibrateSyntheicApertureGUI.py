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

import sys
import os

from samurai.analysis.support.snpEditor import s2pEditor as s2p
from samurai.analysis.support.metaFileController import metaFileController as mfc
from samurai.analysis.support.metaFileController import update_wdir
from samurai.analysis.support.PostProcPy import PostProcPy as pppy
#pppy_template = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Software/synthetic_aperture';


#import my tktools
#tktoolsPath = 'Q:/public/Quimby/Students/Alec/Useful_Code/Al_TkTools.py'
#sys.path.append(tktoolsPath)
from samurai.acquisition.support.samurai_tktools import DirPicker
from samurai.acquisition.support.samurai_tktools import FilePicker
from samurai.acquisition.support.samurai_tktools import EntryAndTitle
from samurai.acquisition.support.samurai_tktools import CheckGroup
from samurai.acquisition.support.samurai_tktools import HelpButton


from collections import OrderedDict
import json
import datetime
import os
from shutil import copyfile
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
        self.default_pp_cal_template = r'U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\support\cal_template.post';
        #this default is for s2p_files not w2p calibration (theyre different)
        
        #our check button group
        cb_list = ['Wave Params', 'Convert to S-Params']
        self.check_options = CheckGroup(tkroot,'Options',cb_list)
        self.check_options.pack(side=tk.TOP)
        
        
        
        self.raw_meas_metafile_entry = FilePicker(self.tkroot,'Measurement Metafile',default_val=self.initMetaSearchDir,filetypes=(('MetaFile','*.json'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black");
        self.cal_solution_file_entry = FilePicker(self.tkroot,'Measurement Calibration Solution',default_val=self.initMetaSearchDir,filetypes=(('Calibration Solution File','*.meas'),('Calibration Solution File','*.s4p'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black");
        self.gthru_file_entry = FilePicker(self.tkroot,'Measurement Switch Terms',default_val=self.initMetaSearchDir,filetypes=(('S2P File','*.s2p'),('Switch Terms','*.switch'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black");
        self.output_meas_directory_entry = DirPicker(self.tkroot,"Output Directory",self.default_output_dir,bd=5,highlightbackground="gray",highlightcolor="black",highlightthickness=5);
        self.post_proc_cal_template_entry = FilePicker(self.tkroot,'Post Processor Calibration Template',default_val=self.default_pp_cal_template,filetypes=(('MUF Post Processor Menu','*.post'),),highlightthickness=5,highlightbackground="gray",highlightcolor="black")

        self.raw_meas_metafile_entry.pack()
        self.cal_solution_file_entry.pack()
        self.gthru_file_entry.pack()
        self.output_meas_directory_entry.pack()
        self.post_proc_cal_template_entry.pack()
        
                #help button
        help_text = 'This is a GUI that will calibrate synthetic aperture data taken by the SAMURAI System. \n'
        help_text+= 'This requires a metafile to have been generated in the way used previously in the program (JSON format).\n'
        help_text+= 'In order to calibrate, simply select:\n'
        help_text+= '                    - A metafile tracking all raw measurements\n'
        help_text+= '                    - A solution (.meas or .s4p) file for the calibration\n'
        help_text+= '                    - Switch terms for calibrating (.s2p,.switch) when using S-Parameters\n'
        help_text+= '                    - An output directory to save the calibrated output\n'
        help_text+= '                    - (OPTIONAL FOR ADVANCED USAGE) A template for the post-processor calibration\n\n'
        help_text+= 'Once these have been selected, simply click calibrate to run the calibration and results will be in the output directory\n\n';
        help_text+= 'This script relies on a few common python libraries (Tkinter,numpy,xml.dom.minidom,etc) and a few custom libraries, most of\n'
        help_text+= '  which are found in Q:/public/Quimby/Students/Alec/Useful_Code/'
        self.help_button = HelpButton(tkroot,help_text,button_text='Need Help? Click Me.')
        self.help_button.pack(side=tk.BOTTOM)

        
        
    def calData(self):
        csa = calSynthAp(self.raw_meas_metafile_entry.get(),self.output_meas_directory_entry.get(),
                         self.cal_solution_file_entry.get(),self.post_proc_cal_template_entry.get(),self.gthru_file_entry.get());
      #  wp_flg = self.check_options.get_button_state(0);
        convert_flg = self.check_options.get_button_state(1)
        #print(self.check_options.print_debug());
        #csa.populate_post_proc_and_calibrate(wp_flg,convert_flg);
        csa.populate_post_proc_and_calibrate_s2p(convert_flg)
        print('DONE. Results in '+self.output_meas_directory_entry.get())
        
        
    def move_data_and_update_metafile(self):
        print("Moving Calibrated Results and Updating Metafile")
        csa = calSynthAp(self.raw_meas_metafile_entry.get(),self.output_meas_directory_entry.get(),
                         self.cal_solution_file_entry.get(),self.post_proc_cal_template_entry.get(),self.gthru_file_entry.get())
        
        csa.update_metafile_and_move()
    

class calSynthAp:
    
##load in our metadata file
#with open(metaPath,'r') as jsonFile:
#    jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
    def __init__(self, metaFile,out_dir,in_cal_path,post_proc_template,gthru_file_path):
        self.mfc = mfc(metaFile)
        self.metaFile = metaFile
        
        self.post_proc_template = post_proc_template
        
        self.times = self.mfc.get_timestamp_data()
      
        self.out_dir = out_dir
        #path to our .meas error box file
        self.in_cal_path = in_cal_path
        self.switch_terms_path = gthru_file_path
        #self.dateWdir = os.path.join(self.calWdir,self.dateWdir)
        #self.calOutDir = os.path.join(self.dateWdir,'calibrated_data_'+os.path.split(self.wdir)[1])
        #self.newWdir = os.path.join(self.wdir,self.calOutDir)
  
    #calibrate in post processor and save in output directory
    def populate_post_proc_and_calibrate_s2p(self,convert_to_s2p_flg):
        #ensure our metafile is updated to the current folder
        self.mfc.set_wdir()
        #get our list of values from the old folder both with and without absolute path
        fnames_abs = self.mfc.get_filename_list(True)
        #open our post proc object and rename to our new directory
        self.ppc = pppy(self.post_proc_template)
        out_name = os.path.split(self.post_proc_template)[1]; #get the file name
        #now rename
        self.ppc.rename(os.path.join(self.out_dir,out_name))
        #now set cal path
        self.ppc.setCalPath(self.in_cal_path)
        self.ppc.setSwitchTerms(self.switch_terms_path)
        #and populate the duts
        self.ppc.setDUTFromList(fnames_abs)
        #now check our checkboxes to see what we want to do
        #self.ppc.convert_to_s2p(convert_to_s2p_flg);
        #then write and run
        print("Running Calibration in "+str(self.out_dir))
        self.ppc.write()
        self.ppc.run()
        print("Calibration Complete. Updating MetaFile and Moving Data...")
        #update metafile and move data
        self.update_metafile_and_move()
        
        
    def update_metafile_and_move(self,convert_to_s2p_flg=0,wave_params_flg=0):
        
        self.move_calibrated_results()
        self.mfc.set_calibration_file(self.in_cal_path)
        #now rewrite a new metafile in new folder
        self.mfc.set_wdir(self.out_dir)
        self.mfc.write()

    #This will copy each of the calibrated measurements
    def move_calibrated_results(self,convert_to_s2p_flg=0,wave_params_flg=0):

        #we now assume given path already exists. This is easier to use
        #get our file names. These names will be the same in the calibration folder
        fnames = self.mfc.get_filename_list()
        #our calibration folder name
        cal_folder_name = os.path.split(self.post_proc_template)[1].split('.')[0]
        cal_folder_full = os.path.join(self.out_dir,cal_folder_name+'_post_Results'); #full path to our calibration folder
        #we now we go into the subdirectories and copy the s2p file which is named based on the post processor template
       # if(wave_params_flg):
       #     ftype = '.w2p';
       # else:
       #     ftype = 's2p';
       # if(convert_to_s2p_flg): #if we converted we need to change to s2p and overwrite whatever was there
       #     ftype = '.s2p' 
        
        #snp_name = cal_folder_name+'_0'+ftype;
        fname_out_list = []
        #now lets copy
        for fname in fnames:
            meas_name_full = os.path.split(fname)[-1] #in case the measurements are in some subdirectory
            meas_name = meas_name_full.split('.')[0] #we remove extension here
            meas_ext  = meas_name_full.split('.')[1]
            snp_name =  cal_folder_name+'_0.'+meas_ext
            copy_src = os.path.join(cal_folder_full,meas_name,snp_name)
            meas = meas_name+'.'+meas_ext
            copy_dst = os.path.join(self.out_dir,meas)#now set our copy destination
            #now we actually copy
            copyfile(copy_src,copy_dst)
            #make list of output file names
            fname_out_list.append(meas)
        #now update the metafile entry
        #this assumes that all of the files have been read and written in order
        self.mfc.set_filename(fname_out_list) #set list to metafile
        

       
root = tk.Tk()
cdg = CalSAGui(root)
root.mainloop()




