# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 08:50:09 2019

@author: ajw5
"""
from collections import OrderedDict
import os
import json
from functools import reduce
import operator

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
        self._alias_dict_key = '__aliases__'
        self._alias_dict = None
        super().__init__(*args,**kwargs)
        
    def add_alias(self,alias,key):
        '''
        @brief add an alias to a key in the dictionary. Aliases are always from
            the base level of the dicitionary, but they can be a list of keys
            to work with nested dictionaries.
        @param[in] alias - alias for the key
        @param[in] key - key to make an alias to
        @note the dictionary is written, these aliases will be under __alias__ key
        '''
        #first check if we have our alias dictionary already
        if self._alias_dict is None: #init if it hasnt been
            self[self._alias_dict_key] = {}
            self._alias_dict = self[self._alias_dict_key]
            self.move_to_end(self._alias_dict_key,False)
        val = self.get(key,None) # make sure the value exists
        if val is None:
            raise KeyError("Alias must link to existing key ({} not a key)".format(key))
        self._alias_dict[alias] = key #add key to dictionary
        
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
    
    def set_from_path(self,key_list,value,**kwargs):
        '''
        @brief set a value from a list of dictionary keys
        @param[in] key_list - list of keys to traverse to set the dictionary value
        @param[in] value - value to set at final value
        '''
        #We need to add keys if they dont exist
        cur_dict = self #start at the root of the dict
        for k in key_list[:-1]: #now loop through. if the key doesnt exist make it
            next_dict = cur_dict.get(k,None)
            if next_dict is None: #then make it a dict
                next_dict = {}
                cur_dict[k] = next_dict
            cur_dict = next_dict
        #now we have made up to our last value and thats in cur_dict
        cur_dict[key_list[-1]] = value
            
    def get_from_path(self,key_list,**kwargs):
        '''
        @param[in] value - value to set at final value
        @param[in] key_list - list of keys to traverse to set the dictionary value
        @note solution from https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
        ''' 
        return reduce(operator.getitem,key_list,self)
    
    def get(self,key,default=None):
        '''
        @brief override the default get to allow nested dict keys
        @param[in] key - key to get
        @param[in] default - value to return if key doesnt exist
        @note utilizes __getitem__ to try and access the key
        '''
        try:
            rv = self[key] #use getitem
        except KeyError: #if its an error return our default
            rv = default
        return rv
    
    def __getitem__(self,*args,**kwargs):
        '''
        @brief allow getting item from a list of keys (e.g. dict[[1,2,3]] or dict[1,2,3]) for nested dict
        '''
        item = args[0] #first argument should be item
        if type(item) is list or type(item) is tuple: #if its a list or tuple, get from path
            return self.get_from_path(item)
        else:
            try: #first try to get the value from the dict
                return super().__getitem__(item)
            except KeyError as ke: #otherwise check our aliases
                if self._alias_dict is not None:
                    if item in self._alias_dict.keys(): #if its an alias try and get that
                        new_item = self._alias_dict[item]
                        return self.__getitem__(new_item) #try and get the new item
                    else: #if it isnt a key just raise the error
                        raise ke
                else:
                    raise ke #also raise the error if the alias dict doesnt exist
      
    def __setitem__(self,*args,**kwargs):
        '''
        @brief allow settings items from key list for nested dictionaries
        '''
        item = args[0] #first argument should be item
        value = args[1]
        if type(item) is list or type(item) is tuple: #if its a list or tuple, get from path
            return self.set_from_path(item,value)
        else:
            return super().__setitem__(*args,**kwargs)
        
def update_nested_dict(dict_update,dict_to_add,overwrite_values=False,**kwargs):
    '''
    @brief take two nested dictionaries and merge them. 
        items in dict1 take precedence. will be merged into dict 1
    @param[in] dict_update - dictionary to update
    @param[in] dict_to_add - dictionary to update from
    @param[in/OPT] overwrite_values - do we overwrite dict_update values if they already exist
    '''
    for k,v in dict_to_add.items():
        if k in dict_update.keys(): #if the key exist keep merging
            if type(v) is dict and type(dict_update[k]) is dict:
                update_nested_dict(dict_update[k],v)
            else:
                if overwrite_values:
                    dict_update[k] = v #overwrite the value
        else: #if it doesnt exist, just add it
            dict_update[k] = v #set the value in dict 1
            print(dict_update[k])
            
            
    
if __name__=='__main__':
    myd  = SamuraiDict({'test1':'test2',3:{'test':{5:'abc'}}})
    myd2 = SamuraiDict({3:{'test1':{"test2":54},'test':{6:123}}})
    
    update_nested_dict(myd,myd2)

    #myd.add_alias('myalias',[3,'test',6])
    print(myd)
    myd.write('test/test.json')
    
    
    
    