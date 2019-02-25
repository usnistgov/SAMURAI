# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#import sys
import os
import time
#import threading
#import sched
import datetime
import six
#import json
import subprocess
import xml.etree.ElementTree as et

#pnagrabber_exe_path_default = r'U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Software\SAMURAI_Control\edited_pnagrabber\PNAGrabber\bin\Debug\PNAGrabber.exe'
#default pnagrabber path for windows from pnagrabber installer
pnagrabber_exe_path_default = r'C:\\Program Files (x86)\\NIST\\Uncertainty Framework\\PNAGrabber.exe'

class pnaGrabber:
    def __init__(self,**options):#PNAoutDir='wdir',exePath=PNAGrabberPath):
        self.options = {}
        defaults = {}
        defaults['wdir'] = './'
        defaults['pnagrabber_template_path'] = os.path.join(defaults['wdir'],'template.pnagrabber')
        defaults['pnagrabber_exe_path'] = pnagrabber_exe_path_default
        for key,val in six.iteritems(defaults): #write defaults
            self.options[key] = val
        for key,val in six.iteritems(options): #write user inputs
            self.options[key] = val
        
        try:
            self.etree = et.parse(self.options['pnagrabber_template_path'])
            self.root = self.etree.getroot()
        except IOError:
            print('ERROR: Template path %s does not exist!' %(self.options['pnagrabber_template_path']))
            raise #still quit here
        if not 'pnagrabber_output_path' in self.options: #if not passed in, set default
            self.options['pnagrabber_output_path'] = self.get_meas_list()[0] #os.path.join(defaults['wdir'],'unnamed.s2p');

        

    #run pnagrabber (for single file)
    def run(self,newPath,clean=-1):
        #get file and time
        ts = time.time()
        runCommand = self.options['pnagrabber_exe_path']+" -r "+self.options['pnagrabber_template_path']
        #os.system(runCommand)
        subprocess.call(runCommand)
        te = time.time()
        #now rename the output file
        
        #first ensure filetype is correct
        new_file_split = newPath.split('.')
        old_file_split = self.options['pnagrabber_output_path'].split('.')
        if(len(new_file_split)>1): #if a file ending was there replace it with correct one
            new_file_split[-1] = old_file_split[-1]
            newPath = '.'.join(new_file_split)
        else: #if it wasnt just add the correct ending
            newPath = newPath+'.'+old_file_split[-1]
        
        #first check if exists and change name
        [newPath,_]= cleanFileName(newPath,clean)
        
        os.rename(self.options['pnagrabber_output_path'],newPath)
        #return runtime and new filename if changed
        return te-ts,newPath
    
    #get list of enabled measurements from template path
    def get_meas_list(self):
        #get list of measurements from pnagrabber template menu
        #this returns only enabled elements
        controls = self.root.find('Controls')
        num_text_boxes = 14 #this is hardcoded into the MUF
        meas_list = []
        for i in range(num_text_boxes):
            tb_element = controls.find('TextBox'+str(i+1)) #get our text box xml element
            is_enabled = bool(tb_element.attrib['Enabled'])
            if is_enabled:
                meas_list.append(tb_element.attrib['ControlText'])
        return meas_list
        
        
  
#this class will track and print statistics on measurements running in a loop. Just set the start and stop point
#tot_vals is the total values the loop will iterate throuhg, and print_mod is how often it should print (n%print_mod)
class LoopTimeReport:
    
    def __init__(self,tot_vals,print_mod=1):
        self.tot_vals = tot_vals
        self.print_mod = print_mod
        self.reset()
        
    def reset(self):
        self.approx_time_per_run = 0
        self.time_total = 0
        self.cur_point = 0
        
    def start_point(self):
        self.time_start = time.time()
        
    def end_point(self,custom_time=-1):
        self.time_end = time.time()
        self.time_cur = self.time_end-self.time_start
        self.approx_time_per_run = (self.approx_time_per_run*self.cur_point+(self.time_cur))/(self.cur_point+1)
        self.time_total+=self.time_cur
        if(self.cur_point%self.print_mod==0):
                print(str(self.cur_point+1)+" of "+str(self.tot_vals)+ " completed")
                print("Approximately "+str(self.approx_time_per_run*float(self.tot_vals-(self.cur_point+1))/60.)+" minutes till completion")
                print("Approximate completion at : "+str(datetime.datetime.now()+datetime.timedelta(seconds=self.approx_time_per_run*float(self.tot_vals-(self.cur_point+1)))))
                if(custom_time>0):
                    print("PNAGrabber Time: "+str(custom_time))
        self.cur_point+=1
      

#check to see if the directory exists, if it does increment and do unitl it doesnt
def cleanDirName(dir_name):
    end_num = 0
    dir_name = os.path.abspath(dir_name)
    while(os.path.isdir(dir_name)):
        end_num += 1
        if(end_num>1): #then remove the old number
            dir_name= dir_name.rsplit('_',1)[0]
        dir_name += "_"+str(end_num)
    return end_num,dir_name


#check if file exists and change name if it does
def cleanFileName(fileName,num=-1):
    fout=fileName
    i=0
    if(num==-1):
        while(os.path.isfile(fout)==True):
            i+=1
            #remove number if there was one
            fout = fout.split('/')[-1]
            if(len(fout.split('('))>1):
                fout = fout.split('(')[0]+fout.split(')')[-1]
            fout = fout.split('.')[0]+'('+str(i)+').'+fout.split('.')[1]
            fout = '/'.join(fileName.split('/')[0:-1])+'/'+fout
    elif(num==0):#no need to add thing on
        fout = fileName
    else:
        i=num
        fout = fout.split('/')[-1]
        fout = fout = fout.split('.')[0]+'('+str(i)+').'+fout.split('.')[1]
        fout = '/'.join(fileName.split('/')[0:-1])+'/'+fout
    return fout,i

PNAGrabber = pnaGrabber