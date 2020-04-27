# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:02:45 2019

@author: ajw5
"""

from lxml import etree as ET

class SamuraiXML(ET._ElementTree):
    '''
    @brief class to implement some default lxml etree operations   
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief initialize the class. All arguments passed to super().__init__()  
        '''
        super().__init__(*args,**kwargs)
        
    def load(self,fpath):
        '''
        @brief load a menu  
        @param[in] fpath - path to xml file to load  
        '''
        parser = ET.XMLParser(remove_blank_text=True)
        self.parse(fpath,parser)
    
    def write(self,fpath,*args,**kwargs):
        '''
        @brief write out the menu  
        @param[in] fpath - path to write to  
        @param[in/OPT] *args,**kwargs - args to pass to ET._ElementTree.write().  
        '''
        #defaults
        kwargs_out = {}
        kwargs_out['xml_declaration'] = True
        kwargs_out['pretty_print'] = True
        for k,v in kwargs.items():
            kwargs_out[k] = v
        super().write(fpath,*args,**kwargs_out)
        return fpath
        
    def tostring(self,*args,**kwargs):
        '''
        @brief print to string  
        @param[in] *args,**kwargs - all passed to ET.tostring() method  
        '''
        #defaults
        kwargs_out = {}
        kwargs_out['xml_declaration'] = True
        kwargs_out['pretty_print'] = True
        for k,v in kwargs.items():
            kwargs_out[k] = v
        return ET.tostring(self,*args,**kwargs_out)
    
    def __str__(self):
        return self.tostring().decode()
    
class SamuraiXMLElement(ET.ElementBase):
    '''
    @brief a samurai element in an elementTree  
    '''
    def tostring(self,*args,**kwargs):
        '''
        @brief print to string  
        @param[in] *args,**kwargs - all passed to ET.tostring() method  
        '''
        #defaults
        kwargs_out = {}
        kwargs_out['pretty_print'] = True
        for k,v in kwargs.items():
            kwargs_out[k] = v
        return ET.tostring(self,*args,**kwargs_out)
    
    def __str__(self):
        return self.tostring().decode()
        
        