# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:11:26 2019

@author: ajw5
"""

from lxml import etree as ET
import re
import os

from samurai.base.MUF.MUFModuleController import MUFModuleController, MUFItemList
from samurai.base.SamuraiDict import SamuraiDict

DEFAULT_VNAUNCERT_EXE_PATH = r"C:\Program Files (x86)\NIST\Uncertainty Framework\VNAUncertainty.exe"

wdir = os.path.realpath(os.path.dirname(__file__))

MENU_TEMPLATE_PATH = os.path.join(wdir,'./templates/template.vnauncert')
MENU_TEMPLATE_PATH_ONE_PORT = os.path.join(wdir,'./templates/template_one_port.vnauncert')

#'C:/Users/ajw5/Source/Repos/MUF/VNAUncertainty/bin/Debug/VNAUncertainty.exe'

test_xml = "./cal_before_after.vnauncert"

class VNAUncertController(MUFModuleController):
    '''
    @brief class to control the VNA uncertainty calculator
    '''
    meas_type_alias_dict = {'term':'Termination (S21=S12=0)','recip':'Reciprocal Thru','switch':'Switch terms'}
    meas_type_caps_dict  = {'THRU':'Thru','TERMINATION (S21=S12=0)':'Termination (S21=S12=0)',
                            'SWITCH TERMS':'Switch terms','RECIPROCAL THRU':'Reciprocal thru'}
    meas_type_one_port_alias_dict = {'Termination (S21=S12=0)':'Termination on port 1'} #aliases for a 1 port SOL types
    
    def __init__(self,menu_path,**kwargs):
        '''
        @brief default constructor
        @param[in] menu_path - path to menu to load. If None load a blank template
        @param[in/OPT] kwargs - keyword args as follows:
            - exe_path - executable path (defaults to MUF install default)
            - - Thsee are also passed to MUFModuleController.__init__()
        '''
        kwargs_out = {}
        kwargs_out['exe_path'] = DEFAULT_VNAUNCERT_EXE_PATH
        for k,v in kwargs.items():
            kwargs_out[k] = v
        if menu_path is None: #load the empty template
            menu_path = MENU_TEMPLATE_PATH
        super().__init__(menu_path,**kwargs_out)
        #now set Item lists to correct value
        self.controls
        
    def set_before_calibration(self,*args,**kwargs):
        '''
        @brief set calibration items from a model kit, and a measurement dictionary
        @note look at self.set_calibration for help
        '''
        self.set_calibration('BeforeCalibration',*args,**kwargs)
        
    def set_calibration(self,tag_name,model_kit,meas_dict,type_dict={},**kwargs):
        '''
        @brief set calibration items from a model kit, and a measurement dictionary
        @note this will clear all previous calibrations
        @param[in] tag_name - controls tag to place the calibration value (e.g. 'BeforeCalibration')
        @param[in] model_kit - MUFModelKit class with the required models and paths
        @param[in] meas_dict - measurement dictionary mapping names (e.g. 'load') to file paths
                    These key names MUST match a name in the MUFModelKit
        @param[in/OPT] type_dict - dictionary with matching keys to meas_dict that has the types of measurements
                    If not specified self._guess_meas_type(key_name) will be run
        @param[in/OPT] kwargs - keyword arguments as follows:
            - verify - Verify that the model and measurement paths exist (default true)
        '''
        options = {'verify':True}
        options.update(kwargs) #get kwargs
        self.clear_calibration_item(tag_name)
        for key,meas_path in meas_dict.items():
            model_path = model_kit['models'].get(key,None)
            if model_path is None:
                raise Exception('{} is not a model key'.format(key))
            if options['verify']:  #check the paths exist
                if not os.path.exists(model_path): raise Exception("Model Path Doesn't Exist {}".format(model_path))
                if not os.path.exists(meas_path):  raise Exception("Measurement Path Doesn't Exist {}".format(meas_path))
            meas_type = type_dict.get(key,self._guess_meas_type(key))
            self._add_calibration_item(tag_name,model_path,meas_type,meas_path)
            
    def set_duts(self,dut_list,**kwargs):
        '''
        @brief set duts from a list of strings. This assumes the calibration standards have already been set.
        @param[in] dut_list - list of DUT paths str
        @param[in/OPT] kwargs - keyword arguments as follows:
            - verify - Verify that the model and measurement paths exist (default true)
        '''
        options = {'verify':True}
        options.update(kwargs)
        parent = MUFItemList(self.controls.find('DUTMeasurements'))
        for dut in dut_list:
            if isinstance(dut,str): #if its a string create an item, otherwise expect an item
                dut = self._create_dut_item(dut)
            if not isinstance(dut,ET._Element):
                raise Exception("DUT is not a string of XML Element, it's a {}".format(type(dut)))
            if options['verify']: #check the paths exist
                if not os.path.exists(dut[1].get('Text')): raise Exception("DUT Path Doesn't Exist {}".format(dut[1].get('Text')))
            parent.add_item(dut)
        
    def clear_calibration_item(self,tag_name):
        '''
        @brief clear all subelements from a provided tag 
        @param[in] tag_name - controls tag to clear (e.g 'BeforeCalibration')
        '''
        for child in list(self.controls.find(tag_name)):
            self.controls.find(tag_name).remove(child)
        
    def _add_calibration_item(self,tag_name,model_path,meas_type,meas_path,**kwargs):
        '''
        @brief add a calibration item to a provided calibration tag (e.g. BeforeCalibration)
        @param[in] tag_name - controls tag to place the calibration value (e.g. 'BeforeCalibration')
        @param[in] model_path - path to model
        @param[in] meas_type - type of measurement (e.g. term,recip,thru,switch terms)
        @param[in] meas_path - path to measurement
        '''
        #first generate the calibration item
        item = self._create_calibration_item(model_path,meas_type,meas_path,**kwargs)
        #now add to the tag
        elem = self.controls.find(tag_name)
        if elem is None:
            raise Exception('Invalid tag_name')
        self.add_item(elem,item)
        
    def _create_calibration_item(self,model_path,meas_type,meas_path,**kwargs):
        '''
        @brief create a calibration item element to add to our xml
        '''
        model_name = self._get_name_from_path(model_path)
        meas_name = self._get_name_from_path(meas_path)
        
        opt = {} #options
        opt['p1'] = 1
        opt['p2'] = 2
        opt['length'] = ''
        opt['length_path'] = ''
        for k,v in kwargs.items():
            opt[k] = v    
        #get absolute paths
        meas_path = os.path.abspath(meas_path)
        model_path = os.path.abspath(model_path)
        #check the meas type
        meas_type = self.meas_type_alias_dict.get(meas_type,meas_path)
        meas_type = self.meas_type_caps_dict.get(meas_type.upper(),None)
        #convert to 1 port if thats what we are using
        if self.is_1_port_calibration():
            meas_type = self.meas_type_one_port_alias_dict.get(meas_type,meas_type)
        if meas_type is None:
            raise Exception("Invalid meas_type")
        #now built tthe item
        subelem_text = [model_name,model_path,meas_type,opt['length'],opt['length_path'],
                        meas_name,meas_path,opt['p1'],opt['p2']] #list of Text items for subelements
        item = self.create_item(model_name,subelem_text)
        return item
    
    def _create_dut_item(self,dut_path):
        '''
        @brief create a dut ite element to add to the xml
        '''
        dut_path = os.path.abspath(dut_path)
        dut_name = self._get_name_from_path(dut_path)
        sub_path = [dut_name,dut_path]
        item = self.create_item(dut_name,sub_path)
        return item
        
    
    def _guess_meas_type(self,key_name):
        '''
        @brief try and guess the type of measurement from the keys in the dictionaries
        @param[in] key_name - name of the key used to guess
        '''
        if re.findall('LOAD|SHORT|OFFSET_*SHORT|OPEN',key_name.upper()):
            return 'term'
        if re.findall('GTHRU',key_name.upper()):
            return 'switch'
        if re.findall('THRU',key_name.upper()):
            return 'recip'#default to reciprical thru
        
    def is_1_port_calibration(self):
        '''@brief Check if we are running a 1 port SOL algorithm'''
        return self.controls.find('CalibrationEngine').get('SelectedIndex') == '3'


#%% Class for Calibration Standards Models

class CalibrationModelKit(SamuraiDict):
    '''
    @brief class to store information on a set of MUF models
    @param[in] model_kit_path - path to a written out MUFModelKit (a json path).
        If None, create a blank calibration model kit
    @param[in/OPT] *args,**kwargs passed to OrderedDict
        type - type of calkit should be specified for new calibration kits
    '''
    def __init__(self,model_kit_path=None,*args,**kwargs):
        '''@brief Constructor'''
        super().__init__(*args,**kwargs)
        self['type'] = None
        self['models'] = {}
        if model_kit_path is not None:
            self.load(model_kit_path)
    
    def add_model(self,name,path):
        '''
        @brief add a model to the model kit. 
        @param[in] name - name of the model. also the dict key to retrieve
        @param[in] path - path to the model
        '''
        self['models'].update({name:path})
        
    def __getitem__(self,item):
        '''@brief Also check the model dictionary'''
        try: return super().__getitem__(item) #try to get the item
        except KeyError as e: #otherwise try the model kit
            try: return super().__getitem__('models')[item]
            except KeyError: raise e

    def __setitem__(self,item,val):
        '''@brief Set the data in the model dictionary first'''
        try: models = super().__getitem__('models')
        except KeyError: models = []
        if item in models: models[item] = val #set the model if its there
        else: return super().__setitem__(item,val)
        
        
if __name__=='__main__':
    
    test_vnauncert_xml = r"./templates/template.vnauncert"
    
    vumc = VNAUncertController(test_vnauncert_xml)
    
    model_kit_path = './templates/WR28.cmk'
    wr28_kit = CalibrationModelKit(model_kit_path)
    cmk = wr28_kit
    
    meas_dict = {
            'load':'./test/load.s2p',
            'offset_short':'./test/offsetShort.s2p',
            'short':'./test/short.s2p',
            'thru':'./test/thru.s2p',
            'gthru':'./test/gthru.s2p'
            }

    vumc.set_before_calibration(wr28_kit,meas_dict)   
    vumc.set_duts([])
    
    vumc.write('./test/test.vnauncert')
    
    # Model kit
    #create model path json file for WR28
    wr28_load_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Load.model"
    wr28_short_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Short.model"
    wr28_offsetShort_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_OffsetShort.cascade"
    wr28_offsetThru_model  = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_ShimThru.model"
    wr28_thru_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_IdentityThru.model"
    
    cmk = CalibrationModelKit(type='WR28')
    cmk.add_model('load',wr28_load_model)
    cmk.add_model('short',wr28_short_model)
    cmk.add_model('offset_short',wr28_offsetShort_model)
    cmk.add_model('offset_thru',wr28_offsetThru_model)
    cmk.add_model('thru',wr28_thru_model)
    cmk.add_model('gthru',wr28_thru_model)
    op = os.path.join(r'./templates','WR28.cmk')
    cmk.write(op)
    
    