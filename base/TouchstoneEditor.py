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

from samurai.analysis.support.SamuraiPlotter import SamuraiPlotter

from samurai.analysis.support.generic import deprecated

DEFAULT_HEADER = 'GHz S RI 50'
DEFAULT_EMPTY_HEADER = 'Hz S RI 50'
DEFAULT_COMMENTS = []
HEADER_FREQ_REGEX = '[KMGT]*[Hh][Zz]' #regex to get GHz, Hz, THz, KHz, MHz


FREQ_MULT_DICT = {'HZ':1,'KHZ':1e3,'MHZ':1e6,'GHZ':1e9,'THZ':1e12}
INV_FREQ_MULT_DICT = {val:key for key,val in FREQ_MULT_DICT.items()}  #inverse of frequency multiplier dictionary

class TouchstoneEditor(object):
   '''
   @brief init arbitrary port touchstone class. This covers wave and S params
   @param[in] input_file - path of file to load in. 
               A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
               measurement with n ports and frequencies [f1,f2,...] 
   '''
   
   def __new__(cls,input_file,*args,**kwargs):
       '''
       @brief instantiator to return correct class (e.g. WnpEditor or SnpEditor)
       @note help from https://stackoverflow.com/questions/9143948/changing-the-class-type-of-a-class-after-inserted-data
       '''
       _,ext = os.path.splitext(input_file)
       if re.findall('w[\d]+p',ext):
           out_cls = WnpEditor
       elif re.findall('s[\d]+p',ext):
           out_cls = SnpEditor
       else:
           out_cls = cls
       instance = super().__new__(out_cls)
       return instance
       
       

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
            no_load - if True, do not immediatly load the file (default False)
            default_extension - default output file extension (e.g. snp,wnp)
        '''
        self.options = {}
        self.options['header'] = None #this will be set later
        self.options['comments'] = DEFAULT_COMMENTS
        self.options['read_header'] = True
        self.options['waves'] = ['A','B'] #waves to store. default to wave parameter
        self.options['plotter'] = None
        self.options['plot_options'] = {}
        self.options['no_load'] = False
        self.options['default_extension'] = 'tnp' #default
        for key,val in six.iteritems(arg_options): #overwrite defaults with inputs
            self.options[key] = val 
        #init plotter if not providied
        if self.options['plotter'] is None:
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
            
        if os.path.splitext(input_file)[-1] == '.meas':
            input_file = get_unperturbed_meas(input_file)
        #initialize dictionary of waves
        if self.param_class is None: #default to this
            self.param_class = TouchstoneParam #parameter class
        self.waves = dict()
        for w in self.options['waves']:
            self.waves[w] = dict()
        self._ports = [] #start with no ports
        #now load the file
        if not self.options['no_load']:
            if(type(input_file)==str):
                self.load(input_file,read_header=self.options['read_header'])
            elif(type(input_file)==tuple or type(input_file)==list):
                self.load_empty(input_file[0],input_file[1])
            
   def _gen_dict_keys(self):
       '''
       @brief function to generate the dictionary keys for each wave in self.waves
       @note dict keys are now generated from port list
       @note this should be redefined in inheriting classes
       @note the keys are placed in self.wave_dict_keys
       @return list of keys for the current ports
       '''
       keys = np.array([i*10+j for i in np.sort(self._ports) for j in np.sort(self._ports)])
       return keys
   
   @property
   def wave_dict_keys(self):
       '''
       @brief getter for wave_dict_keys after we switched to storing ports not keys (easier to add and remove)
       '''
       return self._gen_dict_keys()
   
   @property
   def num_ports(self):
       '''
       @brief quickly get number of ports. Got tired of typing this
       '''
       return len(self._ports)
            
   def load(self,input_file,**kwargs):
        '''
        @brief load a wave parameter file and parse into the class
        @param[in] input_file - path of file to load
        @param[in/OPT] - **kwargs - keyword arguements as follows:
                ftype  - type of file we are loading (e.g. 'text' or 'binary')
                read_header - whether or not to read the header and comments in text files. It is faster to not read the header/comments
        '''
        options = {}
        for k,v in kwargs.items():
            options[k] = v
        #if we default grab from end of file path
        ftype = options.get('ftype',None)
        if ftype is None:
            if(input_file.split('_')[-1]=='binary'):
                ftype='binary'
            else:
                ftype='text'
                
        #get the number of ports from the file extension
        file_ext = os.path.splitext(input_file)[-1]
        num_ports_from_filename = int(''.join(re.findall(r'\d',file_ext)))
        self._set_num_ports(num_ports_from_filename) #set the ports from the filename
        #now set our keys
        self._gen_dict_keys()
        
        #if we have a binary file (e.g. *.w2p_binary)
        if(ftype=='binary'):
            #first read the header
            raw_data = self._load_binary(input_file,**kwargs)  
        #if we have a text file (e.g. *.w2p)
        elif(ftype=='text'):
            raw_data = self._load_text(input_file,**kwargs)

        num_cols = np.size(raw_data,1) #get the number of columns     
        #now split the data (text and binary input should be formatted the same here)
        #first check if our file is named correctly
        num_ports_from_file = int(round(np.sqrt((num_cols-1)/(len(self.waves)*2)))) #int(round(np.sqrt((num_cols-1)/2))) for snp file wnp has a and b
        if(num_ports_from_file!=num_ports_from_filename): #just make sure file matches extension
            raise MalformedSnpError("Number of ports from extension does not match amount of data in file")
        
        if self.options['header'] is None: #if we dont have a header here, set the default
            self.set_header(DEFAULT_HEADER)
        
        #file is good if we make it here so continue to unpacking
        freqs = raw_data[:,0]*self._get_freq_mult() #extract our frequencies
        
        #now get the data for each port. This assumes that the keys are in the same order as the data (which they should be)
        for ki,k in enumerate(self.wave_dict_keys):
            for wi,w in enumerate(self.waves):
                idx = ki*len(self.waves)*2+(1+2*wi)
                data = raw_data[:,idx]+raw_data[:,idx+1]*1j
                self.waves[w][k] = self.param_class(np.array(freqs),np.array(data),plotter=self.options['plotter'])
        self.round_freq_lists() #round when we load (remove numerical rounding error)
    
   def _load_text(self,file_path,**kwargs):
       '''
       @brief internal function to load text snp/wnp file
       @param[in] file_path - path of text file to load
       @param[in/OPT] **kwargs - keyword args as follows:
           read_header - whether or not to read the header and comments in text files. 
                           It is faster to not read the header/comments
       '''
       
       #first read in comments
       if(kwargs.get('read_header',None)): #flag for reading header for speed
            with open(file_path,'r') as fp: 
                for line in fp:
                    if(line.strip()[0]=='#'):
                        self.set_header(line) #try and set it. If its not valid it wont be set
                    elif(line.strip()[0]=='!'):
                        self.options['comments'].append(line.strip()[1:])
                    else: #else its data
                        pass     
       else: #dont read comments
            self.options['comments'].append('Header and comments NOT read from file')
        #now read in data from the file with many possible delimiters in cases
        #of badly formated files
       with open(file_path) as fp:
            regex_str = r'[ ,|\t]+'
            rc = re.compile(regex_str)
            raw_data = np.loadtxt((rc.sub(' ',l) for l in fp),comments=['#','!']) 
            if raw_data.ndim==1: #case if we have 1 data point only
                raw_data = np.reshape(raw_data,(1,-1))
       return raw_data
       
   def _load_binary(self,file_path,**kwargs):
       '''
       @brief internal function to load binary snp/wnp file
       @param[in] file_path - path of binary file to load
       @param[in/OPT] **kwargs - keyword args as follows:
           None yet!
       '''
       [num_rows,num_cols] = np.fromfile(file_path,dtype=np.uint32,count=2) 
       raw_data = np.fromfile(file_path,dtype=np.float64) #read raw data
       raw_data = raw_data[1:] #remove header
       raw_data = raw_data.reshape((num_rows,num_cols)) #match the text output
       self.options['comments'] = ['Data read from binary file']
       return raw_data
   
   def set_header(self,header_str):
       '''
       @brief set our header string with some checks.
       @param[in] header_str - string of our header 
       '''
       header_str = re.sub('#','',header_str)
       freq_mult = self._get_freq_mult(header_str)
       if freq_mult is None:  #make sure we have a frequency in here
           return 
       self.options['header'] = header_str #set if we pass the checks
    
   def _get_freq_mult(self,header_str=None):
       '''
       @brief return a value of a frequency multiplier from a header (or string unit)
       @param[in/OPT] header_str - header to get multiplier from if none use self.options['header']
       @return a multiplier to get from the current units to Hz or None if no match is found
       '''
       if header_str is None:
           header_str = self.options['header']
       unit_strs = re.findall(HEADER_FREQ_REGEX,header_str)
       if unit_strs:
           mult = FREQ_MULT_DICT.get(unit_strs[0].upper(),None) #assume 1 match if any
       else:
           mult = None
       return mult
       
    
   def load_empty(self,num_ports,freqs):
        '''
        @brief create a WnpEditor class with all values as 0
        @param[in] num_ports - number of ports for the class
        @param[in] num_measurements - number of measurements per parameter (i.e. number of frequencies)
        '''
        self._set_num_ports(num_ports) #set the number of ports
        #now set our keys
        self._gen_dict_keys()
        if self.options['header'] is None: #allow override
            self.set_header(DEFAULT_EMPTY_HEADER) #set the default header
        #and pack the port data with 0s
        freqs = np.array(freqs)*self._get_freq_mult()
        for k in self.wave_dict_keys:
            for wave in self.waves.keys():
                self.waves[wave][k] = WnpParam(freqs,np.zeros(len(freqs)),plotter=self.options['plotter'])
        self.round_freq_lists()
        
   def _set_num_ports(self,num_ports):
       '''
       @brief set our ports provided a set number of ports. This will overwrite self._ports
       @param[in] num_ports - number of ports
       '''
       self._ports = np.arange(1,num_ports+1)
       
       
   def write(self,out_file,ftype='default',delimiter=' ',**kwargs):
        '''
        @brief write out data to touchstone (e.g. *.snp,*.wnp,*.tnp)
        @param[in] out_file - path of file name to write to. if *.[wts]np is the extension
            (e.g *.snp) the n will be replaced with the correct number of ports
        @param[in/OPT] ftype - type of file to write out ('default' will write to whatever extension out_file has)
        @param[in/OPT] delimiter - delimiter to use when writing text files (default is ' ')
        @param[in/OPT] **kwargs - keyword arguments as follows
            fix_extension - whether or not to fix the extension provided by out_file (default True)
                This ensures the output file extension is correct
        '''
        options = {}
        options['fix_extension'] = True
        for k,v in kwargs.items():
            options[k] = v
        
        if(ftype=='default'):
            if(re.findall('binary',os.path.splitext(out_file)[-1])):
                ftype='binary'
            else:
                ftype='text'
       
        #round frequencies to nearest Hz
        self.round_freq_lists()
        
        #make sure the frequency lists are equal before writing; just in case somthing went wrong
        self._verify_freq_lists()
        
        #clean the output filename
        fname,ext = os.path.splitext(out_file)
        if options['fix_extension']:
            if ext == '': # no extension provided
                ext = '.ext' #this will be replaced
            if ftype=='binary': #add binary if needed
                ext += '_binary'
            ext = re.sub('(?<=\.).*?((?=_binary)|$)',self.options['default_extension'],ext)
        ext = re.sub('(?<=[wst])n(?=p)',str(self.num_ports),ext) #replace if snp
        out_file = fname+ext
        
        #get our frequency multiplier
        freq_mult = self._get_freq_mult()
        
        #pack into correct data list
        #assume all parameters are same length
        if(ftype=='binary'):
            num_rows = len(self.w1[11].freq_list)
            temp_list = [self.w1[11].freq_list/freq_mult]
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
                #write our header (should just be a single string)
                fp.write('#%s\n' %(self.options['header']))
                #now write data
                for i in range(len(self.w1[self.wave_dict_keys[0]].raw)):
                    line_vals = [self.w1[self.wave_dict_keys[0]].freq_list[i]/freq_mult]
                    for k in self.wave_dict_keys:
                        for w in self.waves.values():
                            line_vals += [w[k].raw[i].real,w[k].raw[i].imag]
                    #write the line to the file. The upper ensures we get E not e
                    fp.write(delimiter.join([str(v).upper() for v in line_vals])+'\n')
                
        else:
            print('Write Type not implemented')
        return out_file
            
   def plot(self,keys='all',waves='all',data_type='mag_db'):
       '''
       @brief plot our wave or s parameter data
       @param[in/OPT] key - port of data to plot or list of ports to plot, or 'all'
       @param[in/OPT] waves - list of keys for self.waves to plot (default 'all')
       @param[in/OPT] data_type - type of data to plot (e.g. mag_db,phase,phase_d)
       '''
       # first our keys for 11,12,21,22,etc...
       if keys=='all': #check for all
           keys = self.wave_dict_keys
       if not hasattr(keys,'__iter__'): #check for single input
           keys = [keys]
       # now fix our wave input
       if waves=='all':
           waves = list(self.waves.keys())
       if not hasattr(waves,'__iter__'):
           waves = [waves]
       #now plot
       for w in waves:
           for k in keys:
               self.waves[w][k].plot(data_type)
           
            
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
                   
   def map_ports(self,port_map_dict):
       '''
       @brief map data between ports from a given mapping
       @param[in] port_map_dict - dictionary describing the move (e.g. {1:2,2:1})
       @note defining a map and not its inverse will delete data (e.g. {1:2} and not {1:2,2:1})
       '''   
       old_keys = self.wave_dict_keys #get the current keys
       new_keys = map_keys(old_keys,port_map_dict)
       #find the keys that changed
       diff_keys = old_keys!=new_keys
       diff_old_keys = old_keys[diff_keys]
       diff_new_keys = new_keys[diff_keys]
       #now correct the ports
       new_ports = []
       for p in self._ports:
           new_ports.append(port_map_dict.get(p,p))
       self._ports = np.sort(new_ports)
       #now lets correct the keys
       for wk in self.waves.keys():
           params = []
           for old_key in diff_old_keys:
               params.append(self.waves[wk].pop(old_key))
           for i,new_key in enumerate(diff_new_keys):
               self.waves[wk].update({new_key:params[i]})
               
   def swap_ports(self,port_a,port_b):
       '''
       @brief swap ports a and b
       @param[in] port_a - port to swap with port b
       @param[in] port_b - port to swap with port a
       '''
       self.map_ports({port_a:port_b,port_b:port_a})
       
   def delete_port(self,port_num): 
       '''
       @brief delete a port from the class
       @param[in] port_num - the number of the port to delete (must be less than self.num_ports)
           This will start at 1 not 0 indexing
       @todo MAKE THIS WORK
       '''
       if port_num not in self._ports:
           raise Exception("Port {} does not exist in this instance.".format(port_num))
       cur_ports = np.array(self._ports)
       orig_wdk = self.wave_dict_keys
       self._ports = cur_ports[cur_ports!=port_num] #remove the port number
       del_keys = orig_wdk[np.in1d(orig_wdk,self.wave_dict_keys,invert=True)] #get the added keys
       removed_waves = {}
       for wk in self.waves.keys():
           removed_waves[wk] = {}
           for k in del_keys:
               removed_waves[wk].update({k:self.waves[wk].pop(k)})
   
   def add_port(self,port_num):
       '''
       @brief add an empty port to the class
       @param[in] port_num - which port to add. Exception if it already exists
       '''
       orig_wdk = self.wave_dict_keys #original wave dict keys
       freqs = self.freq_list
       self._ports = np.sort(np.append(self._ports,[port_num])) #add the new port number
       new_keys = self.wave_dict_keys[np.in1d(self.wave_dict_keys,orig_wdk,invert=True)] #get the added keys
       for k in new_keys:
           for wk in self.waves.keys():
               self.waves[wk][k] = WnpParam(freqs,np.zeros(len(freqs)),plotter=self.options['plotter']) #add empty params

            
   def __getitem__(self,key):
        '''
        @brief override of [] operator to get S parameters
            This is a shortcut that will return freqeuncy/complex value data
        @param[in] key - key of A,B parameters to get
        @return [frequency_list,A_complex_values,B_complex_values] list of lists from the S parameter
        '''
        out_list =  [self.freq_list]
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
       num_ports_eq = self.num_ports==other.num_ports
       if(not num_ports_eq): #dont check more if number of ports arent equal
           return [num_ports_eq,self.num_ports,other.num_ports]
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
           raise AttributeError("Attribute '{}' does not exist and is not a key in self.waves".format(attr))
    
   @property
   def w1(self):
       '''
       @brief shortcut for first wave 
       '''
       return self.waves[list(self.waves.keys())[0]]
   
   @property
   def freq_list(self):
       '''
       @brief get the frequency list of the first dict key parameter (assume they all match)
       '''
       return self.w1[self.wave_dict_keys[0]].freq_list
    
   def _call_param_funct(self,fname,*args):
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
       self._call_param_funct('sort')
       
   def crop(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values outside a window
       '''
       self._call_param_funct('crop',lo_freq,hi_freq)
       
   def cut(self,lo_freq=0,hi_freq=1e60):
       '''
       @brief remove values inside a window
       '''
       self._call_param_funct('cut',lo_freq,hi_freq)
           
   def round_freq_lists(self):
       '''
       @brief round frequencies to nearest hz (assuming they are in GHz)
       '''
       self._call_param_funct('round_freq_list')
           
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
                self.waves[wk][k].freq_list += np.round(LO_freq)
                #now round the frequencies to nearest Hz
                self.waves[wk][k].round_freq_list()

class WnpEditor(TouchstoneEditor):
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
        options['waves'] = ['A','B'] #do s parameters
        options['default_extension'] = 'wnp'
        for k,v in arg_options.items():
            options[k] = v
        self.param_class = WnpParam
        super().__init__(input_file,**options)

class SnpEditor(TouchstoneEditor):
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
        options['default_extension'] = 'snp'
        for k,v in arg_options.items():
            options[k] = v
        self.param_class = SnpParam
        super().__init__(input_file,**options)

    def _gen_dict_keys(self,ports=None):
       '''
       @brief function to generate the dictionary keys for each wave in self.waves
       @param[in/OPT] ports - list of ports to make keys for. Defaults to range(1,num_ports+1) ports (e.g. [1,2] for num_ports=2)
       @note we will also sort the ports from lowest to highest
       @note this should be redefined in inheriting classes
       @note the keys are placed in self.wave_dict_keys
       '''
       #adding the additional self.options['waves']==['s'] here allows us to
       #extend this class and still use the wnp functionalily simply by
       #changing our 'waves' option to ['A','B']
       if (self.num_ports==2 and self.options['waves']==['S']):
           #because s2p files wanted to be special we have to reorder (e.g. [11,21,12,22]) 
           wdk = super()._gen_dict_keys()
           return  np.array([wdk[0],wdk[2],wdk[1],wdk[3]])
       else:
           return super()._gen_dict_keys() #otherwise use the generic
 

#acutally is the same as snpParam
class TouchstoneParam:
    '''
    @brief class for a single wave parameter (e.g. A[11])
    '''
    def __init__(self,freq_list,raw_list,**arg_options):
        '''
        @brief initialize our parameter
        @param[in] freq_list - list of frequencies for the parameter data
        @param[in] raw_list  - raw complex data for the parameter
        @param[in/OPT] arg_options - keyword arg options as follows
            plotter - SamuraiPlotter class to override if not available
            plot_options - dictionary of args to pass to SamuraiPlotter (if plotter not specified)
        '''
        self.options = {}
        self.options['plot_options'] = {'plot_order':['matplotlib']}
        self.options['plotter'] = None
        for k,v in arg_options.items():
            self.options[k] = v
        if self.options['plotter'] is None: #start up plotter if not provided
            self.options['plotter'] = SamuraiPlotter(**self.options['plot_options'])
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
        
    def plot(self,data_type='mag_db',**arg_options):
        '''
        @brief plot parameter data and return the figure
        @param[in/OPT] data_type - type of data to plot. 'mag_db','mag','phase','phase_d','raw' possible
        '''
        data = getattr(self,data_type)
        rv = self.options['plotter'].plot(self.freq_list,data,xlabel='Freq (GHz)',ylabel=data_type,**arg_options)
        return rv
        
    #crop out all frequencies outside a window given by lo and hi frequencies (in Hz)
    def crop(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove all frequencies and their corresponding values outside a given window
        '''
        lo_val = np.round(lo_freq)
        hi_val = np.round(hi_freq)
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
        lo_val = np.round(lo_freq)
        hi_val = np.round(hi_freq)
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
        @brief round frequency list to nearest hz assuming values are in Hz
        '''
        #assume frequency values are in GHz and we round to Hz
        self.freq_list=np.round(self.freq_list,decimals=0)
    
    #put new values into the class
    def update(self,freq_list,raw_list):
        '''
        @brief put new values into the class
        @param[in] freq_list - list of frequencies for the parameter data
        @param[in] raw_list  - raw complex data for the parameter
        '''
        self.freq_list = freq_list
        self.raw = raw_list
        
    def get_value_from_frequency(self,freq):
        '''
        @brief get a raw value from a provided frequency
            if the exact frequency is not found, the closest will be provided
        @param[in] freq - frequency (in Hz) to get the value of
        '''
        fm = np.abs(freq-self.freq_list)
        return self.raw[np.argmin(fm)]
        
    def calculate_time_domain_data(self):
        '''
        @brief calculate the time domain data
        @todo. Verify the lack of ifftshift here is correct for phases...
        @return [time domain values,ifft complex values]
        '''
        ifft_vals = np.fft.ifft(self.raw)
        total_time = 1/np.diff(self.freq_list).mean()
        times = np.linspace(0,total_time,self.freq_list.shape[0])
        return times,ifft_vals
    
    @property
    def mag_db(self):
        '''
        @brief get the magnitude in db (20*log10(mag_lin))
        '''
        return 20*np.log10(self.mag)
    
    @property
    def mag(self):
        '''
        @brief property for magnitude
        @return list of magnitude data
        '''
        return np.abs(self.raw)

    @property
    def phase(self):
        '''
        @brief property for phase in radians
        @return list of phase data in radians
        '''
        return np.angle(self.raw)

    @property
    def phase_d(self):
        '''
        @brief property for phase in degrees
        @return list of phase data in degrees
        '''
        return np.angle(self.raw)*180/np.pi
    
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
    
class WnpParam(TouchstoneParam):
     
    def __init__(self,freq_list,raw_list,**arg_options):
        super().__init__(freq_list,raw_list,**arg_options)   
        
class SnpParam(TouchstoneParam):
     
    def __init__(self,freq_list,raw_list,**arg_options):
        super().__init__(freq_list,raw_list,**arg_options)
         
             
#sl = s2pEditor('U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Cable_Drift/5-18-2018_stretchRepeats/processed/preCal/short_load.s2p')
#get unperturbed result from .meas file
def get_unperturbed_meas(fname):
    dom = parse(fname)
    msp = dom.getElementsByTagName('MeasSParams').item(0)
    unpt = msp.getElementsByTagName('Item').item(0)
    unpt_name = unpt.getElementsByTagName('SubItem').item(1).getAttribute('Text')
    return unpt_name


class TouchstoneError(Exception):
    '''
    @brief custom exception for errors in touchstone handling
    '''
    def __init__(self,err_msg):
        self.err_msg = err_msg
    def __str__(self):
        return repr("SnP/WnP ERROR: %s" %(self.err_msg)) 
    
class SnpError(TouchstoneError):
    pass
    
class MalformedSnpError(SnpError):
    '''
    @brief snp/wnp file is not formed correctly error
    '''
    def __init__(self,err_msg):
        super().__init__(err_msg)
        
def swap_ports(*args,**kwargs):
    '''
    @brief swap port n between just 2 2 port files (for now)
    @param[in] *args - the SnpEditor objects to swap
    '''
    #load in the data
    s1 = args[0]
    s2 = args[1]
    freqs = s1.freq_list
    #assume frequency lists are equal
    if np.all(freqs != s2.freq_list):
        raise SnpError('Frequency lists do not match')
    so1 = SnpEditor([2,freqs])
    so2 = SnpEditor([2,freqs])
    so1.S[11] = s1.S[11]; so1.S[22] = s2.S[22]
    so2.S[11] = s2.S[11]; so2.S[22] = s1.S[22]
    return so1,so2
    

        
def map_keys(key_list,mapping_dict):
    '''
    @brief change a set of keys (e.g. [11,31,13,33]) based on a mapping dict
    @param[in] key_list - list of keys for S/WnpParams (e.g. [11,31,13,33])
    @param[in] mapping_dict - how to map ports (e.g. {3:2,1:4})
    '''
    new_key_list = []
    for key in key_list:
        new_key = int(0)
        trans_key = int(key)
        i = 1
        while(trans_key>=1):
            cur_val = int(trans_key%10)
            new_val = mapping_dict.get(cur_val,cur_val)
            new_key+=new_val*i
            trans_key = int(trans_key)/int(10)
            i*=10
        new_key_list.append(new_key)
    return np.array(new_key_list)
    

if __name__=='__main__':

    snp_test = False
    wnp_test = False
    key_test = False
    swap_test = False
    add_remove_test = False
    new_method_test = True
    
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
        print(wnp_bin==wnp_text)
    if snp_test:
        print("Loading *.snp files")
        snp_text_path = os.path.join(dir_path,'test.s2p')
        snp_bin_path  = os.path.join(dir_path,'test.s2p_binary')
        snp_text = SnpEditor(snp_text_path)
        snp_bin  = SnpEditor(snp_bin_path)
        print(snp_bin==snp_text)
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
        
    if key_test:
        keys = [11,31,13,33]
        mapping = {3:2}
        print(keys)
        new_keys = map_keys(keys,mapping)
        print(new_keys)
        
    if swap_test:
        f1 = os.path.join(dir_path,'test.s2p')
        f2 = os.path.join(dir_path,'test.s2p_binary')
        s1 = SnpEditor(f1)
        s2 = SnpEditor(f2)
        so1,so2 = swap_ports(s1,s2)
        print(so1 == s1)
        print(so2 == s2)
        s1c = SnpEditor(f1)
        s1.swap_ports(1,2)
        s1.swap_ports(1,2)
        print(s1==s1c)
        
    if add_remove_test:
        f1 = os.path.join(dir_path,'test.s2p')
        f2 = os.path.join(dir_path,'test.s2p_binary')
        s1 = SnpEditor(f1)
        s2 = SnpEditor(f2)
        s1.swap_ports(1,2)
        #s1.add_port(3)
        print(s1.S)
        rw = s1.delete_port(1)
        print(s1.S)
        rw = s1.add_port(1)
        
    if new_method_test:
        wnp_text_path = os.path.join(dir_path,'test.w2p')
        wnp_bin_path  = os.path.join(dir_path,'test.w2p_binary')
        w1 = TouchstoneEditor(wnp_text_path)
        w2 = TouchstoneEditor(wnp_bin_path)
        print(w1.__class__)
        print(w2.__class__)
        snp_text_path = os.path.join(dir_path,'test.s2p')
        snp_bin_path  = os.path.join(dir_path,'test.s2p_binary')
        s1 = TouchstoneEditor(snp_text_path)
        s2 = TouchstoneEditor(snp_bin_path)
        
        print(s1.__class__)
        print(s2.__class__)
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        