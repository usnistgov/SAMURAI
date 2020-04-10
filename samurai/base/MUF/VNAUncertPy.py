# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:11:26 2019

@author: ajw5
"""

from lxml import etree as ET
import re
import os

from samurai.analysis.support.MUF.MUFModuleController import MUFModuleController
from samurai.base.SamuraiDict import SamuraiDict

DEFAULT_VNAUNCERT_EXE_PATH = r"C:\Program Files (x86)\NIST\Uncertainty Framework\VNAUncertainty.exe"

#'C:/Users/ajw5/Source/Repos/MUF/VNAUncertainty/bin/Debug/VNAUncertainty.exe'

test_xml = "./cal_before_after.vnauncert"

class VNAUncertController(MUFModuleController):
    '''
    @brief class to control the VNA uncertainty calculator
    '''
    def __init__(self,menu_path,**kwargs):
        '''
        @brief default constructor
        @param[in] menu_path - path to menu to load
        @param[in/OPT] kwargs - keyword args as follows:
            - exe_path - executable path (defaults to MUF install default)
            - - Thsee are also passed to MUFModuleController.__init__()
        '''
        kwargs_out = {}
        kwargs_out['exe_path'] = DEFAULT_VNAUNCERT_EXE_PATH
        for k,v in kwargs.items():
            kwargs_out[k] = v
        super().__init__(menu_path,**kwargs_out)
        
    def set_before_calibration(self,*args,**kwargs):
        '''
        @brief set calibration items from a model kit, and a measurement dictionary
        @note look at self.set_calibration for help
        '''
        self.set_calibration('BeforeCalibration',*args,**kwargs)
        
    def set_calibration(self,tag_name,model_kit,meas_dict,type_dict={},**kwargs):
        '''
        @brief set calibration items from a model kit, and a measurement dictionary
        @param[in] tag_name - controls tag to place the calibration value (e.g. 'BeforeCalibration')
        @param[in] model_kit - MUFModelKit class with the required models and paths
        @param[in] meas_dict - measurement dictionary mapping names (e.g. 'load') to file paths
                    These key names MUST match a name in the MUFModelKit
        @param[in/OPT] type_dict - dictionary with matching keys to meas_dict that has the types of measurements
                    If not specified self._guess_meas_type(key_name) will be run
        @note this will clear all previous calibrations
        '''
        self.clear_calibration_item(tag_name)
        for key,meas_path in meas_dict.items():
            model_path = model_kit['models'].get(key,None)
            if model_path is None:
                raise Exception('{} is not a model key'.format(key))
            meas_type = type_dict.get(key,self._guess_meas_type(key))
            self._add_calibration_item(tag_name,model_path,meas_type,meas_path)
            
    def set_duts(self,dut_list):
        '''
        @brief set duts from a list of elements
        @param[in] dut_list - list of DUT elements (etree._Element type)
        '''
        parent = self.controls.find('DUTMeasurements')
        for d in dut_list:
            self.add_item(parent,d)
        
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
        meas_type_alias_dict = {'term':'Termination (S21=S12=0)','recip':'Reciprocal Thru','switch':'Switch terms'}
        meas_type_caps_dict = {'THRU':'Thru','TERMINATION (S21=S12=0)':'Termination (S21=S12=0)',
                               'SWITCH TERMS':'Switch terms','RECIPROCAL THRU':'Reciprocal thru'}
        meas_type = meas_type_alias_dict.get(meas_type,meas_path)
        meas_type = meas_type_caps_dict.get(meas_type.upper(),None)
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


#%% Class for Calibration Standards Models

class CalibrationModelKit(SamuraiDict):
    '''
    @brief class to store information on a set of MUF models
    @param[in] model_kit_path - path to a written out MUFModelKit (a json path)
    @param[in/OPT] *args,**kwargs passed to OrderedDict
        type - type of calkit. must be specified when model_kit_path is None
    '''
    def __init__(self,model_kit_path,*args,**kwargs):
        '''@brief Constructor'''
        self['type'] = None
        self['models'] = {}
        if model_kit_path is None:
            try:
                self['type'] = kwargs['type']
            except:
                raise KeyError("Please specify 'type' as a keyword argument when creating an empty kit")
        else:
            self.load(model_kit_path)
    
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
    
    from samurai.analysis.support.MUF.MUFModuleController import MUFModelKit
    
    test_vnauncert_xml = r"./templates/template.vnauncert"
    
    vumc = VNAUncertController(test_vnauncert_xml)
    
    model_kit_path = './templates/WR28.mmk'
    wr28_kit = MUFModelKit(model_kit_path)
    
    meas_dict = {
            'load':'./test/load.s2p',
            'offset_short':'./test/offsetShort.s2p',
            'short':'./test/short.s2p',
            'thru':'./test/thru.s2p',
            'gthru':'./test/gthru.s2p'
            }

    vumc.set_before_calibration(wr28_kit,meas_dict)   
    vumc.set_duts()
    
    vumc.write('./templates/test.vnauncert')
    
    # Model kit
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
    mmk.add_model('gthru',wr28_thru_model)
    op = os.path.join(r'C:\SAMURAI\git\samurai\analysis\support\MUF\templates','WR28.mmk')
    mmk.write(op)
    
    