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
        '''
        self.options = {}
        self.options['header'] = []
        self.options['comments'] = []
        self.options['read_header'] = True
        for key,val in six.iteritems(arg_options): #overwrite defaults with inputs
            self.options[key] = val 
        self.A = dict()
        self.B = dict()
        self.dict_keys = [] #keys for our measurement dictionary
        #now load the file
        if(type(input_file)==str):
            self.load(input_file,read_header=self.options['read_header'])
        elif(type(input_file)==tuple or type(input_file)==list):
            self.load_empty(input_file[0],input_file[1])
        
            
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
        self.dict_keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
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
        num_ports_from_file = int(round(np.sqrt((num_cols-1)/4))) #int(round(np.sqrt((num_cols-1)/2))) for snp file wnp has a and b
        if(num_ports_from_file!=self.options['num_ports']): #just make sure file matches extension
            raise MalformedSnpError("Number of ports from extension does not match amount of data in file")
        
        #file is good if we make it here so continue to unpacking
        freqs = raw_data[:,0] #extract our frequencies
        
        #now get the data for each port. This assumes that the keys are in the same order as the file info (which they should be)
        for i in range(len(self.dict_keys)):
            a_idx = i*4+1
            a_data = raw_data[:,a_idx]+raw_data[:,a_idx+1]*1j
            self.A[self.dict_keys[i]] = WnpParam(np.array(freqs),np.array(a_data))
            b_idx = i*4+3
            b_data = raw_data[:,b_idx]+raw_data[:,b_idx+1]*1j
            self.B[self.dict_keys[i]] = WnpParam(np.array(freqs),np.array(b_data))
    
   def load_empty(self,num_ports,freqs):
        '''
        @brief create a WnpEditor class with all values as 0
        @param[in] num_ports - number of ports for the class
        @param[in] num_measurements - number of measurements per parameter (i.e. number of frequencies)
        '''
        self.options['num_ports'] = num_ports #set the number of ports
        #now set our keys
        self.dict_keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
        #and pack the port data with 0s
        for i in range(len(self.dict_keys)):
            self.A[self.dict_keys[i]] = WnpParam(np.array(freqs),np.zeros(len(freqs)))
            self.B[self.dict_keys[i]] = WnpParam(np.array(freqs),np.zeros(len(freqs)))
       
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
        for i in range(1,len(self.dict_keys)):
            if(not np.equal(self.A[self.dict_keys[i]].freq_list,self.B[self.dict_keys[i]].freq_list).all()
            or not np.equal(self.A[self.dict_keys[i]].freq_list,self.A[self.dict_keys[i-1]].freq_list).all()
            or not np.equal(self.B[self.dict_keys[i]].freq_list,self.B[self.dict_keys[i-1]].freq_list).all()):
               print("ERROR: Frequency Ranges are not all equal! Aborting")
               return -1 
        
        #pack into correct data list
        #assume all parameters are same length
        if(ftype=='binary'):
            num_rows = len(self.A[11].freq_list)
            temp_list = [self.A[11].freq_list]
            for k in self.dict_keys:
                temp_list += [self.A[k].raw.real,self.A[k].raw.imag]
                temp_list += [self.B[k].raw.real,self.B[k].raw.imag]
                
            data = np.transpose(np.array(temp_list))
            
            with open(out_file,'wb') as fp:
                num_cols = len(self.dict_keys)*4+1
                np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                data.tofile(fp)
                
        elif(ftype=='text'):
            with open(out_file,'w+') as fp:
                #write our comments
                for i in range(len(self.options['comments'])):
                    fp.write('!%s\n' %(self.options['comments'][i]))
                #write our header
                for i in range(len(self.options['header'])):
                    fp.write('#%s\n' %(self.options['header'][i]))
                #now write data
                for i in range(len(self.A[11].raw)):
                    line_vals = [self.A[11].freq_list[i]]
                    for k in self.dict_keys:
                        line_vals += [self.A[k].raw[i].real,self.A[k].raw[i].imag]
                        line_vals += [self.B[k].raw[i].real,self.B[k].raw[i].imag]

                    fp.write(delimiter.join([str(v) for v in line_vals])+'\n')
                
        else:
            print('Write Type not implemented')

   def __getitem__(self,key):
        '''
        @brief override of [] operator to get S parameters
            This is a shortcut that will return freqeuncy/complex value data
        @param[in] key - key of A,B parameters to get
        @return [frequency_list,A_complex_values,B_complex_values] list of lists from the S parameter
        '''
        return [self.A[key].freq_list,self.A[key].raw,self.B[key].raw]
            
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
       a_list = []
       b_list = []
       for k in self.dict_keys:
           a_list.append(self.A[k]==other.A[k])
           b_list.append(self.B[k]==other.B[k])
       return [num_ports_eq,a_list,b_list]   
    
    
   def sort(self):
       '''
       @brief sort each of our parameters by frequency
       '''
       for k in self.dict_keys:
           self.A[k].sort()
           self.B[k].sort()

       
   def crop(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values outside a window
       '''
       for k in self.dict_keys:
           self.A[k].crop(lo_freq,hi_freq)
           self.B[k].crop(lo_freq,hi_freq)
       
   def cut(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values inside a window
       '''
       for k in self.dict_keys:
           self.A[k].cut(lo_freq,hi_freq)
           self.B[k].cut(lo_freq,hi_freq)
           
   def round_freq_lists(self):
       '''
       @brief round frequencies to nearest hz (assuming they are in GHz)
       '''
       for k in self.dict_keys:
           self.A[k].round_freq_list()
           self.B[k].round_freq_list()
           
   #always assume mixing up negative will mix down
   #frequency in Ghz. 
   #very simply ideal mixing (add our LO freqeuncy)
   #this allows easy if/rf measurement fixing
   def mix_port(self,port,LO_freq = 26e9):
       for k in self.dict_keys:
        if(int(k/10)==port): #see if its port 2
            self.A[k].freq_list += np.round(LO_freq/1e9)
            self.B[k].freq_list += np.round(LO_freq/1e9)
            #now round the frequencies to nearest Hz
            self.A[k].round_freq_list()
            self.B[k].round_freq_list()

class SnpEditor:
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
        self.dict_keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
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
        self.dict_keys = [i*10+j for i in range(1,self.options['num_ports']+1) for j in range(1,self.options['num_ports']+1)]
        
        #and pack the port data with 0s
        for i in range(len(self.dict_keys)):
            self.S[self.dict_keys[i]] = WnpParam(np.array(freqs),np.zeros(len(freqs)))
       
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
                for i in range(len(self.options['comments'])):
                    fp.write('!%s\n' %(self.options['comments'][i]))
                #write our header
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

        
#############################################################################################
@deprecated("User WnpEditor class")
class W2pEditor:
   '''
   @brief class for w2p files
   @depracated Use WnpEditor
   '''
   def __init__(self,input_file='none',ftype='default'):
       
        self.header = []
        self.comments = []
        self.dict_keys = [11,21,12,22] #default
        self.A = dict(); self.B = dict()
        if(input_file!='none'):
            self.load(input_file,ftype=ftype)

            
   def load(self,input_file,ftype='default',delimiter=' '):
       
       #check if were loading a .meas file first and update input accordingly
        if(input_file.split('.')[-1]=='meas'):
            input_file = get_unperturbed_meas(input_file)
            
       #if we default grab from end of file path
        if(ftype=='default'):
            if(input_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
       

        a11_raw = []; b11_raw = []
        a21_raw = []; b21_raw = []
        a12_raw = []; b12_raw = []
        a22_raw = []; b22_raw = []
        freqs = []
        
        
        
        if(ftype=='binary'):
            with open(input_file,'rb') as fp: #open file
                [num_rows,num_cols] = np.fromfile(fp,dtype=np.uint32,count=2) #read header
                #num_rows.append(num_rows);num_cols.append(cur_num_cols); #keep track from each file
                #now read all our data but store line by line to rearrange later
                for j in range(num_rows):
                    #read in and unpack
                    cur_data = np.fromfile(fp,count=num_cols,dtype=np.float64)
                    freqs.append(cur_data[0])
                    a11_raw.append(cur_data[1]+1j*cur_data[2])
                    b11_raw.append(cur_data[3]+1j*cur_data[4])
                    a21_raw.append(cur_data[5]+1j*cur_data[6])
                    b21_raw.append(cur_data[7]+1j*cur_data[8])
                    a12_raw.append(cur_data[9]+1j*cur_data[10])
                    b12_raw.append(cur_data[11]+1j*cur_data[12])
                    a22_raw.append(cur_data[13]+1j*cur_data[14])
                    b22_raw.append(cur_data[15]+1j*cur_data[16])
                    
        elif(ftype=='text'):
            with open(input_file,'r') as fp:
                for line in fp:
                    if(line.strip()[0]=='#'):
                       self.header.append(line)
                    elif(line.strip()[0]=='!'):
                       self.comments.append(line)
                    else: #else its data
                        llist = re.split(delimiter+r'*\|*\t* *',line) #split on lots of charactors and given delimeter
                        llist = [l.strip() for l in llist]
                        freqs.append(np.float64(llist[0]))
                        a11_raw.append(np.float64(llist[1])+1j*np.float64(llist[2]))
                        a21_raw.append(np.float64(llist[5])+1j*np.float64(llist[6]))
                        a12_raw.append(np.float64(llist[9])+1j*np.float64(llist[10]))
                        a22_raw.append(np.float64(llist[13])+1j*np.float64(llist[14]))
                        b11_raw.append(np.float64(llist[3])+1j*np.float64(llist[4]))
                        b21_raw.append(np.float64(llist[7])+1j*np.float64(llist[8]))
                        b12_raw.append(np.float64(llist[11])+1j*np.float64(llist[12]))
                        b22_raw.append(np.float64(llist[15])+1j*np.float64(llist[16]))
            
            
        #pack into dictionary for easy extension
        self.A.update({11:WnpParam(np.array(freqs),np.array(a11_raw))})
        self.A.update({21:WnpParam(np.array(freqs),np.array(a21_raw))})
        self.A.update({12:WnpParam(np.array(freqs),np.array(a12_raw))})
        self.A.update({22:WnpParam(np.array(freqs),np.array(a22_raw))})
        self.B.update({11:WnpParam(np.array(freqs),np.array(b11_raw))})
        self.B.update({21:WnpParam(np.array(freqs),np.array(b21_raw))})
        self.B.update({12:WnpParam(np.array(freqs),np.array(b12_raw))})
        self.B.update({22:WnpParam(np.array(freqs),np.array(b22_raw))})
        
        #store the keys nicely for quick indexing
        self.dict_keys = [11,21,12,22]
            
   def write(self,out_file,ftype='default',delimiter=' '):
       
        if(ftype=='default'):
            if(out_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
       
        #round frequencies to nearest Hz
        self.round_freq_lists()
        
        #make sure the frequency lists are equal before writing;
        if(not np.equal(self.A[11].freq_list,self.B[11].freq_list).all()
            or not np.equal(self.A[21].freq_list,self.B[11].freq_list).all()
            or not np.equal(self.A[21].freq_list,self.B[21].freq_list).all()
            or not np.equal(self.A[12].freq_list,self.B[21].freq_list).all()
            or not np.equal(self.A[12].freq_list,self.B[12].freq_list).all()
            or not np.equal(self.A[22].freq_list,self.B[12].freq_list).all()
            or not np.equal(self.A[22].freq_list,self.B[22].freq_list).all()):
            print("ERROR: Frequency Ranges are not all equal! Aborting")
            return -1
        #pack into correct data list
        #assume all parameters are same length
        if(ftype=='binary'):
            num_rows = len(self.A[11].freq_list)
            temp_list = [self.A[11].freq_list]
            for k in self.dict_keys:
                temp_list += [self.A[k].raw.real,self.A[k].raw.imag]
                temp_list += [self.B[k].raw.real,self.B[k].raw.imag]
                
            data = np.transpose(np.array(temp_list))
            
            with open(out_file,'wb') as fp:
                num_cols = len(self.dict_keys)*4+1
                np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                data.tofile(fp)
                
        elif(ftype=='text'):
            with open(out_file,'w+') as fp:
                #write our comments
                for i in range(len(self.comments)):
                    fp.write(self.comments[i])
                #write our header
                for i in range(len(self.header)):
                    fp.write(self.header[i])
                #now write data
                for i in range(len(self.A[11].raw)):
                    line_vals = [self.A[11].freq_list[i]]
                    for k in self.dict_keys:
                        line_vals += [self.A[k].raw[i].real,self.A[k].raw[i].imag]
                        line_vals += [self.B[k].raw[i].real,self.B[k].raw[i].imag]

                    fp.write(delimiter.join([str(v) for v in line_vals])+'\n')
                
        else:
            print('Write Type not implemented')
            
   def sort(self):
       for k in self.dict_keys:
           self.A[k].sort()
           self.B[k].sort()

       
   def crop(self,lo_freq=0,hi_freq=1e60):
       for k in self.dict_keys:
           self.A[k].crop(lo_freq,hi_freq)
           self.B[k].crop(lo_freq,hi_freq)
       
   def cut(self,lo_freq=0,hi_freq=1e60):
       for k in self.dict_keys:
           self.A[k].cut(lo_freq,hi_freq)
           self.B[k].cut(lo_freq,hi_freq)
           
   def round_freq_lists(self):
       for k in self.dict_keys:
           self.A[k].round_freq_list()
           self.B[k].round_freq_list()
           
   #always assume mixing up negative will mix down
   #frequency in Ghz. 
   #very simply ideal mixing (add our LO freqeuncy)
   #this allows easy if/rf measurement fixing
   def mix_port(self,port,LO_freq = 26e9):
       for k in self.dict_keys:
        if(int(k/10)==port): #see if its port 2
            self.A[k].freq_list += np.round(LO_freq/1e9)
            self.B[k].freq_list += np.round(LO_freq/1e9)
            #now round the frequencies to nearest Hz
            self.A[k].round_freq_list()
            self.B[k].round_freq_list()
            
    #return s2pEditor instantiation. snp_config decides to set certain values to zero (THIS IS IMCOMPLETE) [S11,S21,S12,S22]
   def convert_to_snp(self,snp_config = [0,1,0,1],post_measurements = [[],[],[],[]]):
       #first start with blank editor with A11 frequencies
       my_snp = s2pEditor(freq_list_ghz = self.A[11].freq_list)
       #for our current case we just want a basic S21 assuming everything else is 0
       #for i in range(len(snp_config)):
       #    if snp_config[i]:
       #        my_snp.S[my_snp.dict_keys[i]].update(self.)
       #if snp_config[1]
       #S21_vals = self.B[22].raw/self.A[22].raw
       if(not post_measurements[3]): #this will be used if A22 and B22 meausremntes were not acutally measuring those values like in first measurements
           #make them all zeros for now. Eventually we will want to use B22/A22 as our S22 value
           S22_vals = np.zeros(len(self.A[11].raw))
           if(snp_config[3]):
               S22_vals = self.B[22].raw/self.A[22].raw
       else:
           S22_vals = post_measurements[3]
       
       #my_snp.S[21].update(self.A[11].freq_list,self.B[21].raw/self.A[11].raw)
       S21_vals = (self.B[21].raw-S22_vals*self.A[21].raw)/self.A[11].raw
       my_snp.S[21].update(self.A[11].freq_list,S21_vals)
       my_snp.S[22].update(self.A[22].freq_list,S22_vals)
       return my_snp

@deprecated("Use SnpEditor class")
class S2pEditor:
    #inputFile automatically laods an s2p file. if not given, S2P file with all zeros will be generated with freq_list frequencies (if provided) frequencies provided in GHz
    def __init__(self,inputFile='none',freq_list_ghz=[]):\
    
        self.header = []
        self.comments = []
        self.S = dict()
        self.dict_keys = []
        if(inputFile!='none'): #if provided, load our file
            self.load(inputFile)
            
        else:#generate a bunch of zeros because no input file provided. This will be overwritten if load is called
            self.dict_keys = [11,21,12,22]
            self.comments = ['Partial Values Generated']
            if not np.size(freq_list_ghz): #no frequency list provided so generate default
                freq_list_ghz = np.arange(26.5,40,.01)
            freq_len = np.size(freq_list_ghz)
            raw_list = np.zeros(freq_len)
            for k in self.dict_keys:
                self.S[k] = SnpParam(freq_list_ghz,raw_list)
                
                
            
            
    #flip ports
    def flip(self):
        s11tmp = self.S[11]
        s21tmp = self.S[21]
        self.S[11] = self.S[22]
        self.S[21] = self.S[12]
        self.S[22] = s11tmp
        self.S[12] = s21tmp
    
    #load from file
    def load(self,filePath,ftype='default',delimiter=','):
        
        #check if were loading a .meas file first and update input accordingly
        if(filePath.split('.')[-1]=='meas'):
            filePath = get_unperturbed_meas(filePath)
            
        if(ftype=='default'):
            if(filePath.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
                
        
        s11raw = []
        s21raw = []
        s12raw = []
        s22raw = []
        freqList = []
        
        if(ftype=='binary'):
            with open(filePath,'rb') as fp: #open file
                [num_rows,num_cols] = np.fromfile(fp,dtype=np.uint32,count=2) #read header
                #num_rows.append(num_rows);num_cols.append(cur_num_cols); #keep track from each file
                #now read all our data but store line by line to rearrange later
                for j in range(num_rows):
                    #read in and unpack
                    cur_data = np.fromfile(fp,count=num_cols,dtype=np.float64)
                    freqList.append(cur_data[0])
                    s11raw.append(cur_data[1]+1j*cur_data[2])
                    s21raw.append(cur_data[3]+1j*cur_data[4])
                    s12raw.append(cur_data[5]+1j*cur_data[6])
                    s22raw.append(cur_data[7]+1j*cur_data[8])
    
        elif(ftype=='text'):
            with open(filePath,'r') as fp:
                self.header = []
                self.comments = []
                for line in fp:
                    if(line.strip()[0]=='#'):
                       self.header.append(line)
                    elif(line.strip()[0]=='!'):
                       self.comments.append(line)
                    else: #else its data
                        llist = re.split((r'[ ,|\t%s]+' %(delimiter)),line) #split on lots of charactors and given delimeter
                        llist = [l.strip() for l in llist]
                        freqList.append(float(llist[0]))
                     #   print(line)
                        s11raw.append(np.float64(llist[1])+1j*np.float64(llist[2]))
                        s21raw.append(np.float64(llist[3])+1j*np.float64(llist[4]))
                        s12raw.append(np.float64(llist[5])+1j*np.float64(llist[6]))
                        s22raw.append(np.float64(llist[7])+1j*np.float64(llist[8]))

        #now write to ports keep this for backward compatability
        self.S11 = SnpParam(np.array(freqList),np.array(s11raw))
        self.S21 = SnpParam(np.array(freqList),np.array(s21raw))
        self.S12 = SnpParam(np.array(freqList),np.array(s12raw))
        self.S22 = SnpParam(np.array(freqList),np.array(s22raw))
        self.freq_list = freqList
        #this is a better method
        self.dict_keys = [11,21,12,22]
        self.S[11] = self.S11
        self.S[21] = self.S21
        self.S[12] = self.S12
        self.S[22] = self.S22
        
    #write to file
    def write(self,filePath,ftype='default',delimiter=' '):
        
        if(ftype=='default'):
            if(filePath.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
                
                
        #make sure the frequency lists are equal before writing;
        if(not np.equal(self.S[21].freq_list,self.S[11].freq_list).all()
            or not np.equal(self.S[12].freq_list,self.S[21].freq_list).all()
            or not np.equal(self.S[22].freq_list,self.S[12].freq_list).all()):
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
            
            with open(filePath,'wb') as fp:
                num_cols = len(self.dict_keys)*2+1
                np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                data.tofile(fp)
        elif(ftype=='text'):     
            with open(filePath,'w+') as fp:
                #write our comments
                for i in range(len(self.comments)):
                    comment_line = self.comments[i]+'\n'
                    if(comment_line[0]!='!'):
                       comment_line = '!'+comment_line
                    fp.write(comment_line)
                #write our header
                for i in range(len(self.header)):
                    header_line = self.header[i]+'\n'
                    if(header_line[0]!='#'):
                        header_line = '#'+header_line
                    fp.write(header_line)
                #now write data
                #for i in range(len(self.S11.raw)):
                #    lineVals = [self.S11.freq_list[i]];
                #    lineVals += [self.S11.raw[i].real,self.S11.raw[i].imag];
                #    lineVals += [self.S21.raw[i].real,self.S21.raw[i].imag];
                #    lineVals += [self.S12.raw[i].real,self.S12.raw[i].imag];
                #    lineVals += [self.S22.raw[i].real,self.S22.raw[i].imag];
                #    fp.write(delimiter.join([str(v) for v in lineVals])+'\n')
                for i in range(len(self.S[11].raw)):
                    lineVals = [self.S[11].freq_list[i]]
                    lineVals += [self.S[11].raw[i].real,self.S[11].raw[i].imag]
                    lineVals += [self.S[21].raw[i].real,self.S[21].raw[i].imag]
                    lineVals += [self.S[12].raw[i].real,self.S[12].raw[i].imag]
                    lineVals += [self.S[22].raw[i].real,self.S[22].raw[i].imag]
                    fp.write(delimiter.join([str(v) for v in lineVals])+'\n')
        else:
            print("Write Type not Implemented")
            
                
    #split into S1P values
    def split(self):
        s1p_a = s1pEditor(sParam = self.S11,header = self.header)
        s1p_b = s1pEditor(sParam = self.S22,header = self.header)
        return s1p_a,s1p_b
    
    def crop(self,lo=0,hi=1e60):
        self.S11.crop(lo,hi)
        self.S21.crop(lo,hi)
        self.S12.crop(lo,hi)
        self.S22.crop(lo,hi)
        
    def cut(self,lo=0,hi=1e60):
        self.S11.crop(lo,hi)
        self.S21.crop(lo,hi)
        self.S12.crop(lo,hi)
        self.S22.crop(lo,hi)
    
#alias the class for legacy support
s2pEditor = S2pEditor
    
#cerate new S2P structs with swapped S12 and S22
def swapS2P(sa,sb):
    soa = s2pEditor()
    sob = s2pEditor()
    
    soa.header = sa.header
    soa.comments = sa.comments
    soa.freq_list = sa.freq_list
    soa.S[11] = sa.S[11]
    soa.S[21] = sa.S[21]
    soa.S[12] = sb.S[12]
    soa.S[22] = sb.S[22] 
    
    sob.header = sb.header
    sob.comments = sb.comments
    sob.freq_list = sb.freq_list
    sob.S[11] = sb.S[11]
    sob.S[21] = sb.S[21]
    sob.S[12] = sa.S[12]
    sob.S[22] = sa.S[22]
    
    return soa,sob

#flip ports 1 and 2
def flip_s2p(file_in,file_out):
    s_in = s2pEditor(file_in)
    s_in.flip()
    s_in.write(file_out)
    
def crop_s2p(file_in,file_out,freq_lo,freq_hi):
    s = s2pEditor(file_in)
    s.crop(freq_lo,freq_hi)
    s.write(file_out)

@deprecated("use SnpEditor Class")
class s1pEditor:   
    def __init__(self,inputFile='none',rawData='',freqList='',sParam='',header=[],comments=[]):
        if(inputFile!='none'):
            self.load(inputFile)
        elif(rawData!=''):
            self.S11 = SnpParam(freqList,rawData)
            self.header = header
            self.comments = comments
        elif(sParam!=''):
            self.S11 = sParam
            self.header = header
            self.comments = comments
     
    #load from file
    def load(self,filePath,delimiter=' '):
        with open(filePath,'r') as fp:
            self.header = []
            self.comments = []
            s11raw = []
            freqList = []
            for line in fp:
                if(line.strip()[0]=='#'):
                   self.header.append(line)
                elif(line.strip()[0]=='!'):
                   self.comments.append(line)
                else: #else its data
                    llist = line.split(delimiter)
                    llist = line.split('\t') #split on tabs too
                    llist = [l.strip() for l in llist]
                    freqList.append(float(llist[0]))
                    s11raw.append(float(llist[1])+1j*float(llist[2]))
        #now write to ports
        self.S11 = SnpParam(freqList,s11raw)
        
    #write to file
    def write(self,filePath,delimiter=' '):
        with open(filePath,'w+') as fp:
            #write our comments
            for i in range(len(self.comments)):
                fp.write(self.comments[i])
            #write our header
            for i in range(len(self.header)):
                fp.write(self.header[i])
            #now write data
            for i in range(len(self.S11.raw)):
                lineVals = [self.S11.freq_list[i]]
                lineVals += [self.S11.raw[i].real,self.S11.raw[i].imag]
                fp.write(delimiter.join([str(v) for v in lineVals])+'\n')
                
    def write_binary(self,filePath):
        print("IMPLEMENT")


#class s4pEditor

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
        return self.raw
    
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
    
    
        
