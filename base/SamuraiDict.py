# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 08:50:09 2019

@author: ajw5
"""
from collections import OrderedDict
import os
import json

class SamuraiDict(OrderedDict):
    '''
    @brief this is a class to inherit from that slightly extends orderedDict
        This will provide read/write from json file capabilities along with
        some other small capabilities not provided by orderedict
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief initialize the class. This will take the same arguments as dict()
        @param[in] *args - arguments to pass to OrderedDict
        @param[in] **kwargs - keyword arguments to pass to OrderedDict
        '''
        super().__init__(*args,**kwargs)
        
    def load(self,fpath,**kwargs):
        '''
        @brief load dictionary data from a json file
        @param[in] fpath - path to file to load
        @param[in/OPT] kwargs - keyword args will be passed to json.load()
        '''
        if not os.path.exists(fpath):
            raise FileNotFoundError("File '{}' not found".format(os.path.abspath(fpath)))
        with open(fpath,'r') as jsonFile:
            self.update(json.load(jsonFile, object_pairs_hook=OrderedDict,**kwargs))
            
    def write(self,fpath,**kwargs):
        '''
        @brief write out dictionary data to a json file
        @param[in] fpath - path to write to 
        @param[in/OPT] kwargs - keyword args will be passed to json.dump()
        @return path that was written to 
        '''
        with open(fpath,'w+') as json_file:
            json.dump(self,json_file,indent=4) 
        return fpath
    
    
if __name__=='__main__':
    myd = SamuraiDict({'test1':'test2'})
    