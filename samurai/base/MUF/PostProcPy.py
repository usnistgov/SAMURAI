# -*- coding: utf-8 -*-
"""
Created on Wed Sep 05 15:12:24 2018

@author: ajw5
"""

import subprocess
import os

from xml.dom.minidom import parse, parseString

from samurai.base.generic import subprocess_generator
from samurai.base.MUF.MUFModuleController import MUFModuleController,MUFItemList,create_muf_xml_item
from samurai.base.generic import get_name_from_path

file_dir = os.path.realpath(os.path.dirname(__file__))

DEFAULT_POST_PROCESSOR_EXE_PATH = r"C:\Program Files (x86)\NIST\Uncertainty Framework\PostProcessor.exe"

# Templates for different post processor menus (they are all formatted differently)
TEMPLATE_POST_PROCESSOR_ERROR_BOX_COMBINE = os.path.join(file_dir,'templates/post_proc_combine_2port_error_boxes_template.post')

class PostProcPy(MUFModuleController):
    '''
    @brief Class to control the MUF Post Processor
    @param[in] menu_path - path to the menu to load
    @param[in/OPT] kwargs - keyword arguments as follows:
        - exe_path - path to post processor executable (defaults to MUF default install location)
        - | - The rest are passed to MUFModuleController.__init__
    '''
    
    def __init__(self,menu_path=None,exe_path=None,**kwargs):
        '''@brief Constructor'''
        kwargs_out = {} #kwargs to pass to mufmodulecontroller superclass
        kwargs_out['exe_path'] = DEFAULT_POST_PROCESSOR_EXE_PATH
        for k,v in kwargs.items():
            kwargs_out[k] = v
        super().__init__(menu_path,**kwargs_out) # run mmc initialize
        
    def set_cal_path(self,cal_path):
        '''@brief set the erro box file for the post processor'''
        self._controls.find('PostProcessorMechanisms')[0][1].set('Text',cal_path)
        
    setCalPath = set_cal_path
        
    def set_switch_terms(self,gthru_path):
        '''@brief set the switch terms file for the post processor'''
        self._controls.find('PostProcessorMechanisms')[1][1].set('Text',gthru_path)
        
    setSwitchTerms = set_switch_terms
    
    def set_dut_from_list(self,dut_list):
        '''
        @brief Set a list of paths to multiple DUTs for the post processor. This clears all old DUTs
        @param[in] dut_list - list of DUT paths
        @note The MUF drag and drop interface really slows after a few hundred measurements so this becomes necessary
        '''
        dut_node = MUFItemList(self._controls.find('MultipleMeasurementsList'))
        dut_node.clear_items()
        # now lets create our new items
        dut_items = []
        for dut_path in dut_list:
            name = get_name_from_path(dut_path)
            item = create_muf_xml_item(name,[name,dut_path])
            dut_items.append(item)
        dut_node.add_items(dut_items)
        
    setDUTFromList = set_dut_from_list
        
    def convert_to_s2p(self,set_flg):
        '''
        @brief set or remove flag to convert from w2p to s2p. 
        @param[in] set_flg - True to convert or flase to do nothing
        '''
        my_combo_node = self._controls.find('ComboBox3')
        
        if(set_flg): #then we convert to s2p this is option 2
            my_combo_node.set('SelectedIndex','2')
            #probably dont need to set the text but whatever... why not
            my_combo_node.set('ControlText','Convert .wnp files to .snp files')
        else: #dont normalize phase (or do anything)
            my_combo_node.set('SelectedIndex','0')
            #probably dont need to set the text but whatever... why not
            my_combo_node.set('ControlText','Don\'t normalize phase of .wnp fundamentals to zero')
        
    def rename(self,new_menu_path):
        '''@brief For backward compatability'''
        self.menu_path = new_menu_path
        
if __name__=='__main__':
    #test the subprocess generator main
    #the menu to test on
    post_menu_path = r"C:\Users\ajw5\source\repos\MUF\PostProcessor\bin\Debug\test.post"
    myppp = PostProcPy(post_menu_path)
    #myppp.run()
    
    
    
    
    
        
        
        