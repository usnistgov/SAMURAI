# -*- coding: utf-8 -*-
"""
Created on Wed Sep 05 15:12:24 2018

@author: ajw5
"""

import subprocess
import os

from xml.dom.minidom import parse, parseString

default_exe_path = 'C:/Users/ajw5/Source/Repos/MUF/PostProcessor/bin/Debug/PostProcessor.exe'

class PostProcPy:
    
    def __init__(self,menu_path=None,exe_path=None):
        self.written=0
        self.uncert_menu = menu_path
        if menu_path is not None:
            self.load(menu_path)
        if exe_path is None:
            #print("Default Executable Path being used")
            self.exe_path = default_exe_path #default path 
            
    #load in our menu as dom file and some things from it       
    def load(self,menuPath):
        self.written=0
        self.menu_path = menuPath
        self.dom = parse(menuPath)
        self.menuLoaded=1
        #get the calibration file name node from post processor
        #get the before cal values that are items
        self.PostProcMech = self.dom.getElementsByTagName('PostProcessorMechanisms')[0]
        #get the DUTS
        self.dutNode = self.dom.getElementsByTagName('MultipleMeasurementsList')[0]
        self.duts = self.dutNode.getElementsByTagName('Item')
        
    #set the .meas (or .s4p) error box file in the post processor
    def setCalPath(self,calPath):
        self.PostProcMech.getElementsByTagName('SubItem')[1].setAttribute('Text',calPath)
        
    def setSwitchTerms(self,gthru_path):
        self.PostProcMech.getElementsByTagName('SubItem')[4].setAttribute('Text',gthru_path); #only for s-param menu (wave params have dirfferent menu)
    
    #pass in a list of absolute (or relative i guess) paths to be set in the XML
    #this makes populating the XML a lot more generic and easier
    #the drag and drop interface tends to break when populating with more than a 
    #few hundred measurements
    def setDUTFromList(self,dutList):
        self.written =0
        pathIdx = 1
        nameIdx = 0
        #assume we have 1 DUT and clear the rest out
        #we need 0 and 1 of child nodes because dom likes to load in
        #blank text node here for some reason
        tempNodeList = self.dutNode.childNodes[0:2]
        self.dutNode.childNodes = []; #text node and meas node
        for dutPath in dutList:
            #get our name from the path
            name = os.path.split(dutPath)[1]
            name = name.split('.')[0]
            #assume there is already at least 1 DUT
            #copy text node
            textNode = tempNodeList[0].cloneNode(True)
            self.dutNode.appendChild(textNode)
            #now write our new node
            newNode = tempNodeList[1].cloneNode(True)
            subitems = newNode.getElementsByTagName('SubItem')
            subitems[pathIdx].setAttribute('Text',dutPath)
            subitems[nameIdx].setAttribute('Text',name)
            self.dutNode.appendChild(newNode)
            
    #change what name it will be written to
    #change the value of self.menu_path
    #call this before write to change name of write path
    def rename(self,newPath):
        self.written=0
        self.menu_path = newPath
       
    #write out the current menu xml
    #if no name is provided it will overwrite the original loaded file
    #or at least whatever is in self.menu_path
    #this could have been changed if rename was called
    def write(self,writeName='na'):
        self.written=1
        #check if we want a different name otherwise write to stored name
        if(writeName=='na'):
            writeName=self.menu_path
        with open(writeName,'w+') as fp:
            self.dom.writexml(fp)
            
    def run(self,text_function=print,tf_args_tuple=(),tf_kwargs_dict={}):
        '''
        @brief run our postprocessor
        @param[in/OPT] text_function - function that the output from the post 
            processor will be passed to (in iterated format, default is print())
            First argument must be expecting a string
        @param[in/OPT] tf_args_tuple - tuple of arguments to pass to text_function
        @param[in/OPT] tf_kwargs_dict - dictionary of kwargs to pass to text_function
        '''
        if(self.menuLoaded!=1):
            print("ERROR: No Menu Loaded")
            return
        else:
            if(self.written==0):
                self.write()
        command = self.exe_path+' -r '+self.menu_path
        exe_generator = subprocess_generator(command)
        for out_line in exe_generator:
            text_function(out_line,*tf_args_tuple,**tf_kwargs_dict)        
        
    #set or remove flag in xml to convert from w2p to s2p    
    #set_flg should be true to convert to s2p or false to not do anything
    #would reccommend using false typically if s parameters are in use
    #this will only work if menu is already set up for calibration correction
    def convert_to_s2p(self,set_flg):
        my_combo_node = self.dom.getElementsByTagName('ComboBox3').item(0)
        
        if(set_flg): #then we convert to s2p this is option 2
            my_combo_node.setAttribute('SelectedIndex','2')
            #probably dont need to set the text but whatever... why not
            my_combo_node.setAttribute('ControlText','Convert .wnp files to .snp files')
        else: #dont normalize phase (or do anything)
            my_combo_node.setAttribute('SelectedIndex','0')
            #probably dont need to set the text but whatever... why not
            my_combo_node.setAttribute('ControlText','Don\'t normalize phase of .wnp fundamentals to zero')
        
def subprocess_generator(cmd):
    '''
    @brief get a generator to get the output from post processor
     From https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    '''
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        stdout_line = stdout_line.strip() #remove trailing whitespaces and newlines
        if stdout_line=='':
            continue #dont do anything
        else:
            yield stdout_line #otherwise this value we want
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd) 
        
        
if __name__=='__main__':
    #test the subprocess generator main
    #the menu to test on
    post_menu_path = r"C:\Users\ajw5\source\repos\MUF\PostProcessor\bin\Debug\test.post"
    myppp = PostProcPy(post_menu_path)
    myppp.run()
    
    
    
    
    
        
        
        