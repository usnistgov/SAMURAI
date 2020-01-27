# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 08:50:09 2019
@brief this is a set of functions and classes to extend pythons OrderedDict class  
@warning reading a writing of integer keys using JSON is INVALID and WILL NOT WORK  
@author: ajw5
"""
from collections import OrderedDict
import os
import json
import numpy as np
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
        my_kwargs = {}
        my_kwargs['object_hook'] = SamuraiJSONDecoder
        for k,v in kwargs.items():
            my_kwargs[k] = v
        if not os.path.exists(fpath):
            raise FileNotFoundError("File '{}' not found".format(os.path.abspath(fpath)))
        with open(fpath,'r') as jsonFile:
            self.update(json.load(jsonFile,**my_kwargs))
            
    def loads(self,mystr,**kwargs):
        '''
        @brief load dictionary data from a string
        @param[in] mystr - string to load from
        @param[in/OPT] kwargs - keyword args will be passed to json.loads() 
        '''
        my_kwargs = {}
        my_kwargs['object_hook'] = SamuraiJSONDecoder
        for k,v in kwargs.items():
            my_kwargs[k] = v
        self.update(json.loads(mystr,**my_kwargs))
            
    def write(self,fpath,**kwargs):
        '''
        @brief write out dictionary data to a json file  
        @param[in] fpath - path to write to   
        @param[in/OPT] kwargs - keyword args will be passed to json.dump()  
        @return path that was written to   
        '''
        my_kwargs = {}
        my_kwargs['indent'] = 4
        my_kwargs['cls'] = SamuraiJSONEncoder
        for k,v in kwargs.items():
            my_kwargs[k] = v
        with open(fpath,'w+') as json_file:
            json.dump(self,json_file,**my_kwargs) 
        return fpath
    
    dump=write #alias to match json names
    
    def writes(self,**kwargs):
        '''
        @brief dump a dictionary to a json string  
        @param[in/OPT] kwargs - keyword args passed to json.dump  
        @return string of json  
        '''
        my_kwargs = {}
        my_kwargs['indent'] = 4
        my_kwargs['cls'] = SamuraiJSONEncoder
        for k,v in kwargs.items():
            my_kwargs[k] = v
        mystr = json.dumps(self,**my_kwargs)
        return mystr
    
    dumps=writes #alias to match json names
    
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

class SamuraiJSONEncoder(json.JSONEncoder):
    '''
    @brief custom json encoder for specific samurai types  
    '''
    custom_encoding_method = '_encode_json_' #this method should be written to provide a custom encoding
    def default(self,obj):
        if isinstance(obj,np.ndarray): #change any ndarrays to lists
            return obj.tolist()
        if np.iscomplexobj(obj): #then its a complex number
            return complex_number_encoder(obj) #encode complex numbers
        elif hasattr(obj,self.custom_encoding_method): #assume this will then be a class with a custom method
            return class_encoder(obj)
        elif callable(obj): #if its a callable (e.g. a fucntion) try to encode it
            return function_encoder(obj)
        else:
            return super().default(obj)

def SamuraiJSONDecoder(o):
    '''
    @brief allow defining custom decoders in a function  
    @note class must have a default constructor (class_())   
    @note the class must have a _decode_json_ method  
    @note the class must also be imported into globals()  
    @note if the above notes are not met, standard decoding will be done  
    '''
    custom_decoding_method = '_decode_json_'
    first_key_name = list(o.keys())[0] #
    if first_key_name.startswith('__') and first_key_name.endswith('__'): 
        #then assume its a special directive (e.g. class or operation)
        spec_dir = first_key_name.strip('__')
        if spec_dir=='function':
            return function_decoder(o)
        elif spec_dir=='complex_number':
            return complex_number_decoder(o)
        elif spec_dir=='class': #assume its a class
            class_name = spec_dir
            globals_ = globals()
            class_ = globals_.get(class_name)
            obj = class_() #must have a default constructor
            if class_ is not None: #check if its a 
                if hasattr(obj,custom_decoding_method):
                    cust_dec_meth = getattr(obj,custom_decoding_method)
                    return cust_dec_meth(o)
    elif isinstance(o,dict): #if its a dict, make it a samuraiDict
        o = SamuraiDict(o)
    return o

import inspect
from textwrap import dedent
def function_encoder(myfun):
    '''
    @brief encode a funciton into a dictionary  
    @param[in] myfun - function to encode  
    @note this is still limited in functionality by inspect.getsource
    '''
    mydict = OrderedDict({'__function__':dedent(inspect.getsource(myfun))})
    mydict['__name__'] = myfun.__name__
    return mydict

def function_decoder(obj):
    '''
    @brief class to decode a function created by function_encoder  
    @param[in] object from function_encoder  
    '''
    exec(obj['__function__']) #define the function (e.g. def foo(a,b): return a+b)
    return eval(obj['__name__']) #return the function that was defined (e.g. foo)
    
def class_encoder(myclass):
    '''
    @brief encode a class into a dictionary
    @param[in] myclass - class to encode
    @note this assumes the class has an encode and decode method
    '''
    cust_enc_meth = getattr(myclass,'custom_encoding_method')
    class_name = myclass.__class__.__name__ #get the class name
    class_dict = OrderedDict({'__class__':cust_enc_meth()})
    class_dict['__classname__'] = class_name 
    return class_dict

def complex_number_encoder(obj):
    '''
    @brief Encode a complex number to json with the format
        {__complex_number__:{real:[r1,r2,r3,...],imag:[i1,i2,i3,...]}}  
    @param[in] obj - complex object to encode
    @return Complex number dictionary
    '''
    return {'__complex_number__':{'real':np.real(obj),'imag':np.imag(obj)}}

def complex_number_decoder(obj):
    '''
    @brief Decode a complex number from complex_number_encoder
    @param[in] obj - encoded complex number like {__complex_number__:{real:[r1,r2,r3,...],imag:[i1,i2,i3,...]}}
    @return A complex number or array of numbers
    '''
    nd = obj['__complex_number__']
    return np.array(nd['real'])+1j*np.array(nd['imag'])
    

import unittest
class TestSamuraiDict(unittest.TestCase):
    '''@brief unittest class for testing SamuraiDict operation'''
    
    def test_dict_operation(self):
        '''@brief test basic dictionary operations'''
        myd = {'1':'test1','test2':2,'3':{'3':'test3'}}
        mysd = SamuraiDict(myd)
        self.assertEqual(myd['test2'],mysd['test2'])
        self.assertEqual(myd.get('na',None),mysd.get('na',None))
    
    def test_key_list_update(self):
        '''@brief test updating of nested dictionaries from a key list'''
        myd = SamuraiDict({'test1':'test2',3:{'test':{5:'abc'}}})
        myd[[3,'test',5]] = 'xyz'
        self.assertEqual(myd[3]['test'][5],'xyz')
        
    def test_ed_basic(self):
        '''@brief test encode/decode basic data from string'''
        #test basic dictionary
        myd = SamuraiDict({'test1':'test2','3':SamuraiDict({'test':SamuraiDict({'5':'abc'})})})
        mydl = SamuraiDict() #dict to load
        mydl.loads(myd.dumps())
        self.assertEqual(myd,mydl)
        
        
    def test_ed_function(self):
        '''@brief test encode/decode of functions from string'''
        #test the saving and loading of a function
        def foo(a,b):
            c = a*b
            return c+a
        myd = SamuraiDict({'test1':'test2','3':{'test':{'5':foo}}})
        mydl = SamuraiDict() #dict to load
        mydl.loads(myd.dumps())
        self.assertEqual(foo(4,5),mydl['3']['test']['5'](4,5)) #make sure the function was decoded
        
    def test_ed_complex_number(self):
        '''@brief test encode/decode of complex number(s) from string'''
        myd = SamuraiDict({'test1':'test2','3':{'test':{'5':complex(1,0)},'t2':complex(3.2,4.1)}})
        mydl = SamuraiDict()
        mydl.loads(myd.dumps())
        self.assertEqual(1+0j,mydl['3']['test']['5'])
        self.assertEqual(3.2+4.1j,mydl['3']['t2'])
        #and also test lists
        vals_a = np.ones((100,))+np.zeros((100,))
        vals_b = np.random.rand(100)+np.random.rand(100)
        myd = SamuraiDict({'test1':'test2','3':{'test':{'5':vals_a},'t2':vals_b}})
        mydl = SamuraiDict()
        mydl.loads(myd.dumps())
        self.assertTrue(np.all(vals_a==mydl['3']['test']['5']))
        self.assertTrue(np.all(vals_b==mydl['3']['t2']))
    
if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSamuraiDict)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    if True:
        def foo(a,b): 
            return a+b
    
    myd3 = SamuraiDict({1:{'test1':{'myfun':foo}}})
    myd4 = SamuraiDict()
    myd4.loads(myd3.dumps()) #try and load a function
    myd4['1']['test1']['myfun']
    json.loads(myd3.dumps(),object_hook=SamuraiJSONDecoder)
    
    #update_nested_dict(myd,myd2)

    #myd.add_alias('myalias',[3,'test',6])
    #print(myd)
    #myd.write('test/test.json')
    
    
    
    