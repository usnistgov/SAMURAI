# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:12:48 2019

@author: ajw5
"""

from lxml import etree as ET
import json

test_vnauncert_xml = r"./templates/template.vnauncert"
test_postproc_xml = r"../../calibration/templates/cal_template.post"

class MUFModuleController(ET._ElementTree):
    '''
    @brief base class for MUF module controllers
    '''
    def __init__(self,menu_path,**kwargs):
        '''
        @brief default constructor
        @param[in] menu_path - path to menu to load
        @param[in/OPT] kwargs - keyword args as follows:
            None yet!
        '''
        super().__init__()
        if menu_path is not None:
            self.load(menu_path)
        else:
            raise Exception('No menu path provided') #implement default menu here
    
    def load(self,menu_path):
        '''
        @brief load a menu
        @param[in] menu_path - path to the menu to laod
        '''
        self.parse(menu_path)
    
    def write(self,out_path,*args,**kwargs):
        '''
        @brief write out the menu
        @param[in] out_path - path to write to
        @param[in/OPT] *args,**kwargs - args to pass to ET._ElementTree.write()
        '''
        super().write(out_path,*args,**kwargs)
    
    @property
    def controls(self):
        '''
        @brief getter for MUF list of controls child elements
        '''
        return self.find('Controls')
    
    @property
    def option_items_checkbox(self):
        '''
        @brief get list menu items from MenuStripItems
        '''
        return self.find('MenuStripItems')
        
    
    @property
    def option_items_textbox(self):
        '''
        @brief get list menu items from MenuStripTextBoxes
        '''
        return self.find('MenuStripTextBoxes')
    
    @property
    def option_items_combobox(self):
        '''
        @brief get list menu items from MenuStripItems
        '''
        return self.find('MenuStripComboBoxes')


from collections import OrderedDict

class MUFModelKit(OrderedDict):
    '''
    @brief class to store information on a set of MUF models
    '''
    def __init__(self,model_kit_path,*args,**kwargs):
        '''
        @brief constructor
        @param[in] model_kit_path - path to a written out MUFModelKit (a json path)
        @param[in/OPT] *args,**kwargs passed to OrderedDict
            type - type of calkit. must be specified when model_kit_path is None
        '''
        self['type'] = None
        self['models'] = {}
        if model_kit_path is None:
            try:
                self['type'] = kwargs['type']
            except:
                raise KeyError("Please specify 'type' as a keyword argument when creating an empty kit")
        else:
            self.load_kit(model_kit_path)
            
    def load_kit(self,model_kit_path):
        '''
        @brief load a kit from a file
        '''
        with open(model_kit_path,'r') as jp:
            jdata = json.load(jp, object_pairs_hook=OrderedDict)
        self.update(jdata) #update from the loaded values
        
    def write(self,out_path):
        '''
        @brief write the kit to a file
        @param[in] out_path - path to write to
        '''
        with open(out_path,'w+') as op:
            json.dump(self,op,indent=4)
    
    def add_model(self,name,path):
        '''
        @brief add a model to the model kit. 
        @param[in] name - name of the model. also the dict key to retrieve
        @param[in] path - path to the model
        '''
        self['models'].update({name:path})
        
    def get_model(self,name):
        '''
        @brief get a model from our kit
        '''
        return self['models'][name]
        
    def __getitem__(self,item):
        '''
        @brief also check the model dictionary
        '''
        try:
            return super().__getitem__(item)
        except KeyError as e:
            try:
                return self.get_model(item)
            except KeyError:
                raise e
        
            
            
            
if __name__=='__main__':
    
    import os
    
    vumc = MUFModuleController(test_vnauncert_xml)
    vumc.option_items_checkbox
    vumc.option_items_textbox
    ppmc = MUFModuleController(test_postproc_xml)
    ppmc.option_items_checkbox
    ppmc.option_items_textbox
    
    #create model path json file for WR28
    wr28_load_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Load.model"
    wr28_short_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Short.model"
    wr28_offsetShort_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_OffsetShort.cascade"
    wr28_offsetThru_model  = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_ShimThru.model"
    wr28_thru_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_IdentityThru.model"
    
    mmk = MUFModelKit(None,type='WR28')
    mmk.add_model('load',wr28_load_model)
    mmk.add_model('short',wr28_short_model)
    mmk.add_model('offset_short',wr28_offsetShort_model)
    mmk.add_model('offset_thru',wr28_offsetThru_model)
    mmk.add_model('thru',wr28_thru_model)
    op = os.path.join(r'C:\SAMURAI\git\samurai\analysis\support\MUF\templates','WR28.mmk')
    mmk.write(op)
    
    
    
    

            