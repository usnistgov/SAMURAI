# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 11:02:53 2018
edit .snp files (.s2p,.s4p,etc...)
@author: ajw5
"""
import os
import cmath 
import numpy as np
import re
import six
from xml.dom.minidom import parse 

from samurai.analysis.support.generic import deprecated

class WnpEditor:
   '''
   @brief init arbitrary port wave parameter class
   @param[in] input_file - path of file to load in. 
               A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
               measurement with n ports and frequencies [f1,f2,...] 
   '''
   def __init__(self,input_file,**arg_options):
        '''
        @brief init arbitrary port wave parameter class
        @param[in] input_file - path of file to load in. 
                    A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
                    measurement with n ports and frequencies [f1,f2,...] 
        @param[in] arg_options - keywor arguments as follows:
            header - header to write out to the file (text only)
            comments - comments to write to file (text only)
            read_header - True/False whether or not to read in header from text files (faster if false, default to true)
            waves - list of what waves we are measuring for self.waves dictionary (default ['A','B'] for s params should be ['S'])
        '''
        self.options = {}
        self.options['header'] = []
        self.options['comments'] = []
        self.options['read_header'] = True
        self.options['waves'] = ['A','B'] #waves to store. default to wave parameter
        for key,val in six.iteritems(arg_options): #overwrite defaults with inputs
            self.options[key] = val 
        #initialize dictionary of waves
        self.waves = dict()
        for w in self.options['waves']:
            self.waves[w] = dict()
        self.wave_dict_keys = [] #keys for our measurement dictionary
        #now load the file
        if(type(input_file)==str):
            self.load(input_file,read_header=self.options['read_header'])
        elif(type(input_file)==tuple or type(input_file)==list):
            self.load_empty(input_file[0],input_file[1])
            
   def _gen_dict_keys(self):
       '''
       @brief function to generate the dictionary keys for each wave in self.waves
       @note this should be redefined in inheriting classes
       @note the keys are placed in self.wave_dict_keys
       '''
       keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
       self.wave_dict_keys = keys
            
   def load(self,input_file,ftype='auto',read_header=True):
        '''
        @brief load a wave parameter file and parse into the class
        @param[in] input_file - path of file to load
        @param[in/OPT] ftype  - type of file we are loading (e.g. 'text' or 'binary')
        @param[in] read_header - whether or not to read the header and comments in text files. It is faster to not read the header/comments
        '''
        #check if were loading a .meas file first and update input accordingly
        if(input_file.split('.')[-1]=='meas'):
            input_file = get_unperturbed_meas(input_file)
            
       #if we default grab from end of file path
        if(ftype=='auto'):
            if(input_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
                
        #get the number of ports from the file extension
        file_ext = os.path.splitext(input_file)[-1]
        self.options['num_ports'] = int(''.join(re.findall(r'\d',file_ext)))
        #now set our keys
        self._gen_dict_keys()
        
        #if we have a binary file (e.g. *.w2p_binary)
        if(ftype=='binary'):
            #first read the header
            self.options['header'].append('GHz S RI 50')
            self.options['comments'].append('data read from binary file')
            [num_rows,num_cols] = np.fromfile(input_file,dtype=np.uint32,count=2) 
            raw_data = np.fromfile(input_file,dtype=np.float64) #read raw data
            raw_data = raw_data[1:] #remove header
            raw_data = raw_data.reshape((num_rows,num_cols)) #match the text output
            
        #if we have a text file (e.g. *.w2p)
        elif(ftype=='text'):
            #first read in comments
            if(read_header): #flag for reading header for speed
                with open(input_file,'r') as fp: 
                    for line in fp:
                        if(line.strip()[0]=='#'):
                            self.options['header'].append(line.strip()[1:])
                        elif(line.strip()[0]=='!'):
                            self.options['comments'].append(line.strip()[1:])
                        else: #else its data
                            pass     
            else: #dont read comments
                self.options['header'].append('GHz S RI 50')
                self.options['comments'].append('Header and comments NOT read from file')
            #now read in data from the file with many possible delimiters in cases
            #of badly formated files
            with open(input_file) as fp:
                regex_str = r'[ ,|\t]+'
                rc = re.compile(regex_str)
                raw_data = np.loadtxt((rc.sub(' ',l) for l in fp),comments=['#','!'])                  
                num_rows = np.size(raw_data,0)
                num_cols = np.size(raw_data,1) #get the number of columns
                
        #now split the data (text and binary input should be formatted the same here)
        #first check if our file is named correctly
        num_ports_from_file = int(round(np.sqrt((num_cols-1)/(len(self.waves)*2)))) #int(round(np.sqrt((num_cols-1)/2))) for snp file wnp has a and b
        if(num_ports_from_file!=self.options['num_ports']): #just make sure file matches extension
            raise MalformedSnpError("Number of ports from extension does not match amount of data in file")
        
        #file is good if we make it here so continue to unpacking
        freqs = raw_data[:,0] #extract our frequencies
        
        #now get the data for each port. This assumes that the keys are in the same order as the file info (which they should be)
        for ki,k in enumerate(self.wave_dict_keys):
            for wi,w in enumerate(self.waves):
                idx = ki*len(self.waves)*2+(1+2*wi)
                data = raw_data[:,idx]+raw_data[:,idx+1]*1j
                self.waves[w][k] = WnpParam(np.array(freqs),np.array(data))
    
   def load_empty(self,num_ports,freqs):
        '''
        @brief create a WnpEditor class with all values as 0
        @param[in] num_ports - number of ports for the class
        @param[in] num_measurements - number of measurements per parameter (i.e. number of frequencies)
        '''
        self.options['num_ports'] = num_ports #set the number of ports
        #now set our keys
        self._gen_dict_keys()
        
        #and pack the port data with 0s
        for k in self.wave_dict_keys:
            for wave in self.waves.keys():
                self.waves[wave][k] = WnpParam(np.array(freqs),np.zeros(len(freqs)))
       
   def write(self,out_file,ftype='default',delimiter=' '):
        '''
        @brief write out data to wave parameter file (e.g. '.w2p')
        @param[in] out_file - path of file name to write to
        @param[in/OPT] ftype - type of file to write out ('default' will write to whatever extension out_file has)
        @param[in/OPT] delimiter - delimiter to use when writing text files (default is ' ')
        '''
        if(ftype=='default'):
            if(out_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
       
        #round frequencies to nearest Hz
        self.round_freq_lists()
        
        #make sure the frequency lists are equal before writing; just in case somthing went wrong
        self._verify_freq_lists()
        
        #pack into correct data list
        #assume all parameters are same length
        if(ftype=='binary'):
            num_rows = len(self.w1[11].freq_list)
            temp_list = [self.w1[11].freq_list]
            for k in self.wave_dict_keys:
                for w in self.waves:
                    temp_list += [self.waves[w][k].raw.real,self.waves[w][k].raw.imag]
                
            data = np.transpose(np.array(temp_list))
            
            with open(out_file,'wb') as fp:
                num_cols = len(self.wave_dict_keys)*len(self.waves)*2+1
                np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                data.tofile(fp)
                
        elif(ftype=='text'):
            with open(out_file,'w+') as fp:
                #write our comments
                if type(self.options['comments']) is not list: #assume if its not a list ts a string
                    self.options['comments'] = [self.options['comments']]
                for i in range(len(self.options['comments'])):
                    fp.write('!%s\n' %(self.options['comments'][i]))
                #write our header
                if type(self.options['header']) is not list: #assume if its not a list ts a string
                    self.options['header'] = [self.options['header']]
                for i in range(len(self.options['header'])):
                    fp.write('#%s\n' %(self.options['header'][i]))
                #now write data
                for i in range(len(self.w1[11].raw)):
                    line_vals = [self.w1[11].freq_list[i]]
                    for k in self.wave_dict_keys:
                        for w in self.waves.values():
                            line_vals += [w[k].raw[i].real,w[k].raw[i].imag]
                    #write the line to the file. The upper ensures we get E not e
                    fp.write(delimiter.join([str(v).upper() for v in line_vals])+'\n')
                
        else:
            print('Write Type not implemented')
            
   def _verify_freq_lists(self):
       '''
       @brief make sure all parameters of all waves have the same frequency list
       @raise raises an SnpError if they don't match
       '''
       w1_key = list(self.waves.keys())[0]
       p1_key = self.wave_dict_keys[0]
       comp_freqs = self.waves[w1_key][p1_key].freq_list #frequency list to compare to
       for k in self.wave_dict_keys:
           for w in self.waves.keys():
               if not np.equal(self.waves[w][k].freq_list,comp_freqs).all():
                   raise SnpError("Frequencies of {}[{}] does not match {}[{}]".format(w,k,w1_key,p1_key))
            
   def delete_port(self,port_num): 
       '''
       @brief delete a port from the class
       @param[in] port_num - the number of the port to delete (must be less than self.options['num_ports'])
           This will start at 1 not 0 indexing
       @todo finish this when needed
       '''
       num_ports = self.options['num_ports']
       if port_num > num_ports:
           raise Exception("Cant remove port {} when there are only {} ports!".format(port_num,num_ports))
       num_ports -= 1
       self.options['num_ports'] = num_ports #decrement our number of ports
       #now get the keys for the port to remove
       removed_waves = {}
       for wk in self.waves.keys():
           removed_waves[wk] = []
       dict_keys = self.wave_dict_keys.copy() #local copy
       for k in dict_keys:
           if str(port_num) in str(k): #if it has the digit matching the port
               for wk in self.waves.keys():
                   removed_waves[wk].append(self.waves[wk].pop(k))
                   self.wave_dict_keys.remove(k)
       return removed_waves
            
   def __getitem__(self,key):
        '''
        @brief override of [] operator to get S parameters
            This is a shortcut that will return freqeuncy/complex value data
        @param[in] key - key of A,B parameters to get
        @return [frequency_list,A_complex_values,B_complex_values] list of lists from the S parameter
        '''
        out_list =  [self.waves[self.w1].freq_list]
        for w in self.waves.keys():
            out_list.append(self.waves[w][key].raw)
        return out_list
            
   def __eq__(self,other):
       '''
       @brief override default to check equality of each port. 
         we will return whther number of ports match, then lists of A matching and B matching
       @param[in] other - Wnp Editor to compare to 
       @return list of equality for each port for A and B [num_ports_eq,[A,A,A,A],[B,B,B,B]]
           if the number of ports arent equal just return [num_ports_eq,num_ports_self,num_ports_other]
       '''
       num_ports_eq = self.options['num_ports']==other.options['num_ports']
       if(not num_ports_eq): #dont check more if number of ports arent equal
           return [num_ports_eq,self.options['num_ports'],other.options['num_ports']]
       out_lists = {}
       for w in self.waves.keys():
           out_lists[w] = []
       for k in self.wave_dict_keys:
           for w in self.waves.keys():
               out_lists[w].append(self.waves[w][k]==other.waves[w][k])
       return [num_ports_eq,out_lists] 
   
   def __getattr__(self,attr):
       '''
       @brief run if we dont have the attribute
           1. try and find in waves
       '''
       try:
           return self.waves[attr]
       except:
           raise AttributeError("Attribute does not exist and is not a key in self.waves")
    
   @property
   def w1(self):
       '''
       @brief shortcut for first wave 
       '''
       return self.waves[list(self.waves.keys())[0]]
    
   def _call_wnp_param_funct(self,fname,*args):
       '''
       @brief call a function from wnp param on all waves and all parameters
       '''
       for k in self.wave_dict_keys:
           for wk in self.waves.keys():
               _funct = getattr(self.waves[wk][k],fname)
               _funct(*args) #call the function with the input args
    
   def sort(self):
       '''
       @brief sort each of our parameters by frequency
       '''
       self._call_wnp_param_funct('sort')
       
   def crop(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values outside a window
       '''
       self._call_wnp_param_funct('crop',lo_freq,hi_freq)
       
   def cut(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values inside a window
       '''
       self._call_wnp_param_funct('cut',lo_freq,hi_freq)
           
   def round_freq_lists(self):
       '''
       @brief round frequencies to nearest hz (assuming they are in GHz)
       '''
       self._call_wnp_param_funct('round_freq_list')
           
   #always assume mixing up negative will mix down
   #frequency in Ghz. 
   #very simply ideal mixing (add our LO freqeuncy)
   #this allows easy if/rf measurement fixing
   def mix_port(self,port,LO_freq = 26e9):
       '''
       @todo update for new setup
       '''
       for k in self.wave_dict_keys:
        if(int(k/10)==port): #see if its our port
            for wk in self.waves.keys():
                self.waves[wk][k].freq_list += np.round(LO_freq/1e9)
                #now round the frequencies to nearest Hz
                self.waves[wk][k].round_freq_list()

class SnpEditor(WnpEditor):
    '''
    @brief class for s parameter file (*.snp)
    '''
    def __init__(self,input_file,**arg_options):
        '''
        @brief init arbitrary port s parameter class
        @param[in] input_file - path of file to load in. 
                    A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
                    measurement with n ports and frequencies [f1,f2,...] 
        '''
        options = {}
        options['waves'] = ['S'] #do s parameters
        for k,v in arg_options.items():
            options[k] = v
        super().__init__(input_file,**options)

    def _gen_dict_keys(self):
       '''
       @brief function to generate the dictionary keys for each wave in self.waves
       @note this should be redefined in inheriting classes
       @note the keys are placed in self.wave_dict_keys
       '''
       #adding the additional self.options['waves']==['s'] here allows us to
       #extend this class and still use the wnp functionalily simply by
       #changing our 'waves' option to ['A','B']
       if self.options['num_ports']==2 and self.options['waves']==['S']:
           self.wave_dict_keys = [11,21,12,22] #because s2p files wanted to be special
       else:
           super()._gen_dict_keys() #otherwise use the generic

##############################################################################
# before snpeditor inherited from wnpeditor
##############################################################################
@deprecated("use updated SnpEditor")
class SnpEditor_old:
   '''
   @brief init arbitrary port S parameter class
   @param[in] input_file - path of file to load in. 
               A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
               measurement with n ports and frequencies [f1,f2,...] 
   '''
   def __init__(self,input_file,**arg_options):
        '''
        @brief init arbitrary port wave parameter class
        @param[in] input_file - path of file to load in. 
                    A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
                    measurement with n ports and frequencies [f1,f2,...] 
        @param[in/OPT] arg_options - keyword argument options. options are as follows:
                        'read_header' - whether or not to read the header. defaults to true, false may be faster on text files
                        'header' - header to write out
                        'comments' - comments to write to file
        '''
        #default options
        self.options = {}
        self.options['header'] = []
        self.options['comments'] = []
        self.options['read_header'] = True
        for key,val in six.iteritems(arg_options): #overwrite defaults with inputs
            self.options[key] = val 
        self.S = dict()
        self.dict_keys = [] #keys for our measurement dictionary
        #now load the file
        if(type(input_file)==str):
            self.load(input_file,read_header=self.options['read_header'])
        elif(type(input_file)==tuple or type(input_file)==list):
            self.load_empty(input_file[0],input_file[1])
        
            
   def load(self,input_file,ftype='auto',read_header=True):
        '''
        @brief load a s parameter file and parse into the class
        @param[in] input_file - path of file to load
        @param[in/OPT] ftype  - type of file we are loading (e.g. 'text' or 'binary')
        @param[in] read_header - whether or not to read the header and comments in text files. It is faster to not read the header/comments
        '''
        #check if were loading a .meas file first and update input accordingly
        if(input_file.split('.')[-1]=='meas'):
            input_file = get_unperturbed_meas(input_file)
            
       #if we default grab from end of file path
        if(ftype=='auto'):
            if(input_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
                
        #get the number of ports from the file extension
        file_ext = os.path.splitext(input_file)[-1]
        self.options['num_ports'] = int(''.join(re.findall(r'\d',file_ext)))
        #now set our keys
        self.dict_keys = [j*10+i for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
        #if we have a binary file (e.g. *.s2p_binary)
        if(ftype=='binary'):
            #first read the header
            self.options['header'].append('GHz S RI 50')
            self.options['comments'].append('data read from binary file')
            [num_rows,num_cols] = np.fromfile(input_file,dtype=np.uint32,count=2) 
            raw_data = np.fromfile(input_file,dtype=np.float64) #read raw data
            raw_data = raw_data[1:] #remove header
            raw_data = raw_data.reshape((num_rows,num_cols)) #match the text output
            
        #if we have a text file (e.g. *.s2p)
        elif(ftype=='text'):
            #first read in comments
            if(read_header): #flag for reading header for speed
                with open(input_file,'r') as fp: 
                    for line in fp:
                        if(line.strip()[0]=='#'):
                            self.options['header'].append(line.strip()[1:])
                        elif(line.strip()[0]=='!'):
                            self.options['comments'].append(line.strip()[1:])
                        else: #else its data
                            pass     
            else: #dont read comments
                self.options['header'].append('GHz S RI 50')
                self.options['comments'].append('Header and comments NOT read from file')
            #now read in data from the file with many possible delimiters in cases
            #of badly formated files
            with open(input_file) as fp:
                regex_str = r'[ ,|\t]+'
                rc = re.compile(regex_str)
                raw_data = np.loadtxt((rc.sub(' ',l) for l in fp),comments=['#','!'])                  
                num_rows = np.size(raw_data,0)
                num_cols = np.size(raw_data,1) #get the number of columns
                
        #now split the data (text and binary input should be formatted the same here)
        #first check if our file is named correctly
        num_ports_from_file = int(round(np.sqrt((num_cols-1)/2))) #int(round(np.sqrt((num_cols-1)/2))) for snp file wnp has a and b
        if(num_ports_from_file!=self.options['num_ports']): #just make sure file matches extension
            raise MalformedSnpError("Number of ports from extension does not match amount of data in file")
        
        #file is good if we make it here so continue to unpacking
        freqs = raw_data[:,0] #extract our frequencies
        
        #now get the data for each port. This assumes that the keys are in the same order as the file info (which they should be)
        for i in range(len(self.dict_keys)):
            s_idx = i*2+1
            s_data = raw_data[:,s_idx]+raw_data[:,s_idx+1]*1j
            self.S[self.dict_keys[i]] = SnpParam(np.array(freqs),np.array(s_data))
    
   def load_empty(self,num_ports,freqs):
        '''
        @brief create a WnpEditor class with all values as 0
        @param[in] num_ports - number of ports for the class
        @param[in] num_measurements - number of measurements per parameter (i.e. number of frequencies)
        '''
        self.options['num_ports'] = num_ports #set the number of ports
        #now set our keys
        if self.options['num_ports'] == 2: 
            # s2p files follow a different format... because why not
            # http://na.support.keysight.com/plts/help/WebHelp/FilePrint/SnP_File_Format.htm
            self.dict_keys = [11,21,12,22]
        else:
            self.dict_keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
        #and pack the port data with 0s
        for i in range(len(self.dict_keys)):
            self.S[self.dict_keys[i]] = WnpParam(np.array(freqs),np.zeros(len(freqs)))
            
   def delete_port(self,port_num): 
       '''
       @brief delete a port from the class
       @param[in] port_num - the number of the port to delete (must be less than self.options['num_ports'])
           This will start at 1 not 0 indexing
       @todo finish this when needed
       '''
       num_ports = self.options['num_ports']
       if port_num > num_ports:
           raise Exception("Cant remove port {} when there are only {} ports!".format(port_num,num_ports))
       
       
   def write(self,out_file,ftype='default',delimiter=' '):
        '''
        @brief write out data to S parameter file (e.g. '.s2p')
        @param[in] out_file - path of file name to write to
        @param[in/OPT] ftype - type of file to write out ('default' will write to whatever extension out_file has)
        @param[in/OPT] delimiter - delimiter to use when writing text files (default is ' ')
        '''
        if(ftype=='default'):
            if(out_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
       
        #round frequencies to nearest Hz
        self.round_freq_lists()
        
        #make sure the frequency lists are equal before writing; just in case somthing went wrong
        for i in range(1,len(self.dict_keys)):
            if(not np.equal(self.S[self.dict_keys[i]].freq_list,self.S[self.dict_keys[i-1]].freq_list).all()):
               print("ERROR: Frequency Ranges are not all equal! Aborting")
               return -1 
        
        #pack into correct data list
        #assume all parameters are same length
        if(ftype=='binary'):
            num_rows = len(self.S[11].freq_list)
            temp_list = [self.S[11].freq_list]
            for k in self.dict_keys:
                temp_list += [self.S[k].raw.real,self.S[k].raw.imag]
                
            data = np.transpose(np.array(temp_list))
            
            with open(out_file,'wb') as fp:
                num_cols = len(self.dict_keys)*2+1
                np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                data.tofile(fp)
                
        elif(ftype=='text'):
            with open(out_file,'w+') as fp:
                #write our comments
                if(type(self.options['comments']!=list)): #assume if its not a list ts a string
                    self.options['comments'] = [self.options['comments']]
                for i in range(len(self.options['comments'])):
                    fp.write('!%s\n' %(self.options['comments'][i]))
                #write our header
                if(type(self.options['header']!=list)): #assume if its not a list ts a string
                    self.options['header'] = [self.options['header']]
                for i in range(len(self.options['header'])):
                    fp.write('#%s\n' %(self.options['header'][i]))
                #now write data
                for i in range(len(self.S[11].raw)):
                    line_vals = [self.S[11].freq_list[i]]
                    for k in self.dict_keys:
                        line_vals += [self.S[k].raw[i].real,self.S[k].raw[i].imag]
                    fp.write(delimiter.join([str(v) for v in line_vals])+'\n')
                
        else:
            print('Write Type not implemented')
            
   def __eq__(self,other):
       '''
       @brief override default to check equality of each port. 
         we will return whther number of ports match, then lists of A matching and B matching
       @param[in] other - Wnp Editor to compare to 
       @return list of equality for each port for A and B [num_ports_eq,[S,S,S,S]]
           if the number of ports arent equal just return [num_ports_eq,num_ports_self,num_ports_other]
       '''
       num_ports_eq = self.options['num_ports']==other.options['num_ports']
       if(not num_ports_eq): #dont check more if number of ports arent equal
           return [num_ports_eq,self.options['num_ports'],other.options['num_ports']]
       s_list = []
       for k in self.dict_keys:
           s_list.append(self.S[k]==other.S[k])
       return [num_ports_eq,s_list]   
    
    
   def sort(self):
       '''
       @brief sort each of our parameters by frequency
       '''
       for k in self.dict_keys:
           self.S[k].sort()
       
   def crop(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values outside a window
       '''
       for k in self.dict_keys:
           self.S[k].crop(lo_freq,hi_freq)
       
   def cut(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values inside a window
       '''
       for k in self.dict_keys:
           self.S[k].cut(lo_freq,hi_freq)
           
   def round_freq_lists(self):
       '''
       @brief round frequencies to nearest hz (assuming they are in GHz)
       '''
       for k in self.dict_keys:
           self.S[k].round_freq_list()
           
   #always assume mixing up negative will mix down
   #frequency in Ghz. 
   #very simply ideal mixing (add our LO freqeuncy)
   #this allows easy if/rf measurement fixing
   def mix_port(self,port,LO_freq = 26e9):
       for k in self.dict_keys:
        if(int(k/10)==port): #see if its port 2
            self.S[k].freq_list += np.round(LO_freq/1e9)
            #now round the frequencies to nearest Hz
            self.S[k].round_freq_list()

   def __getitem__(self,key):
        '''
        @brief override of [] operator to get S parameters
            This is a shortcut that will return freqeuncy/complex value data
        @param[in] key - key of s parameters to get
        @return [frequency_list,complex_values] list of lists from the S parameter
        '''
        return [self.S[key].freq_list,self.S[key].raw]

# =============================================================================
# class snpEditor:
#     
#     def __init__(self,inputFile='none'):
#         self.freqs   = [];
#         self.sParams = {} #dicitionary of our S params
# #        if(inputFile!='none'):
# #            self.parseFile(inputFile);
#         
#     def loadS2P(self,filePath):
#         portDict = {"raw":[],"mag":[],"phase":[],"phase_d":[]}
#         self.sParams.update({"S11":portDict})
#         self.sParams.update({"S12":portDict})
#         self.sParams.update({"S21":portDict})
#         self.sParams.update({"S22":portDict})
#             
#     #pase the input file
#  #   def parseFile(self,filePath):
#         #first find what kind of file
#  #       fend = filePath.split('.')[-1];
#  
# =============================================================================
 

#acutally is the same as snpParam
class WnpParam:
    '''
    @brief class for a single wave parameter (e.g. A[11])
    '''
    def __init__(self,freq_list,raw_list):
        '''
        @brief initialize our parameter
        @param[in] freq_list - list of frequencies for the parameter data
        @param[in] raw_list  - raw complex data for the parameter
        '''
        self.update(freq_list,raw_list)
        
    def sort(self):
        '''
        @brief sort the parameter by frequency
        '''
        myzipped = zip(self.freq_list,self.raw)
        list(myzipped).sort()
        freq_list,raw = zip(*myzipped)
        self.freq_list = np.array(freq_list)
        self.raw = np.array(raw)
        
    #crop out all frequencies outside a window given by lo and hi frequencies (in Hz)
    def crop(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove all frequencies and their corresponding values outside a given window
        '''
        lo_val = np.round(lo_freq/1e9,decimals=9)
        hi_val = np.round(hi_freq/1e9,decimals=9)
        #data is in ghz in files
        del_idx = np.where(np.logical_or(self.freq_list<lo_val,self.freq_list>hi_val))
        if(np.size(del_idx)==np.size(self.freq_list)):
            print("Error: No Frequencies within range! Aborting")
            return -1
        #delete array seems to end up
        #self.del_idx = del_idx;
        self.freq_list = np.delete(self.freq_list,del_idx)
        self.raw = np.delete(self.raw,del_idx)
        
    #cut out all frequencies insides a window given by lo and hi frequencies (in Hz)
    def cut(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove all frequencies and their corresponding values inside a given window
        '''
        lo_val = np.round(lo_freq/1e9,decimals=9)
        hi_val = np.round(hi_freq/1e9,decimals=9)
        #data is in ghz in files
        del_idx = np.where(np.logical_or(self.freq_list>lo_val,self.freq_list<hi_val))
        if(np.size(del_idx)==np.size(self.freq_list)):
            print("Error: No Frequencies within range! Aborting")
            return -1
        #delete array seems to end up
        #self.del_idx = del_idx;
        self.freq_list = np.delete(self.freq_list,del_idx)
        self.raw = np.delete(self.raw,del_idx)
    
    #round frequency list to nearest hz
    #useful for writing out 
    def round_freq_list(self):
        '''
        @brief round frequency list to nearest hz assuming values are in GHz
        '''
        #assume frequency values are in GHz and we round to Hz
        self.freq_list=np.round(self.freq_list,decimals=9)
    
    #put new values into the class
    def update(self,freq_list,raw_list):
        '''
        @brief put new values into the class
        @param[in] freq_list - list of frequencies for the parameter data
        @param[in] raw_list  - raw complex data for the parameter
        '''
        self.freq_list = freq_list
        self.raw = raw_list
        
    def calculate_time_domain(self):
        ifft_vals = np.fft.ifft(self.raw)
        total_time = 1/np.diff(self.freq_list).mean()
        times = np.linspace(0,total_time,self.freq_list.shape[0])
        return times,ifft_vals
        
    @property
    def mag(self):
        '''
        @brief property for magnitude
        @return list of magnitude data
        '''
        return [abs(i) for i in self]

    @property
    def phase(self):
        '''
        @brief property for phase in radians
        @return list of phase data in radians
        '''
        return [cmath.phase(i) for i in self]

    @property
    def phase_d(self):
        '''
        @brief property for phase in degrees
        @return list of phase data in degrees
        '''
        return [cmath.phase(i)*180/np.pi for i in self]
    
    def __get__(self,instance,owner):
        return instance.raw
    
    def __getitem__(self,idx):
        return self.raw[idx]
    
    def __eq__(self,other):
        '''
        @brief check equality of frequency and data in parameter
        @return [freq_eq,data_eq]
        '''
        freq_eq = np.equal(self.freq_list,other.freq_list).all()
        data_eq = np.equal(self.raw,other.raw).all()
        return freq_eq,data_eq
        
class SnpParam(WnpParam):
     
    def __init__(self,freqList,rawList):
        WnpParam.__init__(self,freqList,rawList)
         
             
#sl = s2pEditor('U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Cable_Drift/5-18-2018_stretchRepeats/processed/preCal/short_load.s2p')
#get unperturbed result from .meas file
def get_unperturbed_meas(fname):
    dom = parse(fname)
    msp = dom.getElementsByTagName('MeasSParams').item(0)
    unpt = msp.getElementsByTagName('Item').item(0)
    unpt_name = unpt.getElementsByTagName('SubItem').item(1).getAttribute('Text')
    return unpt_name


class SnpError(Exception):
    '''
    @brief custom exception for errors in snp handling
    '''
    def __init__(self,err_msg):
        self.err_msg = err_msg
    def __str__(self):
        return repr("SnP/WnP ERROR: %s" %(self.err_msg)) 
    
class MalformedSnpError(SnpError):
    '''
    @brief snp/wnp file is not formed correctly error
    '''
    def __init__(self,err_msg):
        super().__init__(err_msg)
    

if __name__=='__main__':

    snp_test = True
    wnp_test = False
    
    #geyt the current file directory
    import os 
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if wnp_test:
        print("Loading *.wnp files")
        #load_path = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\4-5-2019\cal\calibration_pre\load.w3p"
        #load = WnpEditor(load_path)
        #load.delete_port(2)
        wnp_text_path = os.path.join(dir_path,'test.w2p')
        wnp_bin_path  = os.path.join(dir_path,'test.w2p_binary')
        wnp_text = WnpEditor(wnp_text_path)
        wnp_bin  = WnpEditor(wnp_bin_path)
    if snp_test:
        print("Loading *.snp files")
        snp_text_path = os.path.join(dir_path,'test.s2p')
        snp_bin_path  = os.path.join(dir_path,'test.s2p_binary')
        snp_text = SnpEditor(snp_text_path)
        snp_bin  = SnpEditor(snp_bin_path)
        snp_text.write('test2.s2p')
        snp_text.write('test2.s2p_binary')
        snp_text2 = SnpEditor('test2.s2p_binary')
        snp_text2.write('test22.s2p')
        print(snp_text==snp_text2)
        snp_bin.write('test3.s2p')
        snp_bin2 = SnpEditor('test3.s2p')
        print(snp_bin==snp_bin2)
        os.remove('test2.s2p')
        os.remove('test2.s2p_binary')
        os.remove('test22.s2p')
        os.remove('test3.s2p')
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        