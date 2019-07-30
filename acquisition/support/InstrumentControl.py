# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 10:31:36 2019

@author: ajw5
"""


import re
from collections import OrderedDict
import json

class Instrument(OrderedDict):
    '''
    @brief class for instrument control abstraction
    '''
    def __init__(self,command_dict_path):
        '''
        @brief constructor
        @param[in] command_dict -json file of all the commands if none don't load
        '''    
        #abstraction for any type of connection (e.g. visa object)
        # to use default read/write/query should have a read/write/query method
        self.connection = None
        self.load_command_dict(command_dict_path)

    def load_command_dict(self,command_dict_path):
        '''
        @brief load a command dictionary from a json file path
        @param[in] command_dict_path - path to the json file
        '''
        self['command_dictionary_path'] = command_dict_path #save for writing out
        self.command_dict = InstrumentCommandDict(command_dict_path)
          
    def connect(self):
        '''
        @brief template for instrumnet connection. calls self.connection.connect()
        '''
        self.connection.connect()
        
    def disconnect(self):
        '''
        @brief template for instrument disconnect. calls self.connection.disconnect()
        '''
        self.connection.disconnect()
            
    def read(self):
        '''
        @brief template for an instrument read. calls self.connection.read()
        '''
        rv = self.connection.read()
        rv = self.cast_return_value(rv)
        return rv
    
    def write(self,msg):
        '''
        @brief template for instrument write. calls self.connection.write()
        '''
        self.connection.write(msg)
    
    def query(self,msg):
        '''
        @brief template for a instrument query. calls self.connection.query()
        '''
        rv = self.connection.query(msg)
        rv = self.cast_return_value(rv)
        return rv
    
    def cast_return_value(value_str):
        '''
        @brief try and cast a return value. return float or string depending
            on what works.
        @param[in] value_str - value string to cast
        '''
        try:
            rv = float(value_str)
            return rv
        except ValueError:
            return value_str.strip() #remove trailing whitespace
                
class SCPIInstrument(Instrument):
    '''
    @brief class for scpi instrument control
    '''
    def __init__(self,command_dict_path):
        '''
        @brief constructor
        @param[in] command_dict -json file of all the commands
        '''
        super().__init__(None)
    
    #override from superclass
    def load_command_dict(self,command_dict_path):
        '''
        @brief load a command dictionary from a json file path
        @param[in] command_dict_path - path to the json file
        '''
        self['command_dictionary_path'] = command_dict_path #save for writing out
        self.command_dict = SCPICommandDict(command_dict_path)
    

class InstrumentCommandDict(OrderedDict):
    '''
    @brief class to store instrument commands
    '''
    def __init__(self,load_path=None):
        '''
        @brief constructor
        @param[in/OPT] load_path - path to load from json file
        '''
        super().__init__()
        self['aliases'] = {} #aliases for commands
        self['commands'] = {}
        if load_path is not None:
            self.load(load_path)
        
    def add_command(self,instrument_command,alias=None):
        '''
        @brief add a command to the dictionary. default to key,val pairs
        @param[in] instrument_command - InstrumentCommand Class
        @param[in] alias - alias to add to this command
        '''
        com_name = self._get_default_command_name(instrument_command)
        self.commands.update({com_name:instrument_command})
        #if an alias is provided
        if alias is not None:
            self.add_alias(com_name,alias)
            
    def add_alias(self,command_name,alias):
        '''
        @brief add an alias to a command
        '''
        self.aliases.update({alias:command_name})
        
    def _get_default_command_name(self,instrument_command):
        '''
        @brief generate a default command name. This is going to be
            by default '' passed to all arguments and then stripped of whitespace
        @param[in] instrument_command - InstrumentCommandClass to get default name
        '''
        default_format = ''
        format_args = tuple([default_format]*instrument_command.num_args)
        #we call get_command_template so we dont ignore anything 
        return instrument_command.get_command_template().format(*format_args).strip()
        
        
    def get(self,key,*args):
        '''
        @brief get a command from a key or an alias. This syntax is the same as dict.get()
        @param[in] key - key to get the command of
        @param[in/OPT] default - adefault argument can also be passed in if the key is not found
        @note this also allows nested aliases (e.g. alias1->alias2->command)
        @return InstrumentCommand class of the command
        '''
        #see if the value is an alias
        if key in self.aliases.keys():
            return self.get(self.aliases[key])
        elif key in self.commands.keys(): #othweise its a command (hopefully)
            return self.commands[key]
        else: #otherwise lets pass it to OrderedDict get() method
            return super().get(key,*args)
            
    
    def find_command(self,search_str,case_sensitive=False):
        '''
        @brief search our command dictionary for values values that contain
            search_str. this just looks through the default keys
        @param[in] search_str - substring or regex expression to find 
        @param[in/OPT] case_sensitive - is the search case sensitive
        @return list of commands with the substring,list of aliases with substring
        '''
        if not case_sensitive: #make lower case
            search_str = search_str.lower()
        com_list = list(self.commands.keys())
        com_found_list = []
        for c in com_list:
            c_comp = c
            if not case_sensitive:
                c_comp = c_comp.lower()
            if re.findall(search_str,c_comp): #see if the expression is there
                com_found_list.append(c)
        ali_list = self.aliases.keys()
        ali_found_list = []
        for c in ali_list:
            c_comp = c
            if not case_sensitive:
                c_comp = c_comp.lower()
            if re.findall(search_str,c_comp): #see if the expression is there
                ali_found_list.append(c)
        return {'commands':com_found_list,'aliases':ali_found_list}
    
    def write(self,out_path):
        '''
        @brief write our file out in json format
        '''
        with open(out_path,'w+') as json_file:
            json.dump(self,json_file,indent=4) 
            
    def load(self,load_path):
        '''
        @brief load in a file from a json format
        @param[in] load_path - path to file to load
        '''        
        with open(load_path,'r') as json_file:
            #self = json.load(jsonFile, object_pairs_hook=OrderedDict)
            self.update(json.load(json_file, object_pairs_hook=OrderedDict))
        #now make a command
        for k,v in self.commands.items():
            com =  InstrumentCommand('','')
            com.update(v)
            self.commands[k] = com
        
        
    
    @property
    def commands(self):
        '''
        @brief shorthand for self['commands']
        '''
        return self['commands']
    
    @property
    def aliases(self):
        '''
        @brief shorthand for self['aliases']
        '''
        return self['aliases']
        
    def __getattr__(self,attr):
        '''
        @brief try and check for alias calls on getattr
        '''
        try:
            self.get(attr)
        except:
            pass
        return getattr(self,attr)

class SCPICommandDict(InstrumentCommandDict):
    '''
    @brief class for scpi commands
    '''
    def __init__(self,load_path=None):
        super().__init__(load_path)
    
    def add_command(self,instrument_command):
        '''
        @brief typical command adding except we add a shortened version alias
        '''
        com_name = self._get_default_command_name(instrument_command)
        alias_name = re.sub('[a-z]+','',com_name)
        for ig in instrument_command.options['ignore_regex_list']+[' *, *']:
            alias_name = re.sub(ig,'',alias_name)
        alias_name = alias_name.strip() #remove traling whitespace
        if not alias_name==com_name:
            super().add_command(instrument_command,alias_name)
            
    def load(self,load_path):
        super().load(load_path)
        for k,v in self.commands.items():
            com =  SCPICommand('')
            com.update(v)
            self.commands[k] = com

class InstrumentCommand(OrderedDict):
    '''
    @brief class that defines an instrument command.
        Can be SCPI, or not... can be anything
    '''
    def __init__(self,command_raw,command_type,**arg_options):
        '''
        @brief constructor
        @param[in] command_raw - raw string for command descriptor (i.e. SENS<cnum>:FREQ <num>)
        @param[in] command_type - type of command (i.e. SCPI)
        '''
        super().__init__()
        self.update({'type':command_type}) #update command type
        #self.update({'command_template':'Not yet Compiled'}) #template to place params into
        self.update({'command_raw':command_raw}) #raw command
        self.update({'description':None})
        self.update({'arguments':{'required':OrderedDict(),'optional':OrderedDict()}}) #no initial arguments
        
    def add_arg(self,arg_name,optional_flg,description='',**other_options):
        '''
        @brief add argument to this command
        @param[in] arg_name - the name of the argument. This should be the whole string (e.g. <cnum> NOT cnum)
            This is important because these names will be searched when creating the template
        @param[in] optional_flg - True if the arg is optional
        @param[in/OPT] description - brief description of the argument
        @param[in/OPT] other_options - anything else to add to the argument
            arg_string - if this is specified, this value instead of arg_name
                    will be stripped from our command when getting our template
        '''
        arg_dict = {
                'description':None,
                'default':'', #default value if not provided
                'arg_string':arg_name
                }
        arg_dict.update(other_options)
        if not optional_flg:
            self['arguments']['required'].update({arg_name:arg_dict})
        else:
            self['arguments']['optional'].update({arg_name:arg_dict})
    
    def __call__(self,*args,**kwargs):
        '''
        @brief when called as function call the parameter
        @return a string with the formatted function call
        '''
        arg_dict = self.arg_dict
        arg_keys = list(arg_dict.keys()) #ordered keys
        for i,a in enumerate(args):
            arg_dict[arg_keys[i]] = a #set in order
        for k,v in kwargs.items():
            arg_dict[k] = v #keyword values
        #now lets get our arguments in order
        format_args = tuple(arg_dict.values())
        return self.command_template.format(*format_args)
    
    def get_command_template(self,ignore_regex_list=None):
        '''
        @brief generate a template to use for command formatting
        @param[in/OPT] ignore_regex_list - list of regex of things to remove (e.g non-required args)
        '''
        template = self['command_raw']
        #first lets remove our required arguments
        for i,arg_dict in enumerate(self['arguments']['required'].values()):
            a_name = arg_dict['arg_string']
            template=template.replace(a_name,'{%d}' %(i))
        #now lets remove our optional arguments
        for j,arg_dict in enumerate(self['arguments']['optional'].values()):
            a_name = arg_dict['arg_string']
            template=template.replace(a_name,'{%d}' %(j+self.num_required_args))
        if ignore_regex_list is not None:
            for igreg in ignore_regex_list:
                template = re.sub(igreg,'',template)
        return template.strip()
    
    @property
    def command_template(self):
        '''
        @brief generate a template for our command to use for formatting
        '''
        return self.get_command_template()
    
    @property
    def arg_key_list(self):
        '''
        @brief get a list of arguments in ordered form [required,optional]
        '''
        arg_list = []
        arg_list += self['arguments']['required'].keys()
        arg_list += self['arguments']['optional'].keys()
        return arg_list
    
    @property
    def arg_dict(self):
        '''
        @brief return a list of argument names as keys with default params
        '''
        req_dict = OrderedDict((k,v['default']) for k,v in self['arguments']['required'].items())
        opt_dict = OrderedDict((k,v['default']) for k,v in self['arguments']['optional'].items())
        arg_dict = req_dict
        arg_dict.update(opt_dict)
        return arg_dict
    
    @property
    def arg_default_value_list(self):
        '''
        @brief get a list of our default argument values in order
        '''
        val_list = []
        val_list += [d['default'] for d in self['arguments']['required'].values()]
        val_list += [d['default'] for d in self['arguments']['optional'].values()]
        return val_list
    
    @property
    def num_args(self):
        '''
        @brief provide total number of arguments
        '''
        return self.num_required_args+self.num_optional_args
    
    @property
    def num_required_args(self):
        return len(self['arguments']['required'])
    
    @property
    def num_optional_args(self):
        return len(self['arguments']['optional'])
    
    def help(self):
        '''
        @brief return help for our command
        '''
        print(self['description'])
        
        
class SCPICommand(InstrumentCommand):
    '''
    @brief class specifically for scpi commands
    '''
    def __init__(self,command_raw,argument_regex='<.*?>',**arg_options):
        '''
        @brief constructor
        @param[in] command_raw - raw command string (SENSe<cnum>:FREQuency:CENTer <num>)
        @param[in/OPT] argument_regex - regular expression to extract arguments
        '''
        self.options = {}
        #in this we ignore optoinal things and either or type args ([:CW], | BWID)
        #these are ignored when we get the template and make our default aliases
        self.options['ignore_regex_list'] = ['\[.*?\]','\|.*?($|(?={))'] 
        
        #initialize the superclass
        super().__init__(command_raw,'SCPI',**arg_options)
        
        #now extract our arguments
        arg_strings = re.findall(argument_regex,command_raw)
        
        #now lets check if theyre optional or not
        com_split = command_raw.split(' ') 
        for arg_string in arg_strings:
            arg_name = re.sub('<|>','',arg_string)
            opt_flg = True
            default = ''
            if arg_string not in com_split[0]:
                opt_flg = False #if after the space its false
                default = ''
            self.add_arg(arg_name,opt_flg,default=default,arg_string=arg_string)
    
    def __call__(self,*args,**kwargs):
        call_str = super().__call__(*args,**kwargs)
        if args and args[0] is '?':
            #then remove the space
            call_str = re.sub(' +\?','?',call_str)
        #remove any trailing commas
        call_str = re.sub(' *, *$','',call_str)
        return call_str
    
    @property    
    def command_template(self):
        return self.get_command_template(ignore_regex_list=self.options['ignore_regex_list'])
    


if __name__=='__main__':
    '''
    command = 'SENSe<cnum>:FREQuency:CENTer <num>'
    command_list = [command]
    
    com_dict = InstrumentCommandDict()
    for i,c in enumerate(command_list):
        scom = SCPICommand(c)
        com_dict.add_command(scom)
    '''
    
    #test loading
    load_path = r'Q:\public\Quimby\Students\Alec\Useful_Code\command_generation\PNAX_communication_dictionary.json'
    mycom = SCPICommandDict(load_path)
    #print(mycom.call_alias('SENS:BAND')('?'))
    print(mycom.call_alias('SOUR:POW')('?'))

        
        
    
        
        
        
        
        
    

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        