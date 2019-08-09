# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:11:26 2019

@author: ajw5
"""

from samurai.analysis.support.MUF.MUFModuleController import MUFModuleController
from lxml import etree as ET

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
            None yet!
            Thsee are also passed to MUFModuleController.__init__()
        '''
        super().__init__(menu_path,**kwargs)
        
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
        cal_element = self.controls.find(tag_name)
        if cal_element is None:
            raise Exception('Invalid tag_name')
        num_children = len(cal_element.getchildren())
        #now set the index of the item. We start at 0
        item.attrib['Index'] = str(num_children)
        #now lets add to the element
        cal_element.addnext(item)
        #now lets set the count
        cal_element.attrib['Count'] = str(num_children+1)
        
        
    def _create_calibration_item(self,model_path,meas_type,meas_path,**kwargs):
        '''
        @brief create a calibration item element to add to our xml
        '''
        model_name = os.path.splitext(os.path.split(model_path)[-1])[0]
        meas_name = os.path.splitext(os.path.split(model_path)[-1])[0]
        
        opt = {} #options
        opt['p1'] = 1
        opt['p2'] = 2
        opt['length'] = ''
        opt['length_path'] = ''
        for k,v in kwargs.items():
            opt[k] = v
        
        #check the meas type
        meas_type_alias_dict = {'term':'Termination (S21=S12=0)','recip':'Reciprocal Thru','switch':'Switch terms'}
        meas_type_caps_dict = {'THRU':'Thru','TERMINATION (S21=S12=0)':'Termination (S21=S12=0)',
                               'SWITCH TERMS':'Switch terms','RECIPROCAL THRU':'Reciprocal thru'}
        meas_type = meas_type_alias_dict.get(meas_type,meas_path)
        meas_type = meas_type_caps_dict.get(meas_type.upper(),None)
        if meas_type is None:
            raise Exception("Invalid meas_type")
            
        #now built tthe item
        item = ET.Element('Item',attrib={"Index":"-1","Text":model_name})
        subelem_text = [model_name,model_path,meas_type,opt['length'],opt['length_path'],
                        meas_name,meas_path,opt['p1'],opt['p2']] #list of Text items for subelements
        for i,sub in enumerate(subelem_text):
            ET.SubElement(item,'SubItem',attrib={"Index":str(i),"Text":str(sub)})
        return item
        
    
        
        
        
if __name__=='__main__':
    
    from samurai.analysis.support.MUF.MUFModuleController import MUFModelKit
    
    test_vnauncert_xml = r"./templates/template.vnauncert"
    
    vumc = VNAUncertController(test_vnauncert_xml)
    
    model_kit_path = './templates/WR28.mmk'
    wr28_kit = MUFModelKit(model_kit_path)
    vumc._add_calibration_item('BeforeCalibration',wr28_kit['load'],'term',wr28_kit['offset_short'])
    
    