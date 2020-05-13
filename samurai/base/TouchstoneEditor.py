# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 11:02:53 2018
edit .snp files (.s2p,.s4p,etc...)
@author: ajw5
"""
import os
import numpy as np
import pandas as pd
import copy
import re
import operator
from functools import reduce
from xml.dom.minidom import parse 
import warnings

from samurai.base.SamuraiDict import SamuraiDict

from samurai.base.generic import deprecated
from samurai.base.generic import moving_average

import plotly.graph_objs as go

#hamming window
import scipy.signal.windows

DEFAULT_EMPTY_HEADER = 'GHz S RI 50' #Ghz default because thats all the MUF recognizes
DEFAULT_HEADER       = 'GHz S RI 50'
DEFAULT_HEADER_TIME  = 'ns S RI 50'
DEFAULT_HEADER_ANG   = 'deg S RI 50'
DEFAULT_COMMENTS = []
HEADER_FREQ_REGEX = '[KMGT]*[Hh][Zz]' #regex to get GHz, Hz, THz, KHz, MHz
HEADER_TIME_REGEX = '[NnUuMm]*[Ss]' #ns,us,ms,s
HEADER_ANG_REGEX = '([Rr][Aa][Dd]|[Dd][Ee][Gg])' #rad,deg
HEADER_REGEX = '({}|{}|{})'.format(HEADER_FREQ_REGEX,HEADER_TIME_REGEX,HEADER_ANG_REGEX)


FREQ_MULT_DICT = {'HZ':1,'KHZ':1e3,'MHZ':1e6,'GHZ':1e9,'THZ':1e12}
TIME_MULT_DICT = {'NS':1e-9,'US':1e-6,'MS':1e-3,'S':1} #time domain for waveforms always convert to seconds
ANG_MULT_DICT  = {'DEG':1,'RAD':180/np.pi} #angular conversion
MULT_DICT = dict(**FREQ_MULT_DICT,**TIME_MULT_DICT,**ANG_MULT_DICT) #combine the dictionaries
INV_MULT_DICT = {val:key for key,val in MULT_DICT.items()}  #inverse of frequency multiplier dictionary

#%% Some useful functions
def get_unperturbed_meas(fname):
    '''
    @brief get the path of the unperturbed (nominal) measurement from a *.meas file
    @param[in] fname - path to the *.meas file
    '''
    wdir = os.path.dirname(fname)
    dom = parse(fname)
    msp = dom.getElementsByTagName('MeasSParams').item(0)
    unpt = msp.getElementsByTagName('Item').item(0)
    unpt_name = unpt.getElementsByTagName('SubItem').item(1).getAttribute('Text')
    unpt_path = os.path.join(wdir,unpt_name)
    return unpt_path

def swap_ports(*args,**kwargs):
    '''
    @brief swap port n between just 2 2 port files (for now)  
    @param[in] args - the SnpEditor objects to swap  
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
    so1.S11[:] = s1.S11; so1.S22[:] = s2.S22
    so1.S21[:] = s1.S21; so1.S12[:] = s2.S12
    so2.S11[:] = s2.S11; so2.S22[:] = s1.S22
    so2.S21[:] = s2.S21; so2.S12[:] = s1.S12
    return so1,so2

def combine_parameters(*args,**kwargs):
    '''
    @brief Combine touchstone files into one with a number of ports
        equal to the sum of the ports of the combined files
    @param[in] args - paths or TouchstoneEditor objects to combine. 
        These must all be of the same class (e.g. SnpEditor) and have the same frequencies
    @param[in/OPT] kwargs - keyword arguments as follows:
        - fill_value - what value to fill undefined parameters (default 0+0j)
        - out_path - directory to write the file to. If None just return the TouchstoneEditor object
    @note This currenlty assumes that ports are consecutive (e.g. 11,12,21,22 NOT 11,13,31,33)
    @note This only supports up to 10 ports
    '''
    options = {}
    options['fill_value'] = 0+0j
    options['out_path'] = None
    for k,v in kwargs.items():
        options[k] = v
    #load the data if a string was passed in
    editors = list(args) 
    for i,ed in enumerate(editors):
        if isinstance(ed,str): 
            editors[i] = TouchstoneEditor(ed)
    #get the class type
    myclass = type(editors[0])
    #verify they are the same class type (same waves)
    editor_type = [type(ed) for ed in editors]
    if not all([et==myclass for et in editor_type]): #check all values are the same type
        raise TypeError("All inputs must be of the same type (currently {})".format(editor_type))
    #now lets make sure frequency lists match
    if not np.all([np.all(editors[0].freq_list==ed.freq_list) for ed in editors]):
        raise TouchstoneError("Cannot combine. Frequencies must match")
    #get the sum of all the ports and the frequency list
    freq_list = editors[0].freq_list
    total_ports = np.sum([ed.num_ports for ed in editors])
    #now create a new editor to copy into
    new_editor = myclass([total_ports,freq_list],header=editors[0].options['header'])
    new_editor.raw = options['fill_value']
    port_count = 0 #current ports
    for ed in editors:
        in_keys = ed.wave_dict_keys
        out_keys = in_keys+(port_count+port_count*10) #add 11,22,etc to get correct port numbers
        port_count += ed.num_ports
        for wk in new_editor.waves:
            for ik,ok in zip(in_keys,out_keys):
                new_editor[(wk,ok)][:] = ed[(wk,ik)] #copy the raw data
    if options['out_path'] is None:
        return new_editor       
    else:
        out_path = new_editor.write(options['out_path'])
        return out_path
    
def split_parameters(meas,split,**kwargs):
    '''
    @brief split a TouchstoneEditor into multiple editors
    @param[in] meas - measurement path or object to split
    @param[in] split - definition of how to split. For now split into n equal parts
    @param[in] kwargs - keyword args as follows:
        - out_path - formattable output path (e.g. 'split_{}') to write split values to. If None, return objects
    @example
        fpath = 'path/to/file.s2p'
        out1,out2 = split_measurements(fpath)
    @note This only supports up to 10 ports
    '''
    options = {}
    options['out_path'] = None
    for k,v in kwargs.items(): #load kwargs
        options[k] = v
    if isinstance(meas,str): #check if its a path
        meas = TouchstoneEditor(meas)
    freqs = meas.freq_list #get our frequencies
    ports_per_split = meas.num_ports/split
    if not ports_per_split == int(ports_per_split): #check for even divisibility
        raise TouchstoneError("Number of ports ({}) not evenly divisible by {}".format(meas.num_ports,split))
    ports_per_split = int(ports_per_split) #change to integer
    out_editors = [type(meas)([ports_per_split,freqs],header=meas.options['header']) for i in range(split)] #create n output editors
    #now populate the output editors from the input
    port_count = 0 #current ports
    for oed in out_editors:
        in_keys = oed.wave_dict_keys+(port_count*10+port_count) #e.g. key+22
        out_keys = oed.wave_dict_keys #add 11,22,etc to get correct port numbers
        port_count += oed.num_ports
        for wk in oed.waves:
            for ik,ok in zip(in_keys,out_keys):
                oed[(wk,ok)][:] = meas[(wk,ik)] #copy the raw data
    #now write out
    if options['out_path'] is None:
        return out_editors 
    else:
        out_paths = [ed.write(options['out_path'].format(i)) for i,ed in enumerate(out_editors)]
        return out_paths
    
def ifft(data,window=None):
    '''
    @brief calculate the time domain data
    @todo Verify the lack of ifftshift here is correct for phases... 
    @param[in] data - data as a TouchstoneParam/Editor
    @param[in/OPT] window - what window to apply. can be 'sinc2' for sinc 
        squared or any input of first arg to of scipy.signal.windows.get_window (e.g. 'hamming', ('chebwin',100)),
        or a callable with input (len(self.raw))
    @return WaveformEditor with time domain data
    '''
    if window is None:
        wvals = np.ones(len(data))
    elif window == 'sinc2': #apply a sinc^2 window (0 at edges)
        wvals = np.linspace(-1,1,len(data))
        wvals = np.sinc(wvals)**2
    elif callable(window):
        wvals = window(len(data))
    else: #assume its a call to scipy.signal.windows.get_window
        wvals = scipy.signal.windows.get_window(window,len(data))
    wdata = data*np.reshape(wvals,tuple([len(wvals)]+[-1]*(np.ndim(data)-1)))
    ifft_vals = np.fft.ifft(wdata,axis=0)
    total_time = 1/np.diff(data.freqs).mean()
    times = np.linspace(0,total_time,len(data))
    #not the cleanest but it works
    if isinstance(data,TouchstoneEditor): #TouchstoneEditor
        num_ports = data.num_ports
        myw = WaveformEditor([num_ports,times])
    else: #TouchstoneParam
         myw = WaveformParam(index=times)
    myw[:] = np.reshape(ifft_vals,tuple([len(ifft_vals)]+[-1]*(np.ndim(myw)-1)))
    return myw


#%% Parsing for files with data on multiple lines
class MultilineFileParser(object):
    '''
    @brief Class for parsing files with more ports than 2 (e.g. *.s4p)
    @author bfj
    '''
    commentList = ['#', '!']
    def __init__(self, dataFile):
        self.dataFile = dataFile

        # Comments at the beginning of the file only
        self.pastComments = False

        self.fid = open(self.dataFile, 'r')

        self.cachedLine = None

    def is_comment(self, char):
        return char in self.commentList

    def readline(self):
        if self.cachedLine is None:
            return self.fid.readline()
        else:
            cLine = self.cachedLine
            self.cachedLine = None
            return cLine

    def get_multiline(self):
        dataStr = self.readline().strip('\n')

        if not self.pastComments:
            while (self.is_comment(dataStr[0])):
                dataStr = self.readline().strip('\n')
            self.pastComments = True

        numCols = len(dataStr.split())
        # Read a new line
        rLine = self.readline().strip('\n')

        while (not len(rLine.split()) == numCols) and not rLine == '':
            dataStr += ' ' + rLine
            rLine = self.readline().strip('\n')

        # We always read too many lines
        self.cachedLine = rLine

        return dataStr

    def __iter__(self):
        return self

    def __next__(self):
        data = self.get_multiline()
        if not data == '':
            return data
        else:
            raise StopIteration()
            
#%% IO Functions for touchstone files
def read_text_touchstone(file_path,**kwargs):
    '''
    @brief Load snp/wnp file data to a table (just like the data is stored in the file)
    @param[in] file_path - path of text file to load  
    @param[in/OPT] kwargs - keyword args as follows:  
        - read_header - whether or not to read the header and comments in text files.
                        It is faster to not read the header/comments  
    @return Dictionary with elements {'data':raw_data,'header':header_string,'comments':['list','of','comments']}
    '''
    #first read in comments
    comments = []
    header = DEFAULT_HEADER
    if(kwargs.get('read_header',None)): #flag for reading header for speed
         with open(file_path,'r') as fp: 
             for line in fp:
                 if(line.strip()[0]=='#'):
                     header = line
                     #self.set_header(line) #try and set it. If its not valid it wont be set
                 elif(line.strip()[0]=='!'):
                     comments.append(line.strip()[1:])
                 else: #else its data
                     pass     
    else: #dont read comments
         comments.append('Header and comments NOT read from file')
    #now read in data from the file with many possible delimiters in cases
    #of badly formated files
    fp = MultilineFileParser(file_path)
    regex_str = r'[ ,|\t]+'
    rc = re.compile(regex_str)
    raw_data = np.loadtxt((rc.sub(' ',l) for l in fp),comments=['#','!']) 
    if raw_data.ndim==1: #case if we have 1 data point only
        raw_data = np.reshape(raw_data,(1,-1))
    return {'data':raw_data,'header':header,'comments':comments}
        
def read_binary_touchstone(file_path):
    '''
    @brief Function to load binary snp/wnp file  
    @param[in] file_path - path of binary file to load  
    @param[in/OPT] kwargs - keyword args as follows:  
    '''
    [num_rows,num_cols] = np.fromfile(file_path,dtype=np.uint32,count=2) 
    raw_data = np.fromfile(file_path,dtype=np.float64) #read raw data
    raw_data = raw_data[1:] #remove header
    raw_data = raw_data.reshape((num_rows,num_cols)) #match the text output
    comments = ['Data read from binary file']
    return {'data':raw_data,'header':DEFAULT_HEADER,'comments':comments}

#%% actual file manipulation class
class TouchstoneEditor(pd.DataFrame):
    '''
    @brief Load and handle arbitrary port touchstone class. This covers wave and S params  
    @author ajw5
    @note This inherits from a pandas dataframe for easy usage
    @param[in] args - input arguments can be: 
        - path of file to load in. 
        - A tuple (n,[f1,f2,....]) or list [n,[f1,f2,....]] can also be passed to create an empty 
                measurement with n ports and frequencies [f1,f2,...] 
        - A typical pandas dataframe constructor
    @note This can also be called as the typical constructor of a pandas DataFrame
    @param[in] arg_options - keywor arguments as follows:  
        - header - header to write out to the file (text only)  
        - comments - comments to write to file (text only)  
        - read_header - True/False whether or not to read in header from text files (faster if false, default to true)  
        - waves - list of what waves we are measuring for self.waves dictionary (default ['A','B'] for s params should be ['S'])  
        - no_load - if True, do not immediatly load the file (default False)  
        - default_extension - default output file extension (e.g. snp,wnp)  
    '''
    
    # normal properties
    _metadata = ['options','_ports']
    
    def __new__(cls,*args,**kwargs):

        '''
        @brief instantiator to return correct class (e.g. WnpEditor or SnpEditor)  
        @param[in/OPT] kwargs - keyword arguments. most passed to init but the following:
            override_extension_check - prevent the class from being changed due to extension  
        @note help from https://stackoverflow.com/questions/9143948/changing-the-class-type-of-a-class-after-inserted-data  
        '''
        
        if not len(args): #if empty, add an argument
            args = (None,) 
        override_extension_check = kwargs.pop('override_extension_check',None)
        if not override_extension_check: #we can override this new set for certain cases
            if isinstance(args[0],str): #this could be a list for an empty object
                input_file = args[0]
                _,ext = os.path.splitext(input_file)
                if re.findall('meas',ext):
                    input_file = get_unperturbed_meas(input_file)
                    _,ext = os.path.splitext(input_file)
                if re.findall('w[\d]+p',ext):
                    out_cls = WnpEditor
                elif re.findall('s[\d]+p',ext):
                    out_cls = SnpEditor
                elif re.findall('waveform',ext):
                    out_cls = WaveformEditor
                elif re.findall('beamform',ext):
                    out_cls = BeamformEditor
                elif re.findall('switch',ext):
                    out_cls = SnpEditor
                else:
                    out_cls = cls
            else: #if its a list, return whatever it was instantiated as
                out_cls = cls 
        else: #if we override return whatever it is defined as
            out_cls = cls
        instance = super().__new__(out_cls)
        if out_cls != cls: #run the init if it hasn't yet
            instance.__init__(*args,**kwargs)
        return instance
    
    
    def __init__(self,*args,**kwargs):
         '''@brief Constructor'''
         option_keys = ['header'      ,'comments'                     ,'read_header',
                        'waves'  ,'no_load','default_extension','param_class']
         option_vals = [DEFAULT_HEADER,copy.deepcopy(DEFAULT_COMMENTS),True,
                        ['A','B'],False    ,'tnp'              ,TouchstoneParam]
         self.options = {}
         for key,val in zip(option_keys,option_vals): #extract our options
             self.options[key] = kwargs.pop(key,val) #default value
         if not len(args): #if empty, add an argument
            args = (None,)
         # Extract important arguments if we are building in a special way
         if isinstance(args[0],str): # if its a string assume its a file path
             input_file = args[0]; args = tuple(list(args[1:]))
         elif isinstance(args[0],tuple) or isinstance(args[0],list):
             if np.ndim(args[0]) and len(args[0])==2 and np.isscalar(args[0][0]): #then assume its a port setup
                 input_file = args[0]; args = tuple(list(args[1:]))
         else: #otherwise its probably a DataFrame setup
             input_file = None
         #initialize the dataframe
         self._ports = [] #start with no ports
         freqs = kwargs.pop('freqs',None)
         if freqs is not None:
             kwargs['index'] = freqs
         #now lets not pass any unused args to dataframe to prevent errors
         #and then initialize the dataframe (super())
         dframe_kwarg_names = ['data','index','columns','dtype','copy']
         dframe_kwargs = {}
         unused_kwarg_label = 'Unused Keyword Argument'
         for kname in dframe_kwarg_names:
             kwarg_value = kwargs.pop(kname,unused_kwarg_label)
             if kwarg_value is not unused_kwarg_label:
                 dframe_kwargs[kname] = kwarg_value
         super().__init__(*args,**dframe_kwargs)
         #now load the file
         if not self.options['no_load']:
             if(isinstance(input_file,str)): #if its a string, load a file
                 self.read(input_file,read_header=self.options['read_header'])
             elif(isinstance(input_file,tuple) or isinstance(input_file,list)):
                 self._create_empty(input_file[0],input_file[1])
             elif input_file is None: #try and guess the number of ports
                 pass

    def _gen_dict_keys(self):
        '''
        @brief function to generate the dictionary keys for each wave in self.waves  
        @note dict keys are now generated from port list  
        @note this should be redefined in inheriting classes  
        @note the keys are placed in self.wave_dict_keys  
        @return list of keys for the current ports  
        @example
        >>> mys2p._gen_dict_keys()  
        array([11, 21, 12, 22])  
        >>> myw2p._gen_dict_keys()  
        array([11, 21, 12, 22])
        '''
        keys = np.array([i*10+j for i in np.sort(self._ports) for j in np.sort(self._ports)])
        return keys
    

             
    def read(self,input_file,round_freqs=True,**kwargs):
         '''
         @brief Read in a wave parameter file and parse into the class  
         @param[in] input_file - path of file to load  
         @param[in] round_freqs - round frequency indices (default True)
         @param[in/OPT] - kwargs - keyword arguements as follows:  
                 - ftype  - type of file we are loading (e.g. 'text' or 'binary')  
                 - read_header - whether or not to read the header and comments in text files. It is faster to not read the header/comments
         '''
         options = {}
         for k,v in kwargs.items():
             options[k] = v
         
         #if its a *.meas file get the nominal solution
         ext = os.path.splitext(input_file)[-1]
         if ext == '.meas': 
             input_file = get_unperturbed_meas(input_file)
         
         #if we default grab from end of file path
         ftype = options.get('ftype',None)
         if ftype is None:
             if(input_file.split('_')[-1]=='binary'):
                 ftype='binary'
             else:
                 ftype='text'
                 
         #get the number of ports from the file extension
         file_ext = os.path.splitext(input_file)[-1]
         num_ports_from_filename_str = ''.join(re.findall(r'\d',file_ext))
         if num_ports_from_filename_str == '': #if not specified assume 1
             num_ports_from_filename_str = '1' 
         num_ports_from_filename = int(num_ports_from_filename_str)
         self._set_num_ports(num_ports_from_filename) #set the ports from the filename
         #now set our keys
         self._gen_dict_keys()
         
         #if we have a binary file (e.g. *.w2p_binary)
         if(ftype=='binary'):
             #first read the header
             loaded_data = read_binary_touchstone(input_file)  
         #if we have a text file (e.g. *.w2p)
         elif(ftype=='text'):
             loaded_data = read_text_touchstone(input_file,**kwargs)
             
         #now set the variables from the loaded data
         raw_data = loaded_data['data']
         self.set_header(loaded_data['header'])
         self.options['comments'] = loaded_data['comments']
         num_cols = np.size(raw_data,1) #get the number of columns     
 
         # check if our file is named correctly
         num_ports_from_file = int(round(np.sqrt((num_cols-1)/(len(self.waves)*2)))) #int(round(np.sqrt((num_cols-1)/2))) for snp file wnp has a and b
         if(num_ports_from_file!=num_ports_from_filename): #just make sure file matches extension
             raise MalformedSnpError("Number of ports from extension does not match amount of data in file")
         
         if self.options['header'] is None: #if we dont have a header here, set the default
             self.set_header(DEFAULT_HEADER)
             
         freqs = raw_data[:,0]*self._get_freq_mult() #set our frequencies from the raw data
         # create an empty dataframe to store the data
         self._create_empty(num_ports_from_file,freqs)
         
         #file is good if we make it here so continue to unpacking
         self._extract_data(raw_data)
         
         if round_freqs:
             self.round_freq_list()
         
    # also alias to load
    load = read
     
    def write(self,out_file,ftype='default',delimiter=' ',round_freqs=True,**kwargs):
         '''
         @brief write out data to touchstone (e.g. *.snp,*.wnp,*.tnp)  
         @param[in] out_file - path of file name to write to. if *.[wts]np is the extension
             (e.g *.snp) the n will be replaced with the correct number of ports  
         @param[in/OPT] ftype - type of file to write out ('default' will write to whatever extension out_file has)  
         @param[in/OPT] delimiter - delimiter to use when writing text files (default is ' ')  
         @param[in/OPT] round_freqs - round our frequency list to the nearest hz
         @param[in/OPT] kwargs - keyword arguments as follows  
             - fix_extension - whether or not to fix the extension provided by out_file (default True)
                 This ensures the output file extension is correct  
         '''
         options = {}
         options['fix_extension'] = True
         for k,v in kwargs.items():
             options[k] = v
         
         if(ftype=='default'):
             if not (re.findall('binary',os.path.splitext(out_file)[-1])):
                 ftype='text'
             else:
                 ftype='binary'
                 
         comments = self.options['comments']
         header   = self.options['header']
       
         #round frequencies to nearest Hz
         if round_freqs:
             self.round_freq_list() #issue when using Waveforms with time
         
         #clean the output filename
         fname,ext = os.path.splitext(out_file)
         if options['fix_extension']: #just replace the extension with the correct one
             ext = '.ext' #this will be replaced
             if ftype=='binary': #add binary if needed
                 ext += '_binary'
             ext = re.sub('(?<=\.).*?((?=_binary)|$)',self.options['default_extension'],ext)
         ext = re.sub('(?<=[wst])n(?=p)',str(self.num_ports),ext) #replace if snp
         out_file = fname+ext
         
         #get our frequency multiplier
         freq_mult = self._get_freq_mult()
         
         #pack into correct data  array
         out_data = np.ndarray((self.shape[0],self.shape[1]*2+1),dtype=np.double)
         out_data[:,0] = self.freqs/freq_mult
         out_data[:,1::2] = self.raw.real 
         out_data[:,2::2] = self.raw.imag
         
         if(ftype=='binary'): # Write to binary file             
             with open(out_file,'wb') as fp:
                 num_rows = len(self.freqs)
                 num_cols = len(self.wave_dict_keys)*len(self.waves)*2+1
                 np.array([num_rows,num_cols],dtype=np.uint32).tofile(fp)
                 out_data.tofile(fp)
                 
         elif(ftype=='text'): #write to text file
             with open(out_file,'w+') as fp:
                 #write our comments
                 if type(comments) is not list: #assume if its not a list ts a string
                     comments = [comments]
                 for i in range(len(comments)):
                     fp.write('!%s\n' %(comments[i]))
                 #write our header (should just be a single string)
                 fp.write('#%s\n' %(header))
                 #now write out our data
                 for line_data in out_data:
                     #str(dat).upper is used here because '{:G}'.format gives weird amount of precision
                     fp.write(delimiter.join([str(dat).upper() for dat in line_data])+'\n')
                 
         else:
             print('Write Type not implemented')
         return out_file
         
    def _extract_data(self,raw_data):
        '''
        @brief class to extract data from raw data. This can be overriden for special cases  
        @note if not overriden this points to the same data as in self._raw  
        '''
        #now get the data for each port. This assumes that the keys are in the same order as the data (which they should be)
        for wi,w in enumerate(self.waves):
            for ki,k in enumerate(self.wave_dict_keys):
                idx = ki*len(self.waves)*2+(1+2*wi)
                data = raw_data[:,idx]+raw_data[:,idx+1]*1j
                #extract to self._raw
                self[(w,k)] = data
                
        #self.round_freq_list() #round when we load (remove numerical rounding error)
    
    def _create_empty(self,num_ports,freqs):
        '''
        @brief create a WnpEditor class with all NaNs
        @param[in] num_ports - number of ports for the class  
        @param[in] num_measurements - number of measurements per parameter (i.e. number of frequencies)  
        '''
        self._set_num_ports(num_ports) #set the number of ports
        #now set our keys
        self._gen_dict_keys()
        if self.options['header'] is None: #allow override
            self.set_header(DEFAULT_EMPTY_HEADER) #set the default header
        #and pack the port data with 0s
        # this will alternate waves like the data is in the file to prevent copy
        wave_column_list = self.options['waves']*len(self.wave_dict_keys)
        key_column_list = np.repeat(self.wave_dict_keys,len(self.options['waves']))
        columns = [wave_column_list,key_column_list]
        super().__init__(columns=columns,index=pd.Index(freqs,name='frequency'),dtype=np.cdouble)
        #self.round_freq_list()
    
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
        @example  
        >>> mys2p._get_freq_mult()
        1000000000.0
        >>> mys2p._get_freq_mult('KHz')
        1000.0
        '''
        if header_str is None:
            header_str = self.options['header']
        unit_strs = re.findall(HEADER_REGEX,header_str)[0]
        if unit_strs:
            mult = MULT_DICT.get(unit_strs[0].upper(),None) #assume 1 match if any
        else:
            mult = None
        return mult
         
    def _set_num_ports(self,num_ports):
        '''
        @brief set our ports provided a set number of ports. This will overwrite self._ports  
        @param[in] num_ports - number of ports  
        '''
        self._ports = np.arange(1,num_ports+1)
        
             
    def plot_plotly(self,keys='all',waves='all',data_type='mag_db',**arg_options):
        '''
        @brief plot our wave or s parameter data using plotly. Placeholder until pandas implements
            plotly as a backedn plotting enging (they say next release)
        @param[in/OPT] key - port of data to plot or list of ports to plot, or 'all'  
        @param[in/OPT] waves - list of keys for self.waves to plot (default 'all')  
        @param[in/OPT] data_type - type of data to plot (e.g. mag_db,phase,phase_d)  
        @param[in/OPT] arg_options - keywrod args passed to go.Figure() 
        '''
        # first our keys for 11,12,21,22,etc...
        if keys=='all': #check for all
            keys = self.wave_dict_keys
        if not hasattr(keys,'__iter__'): #check for single input
            keys = [keys]
        # now fix our wave input
        if waves=='all':
            waves = list(self.waves)
        if not hasattr(waves,'__iter__'):
            waves = [waves]
        #now plot
        fig = go.Figure(**arg_options)
        traces = []
        for w in waves:
            for k in keys:
               trace = self[w][k].plot_plotly(data_type,trace_only=True,name='{}{}'.format(w,k))
               fig.add_trace(trace)
        return fig
                    
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
        #now lets correct the keys
        for wk in self.waves:
            params = []
            for old_key in diff_old_keys:
                params.append(copy.deepcopy(self[wk][old_key])) #make a temporary copy of the data
            for i,new_key in enumerate(diff_new_keys):
                self[(wk,new_key)][:] = params[i]
                
    def swap_ports(self,port_a,port_b):
        '''
        @brief swap ports a and b  
        @param[in] port_a - port to swap with port b  
        @param[in] port_b - port to swap with port a  
        '''
        self.map_ports({port_a:port_b,port_b:port_a})   
    
    @deprecated("Use self.apply(funct,raw=True,args=*args,**kwargs) method")
    def run_function_on_data(self,funct,*args,**kwargs):
        '''
        @brief run a function on each of our param raw data.  
        @param[in] funct - function to run  
        @param[in/OPT] args - arguments for funct  
        @param[in/OPT] kwargs - keyword args for funct  
        @note this will operate directly on the data of each parameter. the first input to funct must also be self._raw  
        '''
        for k in self.waves.keys(): #loop through each key we have
            for p in self.waves[k].keys():
                self.waves[k][p].run_function_on_data(funct,*args,**kwargs)
    
    def average_keys(self,key_list):
         '''
         @brief average the keys in key_list and overwrite all keys data with the average data  
         @note this averages complex numbers
         @param[in] key_list - list of keys to average (e.g. [21,12])  
         @return TouchstoneParam or child thereof that has been averaged  
         '''
         for wk in self.waves: #do for each wave
             avg_param = self[wk][key_list].mean(axis=1)
             for k in key_list: #now set all of the keys. Each key will have a deep copy
                 self[(wk,k)] = avg_param
         return avg_param 
     
    def sort(self,**kwargs):
        '''@brief sort each of our parameters by frequency. calls DataFrame.sort_index(**kwargs)'''
        kwargs['inplace'] = kwargs.pop('inplace',True) #Default to true
        return self.sort_index()
    
    def ifft(self,window=None):
        '''
        @brief calculate the ifft of the data 
        @todo. Verify the lack of ifftshift here is correct for phases... 
        @param[in/OPT] window - what window to apply. can be 'sinc2' for sinc 
            squared or any input of first arg to of scipy.signal.windows.get_window (e.g. 'hamming', ('chebwin',100)),
            or a callable with input (len(self.raw))
        @return WaveformParam  
        '''
        return ifft(self,window=None)
        
    def crop(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove values outside a window (lo<=freqs<=hi)
        @param[in] lo_freq - lower part of window (Hz)
        @param[in] hi_freq - upper part of window (Hz)
        @return TouchstoneEditor with only values inside a window
        '''
        idx = np.logical_and(self.freqs>=lo_freq,self.freqs<=hi_freq)
        return self[idx]
        
    def cut(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove values inside a window (lo>=freqs or hi<=freqs)
        @param[in] lo_freq - lower part of window (Hz)
        @param[in] hi_freq - upper part of window (Hz)
        @return TouchstoneEditor with only values outside a window
        '''
        idx = np.logical_or(self.freqs<=lo_freq,self.freqs>=hi_freq)
        return self[idx]
            
    def round_freq_list(self):
        '''
        @brief round frequencies to nearest Hz. 
            This is to prevent a machine error issue seen when writing in the past
        '''
        self.freqs = np.round(self.freqs,decimals=0)
      
    @property
    def wave_dict_keys(self):
        '''@brief getter for wave_dict_keys after we switched to storing ports not keys'''
        return self._gen_dict_keys()
    
    @property
    def num_ports(self):
        '''@brief quickly get number of ports. Got tired of typing this  '''
        return len(self._ports)  
      
    @property
    def freqs(self): return self.index
    @freqs.setter
    def freqs(self,val): self.index = val
    @property
    def waves(self): return self.options['waves']
    
    # for returning correct classes
    @property
    def _constructor(self): return type(self)
    @property
    def _constructor_sliced(self): return self.options['param_class']
    
    @property
    def w1(self): return self.options['waves'][0]
    @property
    def v1(self): return self.w1[self.wave_dict_keys[0]]
    @property
    def freq_list(self): return self.freqs
    @property
    def bandwidth(self): return self.v1.bandwidth
    @property
    def frequency_step(self): return self.v1.frequency_step
    @property
    def raw(self): return self.to_numpy() 
    @raw.setter
    def raw(self,val): self[:] = val
    
    #some useful properties for different data getting types
    @property
    def mag(self): return type(self)(np.real(np.abs(self)),index=self.index,columns=self.columns)
    @property
    def mag_db(self): return 20*np.log10(self.mag)
    @property
    def phase(self): return type(self)(np.angle(self),index=self.index,columns=self.columns)
    @property
    def phase_d(self): return self.phase*180/np.pi
    
    # check total equality of the data
    def __eq__(self,other): return self.equals(other)
    
    def __getattr__(self,val):
        '''@brief Return view if accessed by e.g. S11'''
        if len(val)>1 and val[0] in self.options['waves'] and val[1:].isdigit():
            return self[(val[0],int(val[1:]))]
        return super().__getattr__(val)
        
              

class WnpEditor(TouchstoneEditor):
    '''@brief class for wave parameter file (*.wnp)'''
    def __init__(self,*args,**arg_options):
        options = {}
        options['waves'] = ['A','B'] #do s parameters
        options['default_extension'] = 'wnp'
        options['param_class'] = WnpParam
        for k,v in arg_options.items():
            options[k] = v
        super().__init__(*args,**options)

class SnpEditor(TouchstoneEditor):
    '''@brief class for s parameter file (*.snp)'''
    def __init__(self,*args,**arg_options):
        options = {}
        options['waves'] = ['S'] #do s parameters
        options['default_extension'] = 'snp'
        options['param_class'] = SnpParam
        for k,v in arg_options.items():
            options[k] = v
        super().__init__(*args,**options)

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
       
class WaveformEditor(SnpEditor):
    '''
    @brief class to read *.waveform classes that the MUF puts out. This can also be multi-port waveforms
    @param[in] args - variable arguements. If 2 args are passed, its assumed we have times/freqs,data (xaxis,yaxis)
                    otherwise pass parsing to TouchstoneParameter parsing
    '''
    def __init__(self,*args,**kwargs):
        '''@brief wrap touchstone parameter constructor to allow passing of x,y data explicitly'''
        if 'default_extension' not in kwargs.keys():
            kwargs['default_extension'] = 'waveform'
        if len(args)==2: #assume data is passed explicitly
            super().__init__([1,np.array(args[0])],**kwargs) #create correct size
            self[('S',21)].raw[:] = np.array(args[1],dtype=np.cdouble)
        else:
            super().__init__(*args,**kwargs)
        self.set_header(DEFAULT_HEADER_TIME)
        self.index.name='time'

    def read(*args,**kwargs):
        kwargs['round_freqs'] = kwargs.pop('round_freqs',False)
        return super().read(*args,**kwargs)
    
    def write(*args,**kwargs):
        kwargs['round_freqs'] = kwargs.pop('round_freqs',False)
        return super().write(*args,**kwargs)

    @property
    def raw(self): return np.squeeze(super().raw)
    
    @property
    def times(self): return super().freqs
                   
class BeamformEditor(WaveformEditor): 
    '''
    @brief Extension of WaveformEditor for beamformed data (only for 1D right now)
    @todo Extend to 2D (Az,El)
    @param[in] args - variable arguements. If 2 args are passed, its assumed we have angles,data (xaxis,yaxis)
                otherwise pass parsing to TouchstoneParameter parsing
    '''
    def __init__(self,*args,**kwargs):
        if 'default_extension' not in kwargs.keys():
            kwargs['default_extension'] = 'beamform'
        super().__init__(*args,**kwargs)
        self.set_header(DEFAULT_HEADER_ANG)
        
    @property
    def angles(self):
        return self.freqs
    

#%% Class for each parameter
class TouchstoneParam(pd.Series):
    '''
    @brief class for a single parameter (e.g. S[11])  
    @brief initialize our parameter  
    @param[in/OPT] freqs - frequencies of the raw data (passed to series indices)
    @cite https://pandas.pydata.org/pandas-docs/stable/development/extending.html
    '''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        kwargs['index'] = kwargs.pop('freqs',kwargs.pop('index',None))
        kwargs['dtype'] = kwargs.pop('dtype',np.cdouble)
        super().__init__(*args,**kwargs)
    
    # https://pandas.pydata.org/pandas-docs/stable/development/extending.html
    @property
    def _constructor(self): return type(self)
    @property
    def _constructor_expanddim(self): return TouchstoneEditor
    
    def sort(self):
        '''@brief sort the parameter by frequency  '''
        kwargs['inplace'] = kwargs.pop('inplace',True) #Default to true
        return self.sort_index()
        
    def crop(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove all frequencies and their corresponding values outside a given window  
        @return type(self) with values removed
        '''
        lo_val = np.round(lo_freq)
        hi_val = np.round(hi_freq)
        idx = np.logical_and(self.freqs>=lo_freq,self.freqs<=hi_freq)
        return self[idx]
        
    def cut(self,lo_freq=0,hi_freq=1e60):
        '''
        @brief remove all frequencies and their corresponding values inside a given window 
        @return type(self) with values removed
        '''
        lo_val = np.round(lo_freq)
        hi_val = np.round(hi_freq)
        idx = np.logical_and(self.freqs>lo_val,self.freqs<hi_val)
        return self[idx]
        
    def ifft(self,window=None):
        '''
        @brief calculate the ifft of the data 
        @todo. Verify the lack of ifftshift here is correct for phases... 
        @param[in/OPT] window - what window to apply. can be 'sinc2' for sinc 
            squared or any input of first arg to of scipy.signal.windows.get_window (e.g. 'hamming', ('chebwin',100)),
            or a callable with input (len(self.raw))
        @return WaveformParam  
        '''
        return ifft(self,window=None)
    
    #alias for backward compatability
    calculate_time_domain_data = ifft 
    
    def plot_plotly(self,data_type='mag_db',trace_only=False,**plot_options):
        '''
        @brief plot the data from the parameter given as data_type using plotly. Placeholder until pandas implements
            plotly as a backedn plotting enging (they say next release) 
        @param[in] data_type - type of data to plot (e.g. mag,mag_db,phase,phase_d)  
        @param[in/OPT] trace_only - only return the plotly trace (as opposed to a figure) (default False)
        @param[in/OPT] plot_options - keyword args to pass as options to go.Scatter
        @return Plotly figure handle (if trace_only=False) or Plotly trace handle (if trace_only=True)
        '''
        data = getattr(self,data_type)
        freqs = self.freqs
        if not trace_only: #if we dont just want the trace, return the plot
            fig = go.Figure()
        rv = go.Scatter(x=freqs/1e9,y=data,**plot_options)
        if not trace_only:
            fig.add_trace(rv)
            fig.update_layout(xaxis_label='Freq (GHz)',yaxis_label=data_type)
            rv = fig
        return rv
    
    def run_function_on_data(self,funct,*args,**kwargs):
       '''
       @brief run a function on each of our param raw data.  
       @note this sets the raw values (integer index) whereas pd.Series.apply() cannot
       @param[in] funct - function to run  
       @param[in/OPT] args - arguments for funct  
       @param[in/OPT] kwargs - keyword args for funct  
       @note this will operate directly on self.raw. the first input to funct will be complex ndarray  
       '''
       self.raw = funct(self.raw,*args,**kwargs)
    
    def get_bandwidth(self):
        '''@brief get the highest and lowest frequencies to determine our step  '''
        return np.ptp(self.freqs)
    
    def estimate_snr(self,window_size=10):
        '''
        @brief estimate the mean snr of the signal 
            This takes a moving average of the signal and subtracts that from
            the signal. whatever is left is considered noise. This can only
            give a vague estimation of SNR multiple measurements would give
            a much better view  
        @param[in] window_size - size of window to run the moving average with  
        @todo implement  
        '''
        pass
    
    @property
    def freqs(self): return np.array(self.index)
    @freqs.setter
    def freqs(self,val): self.index = val
    
    @property
    def raw(self): return self.to_numpy()
    @raw.setter
    def raw(self,val): self[:] = val
    
    @property
    def bandwidth(self): return self.get_bandwidth()
        
    def get_frequency_step(self):
        '''@brief get the average step between our frequencies'''
        return np.mean(np.diff(self.freqs))
    @property
    def frequency_step(self): return self.get_frequency_step()
    
    #some useful properties for different data getting types
    @property
    def mag(self): return type(self)(np.real(np.abs(self)),index=self.index)
    @property
    def mag_db(self): return 20*np.log10(self.mag)
    @property
    def phase(self): return type(self)(np.angle(self),index=self.index)
    @property
    def phase_d(self): return self.phase*180/np.pi

#just for naming
class WnpParam(TouchstoneParam): pass
class SnpParam(TouchstoneParam): pass
class WaveformParam(TouchstoneParam):
    '''@brief parameter for waveorm files'''
    @property
    def times(self):
        '''@brief allow times as opposed to freq_list'''
        return self.freqs
    @times.setter
    def times(self,val):
        '''@brief setter for times alias'''
        self.freqs[:] = times
        

#%% Error codes
class TouchstoneError(Exception):
    '''
    @brief custom exception for errors in touchstone handling  
    '''
    def __init__(self,err_msg):
        self.err_msg = err_msg
    def __str__(self):
        return repr("%s" %(self.err_msg)) 
    
class TouchstoneArithmeticError(TouchstoneError):
    pass
    
class SnpError(TouchstoneError):
    pass
    
class MalformedSnpError(SnpError):
    '''
    @brief snp/wnp file is not formed correctly error  
    '''
    def __init__(self,err_msg):
        super().__init__(err_msg)

        
def map_keys(key_list,mapping_dict):
    '''
    @brief change a set of keys (e.g. [11,31,13,33]) based on a mapping dict  
    @param[in] key_list - list of keys for TouchstoneParams (e.g. [11,31,13,33])  
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


#%% Unit testing
import unittest
import os 
class TestTouchstoneEditor(unittest.TestCase):
    '''
    @brief Unittests class for Touchstone Editor
    '''
    
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
		#path of our directory for the data
        super().__init__(*args,**kwargs)
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.dir_path = os.path.join(self.dir_path,'../analysis/support/test')
        self.test_snp_txt = 'test.s2p'
        self.test_snp_bin = 'test.s2p_binary'
        self.test_wnp_txt = 'test.w2p'
        self.test_wnp_bin = 'test.w2p_binary'
	
    def test_wnp_io(self):
        '''@brief test loading of wnp editor'''
		#print("Loading *.wnp files")
        wnp_text_path = os.path.join(self.dir_path,self.test_wnp_txt)
        wnp_bin_path  = os.path.join(self.dir_path,self.test_wnp_bin)
        wnp_text = WnpEditor(wnp_text_path)
        wnp_bin  = WnpEditor(wnp_bin_path)
        self.assertEqual(wnp_bin,wnp_text)
        wnp_text.write('test2.w2p')
        wnp_text.write('test2.w2p_binary')
        os.remove('test2.w2p')
        os.remove('test2.w2p_binary')
		
    def test_snp_io(self):
        '''@brief test loading and writing of snp editor'''
		#print("Loading *.snp files")
        snp_text_path = os.path.join(self.dir_path,self.test_snp_txt)
        snp_bin_path  = os.path.join(self.dir_path,self.test_snp_bin)
        snp_text = SnpEditor(snp_text_path)
        snp_bin  = SnpEditor(snp_bin_path)
        self.assertEqual(snp_bin,snp_text)
        snp_text.write('test2.s2p')
        snp_text.write('test2.s2p_binary')
        snp_text2 = SnpEditor('test2.s2p')
        snp_text2.write('test22.s2p')
        self.assertEqual(snp_text,snp_text2)
        snp_bin.write('test3.s2p_binary')
        snp_bin2 = SnpEditor('test3.s2p_binary')
        self.assertEqual(snp_bin,snp_bin2)
        os.remove('test2.s2p')
        os.remove('test2.s2p_binary')
        os.remove('test22.s2p')
        os.remove('test3.s2p_binary')
		
    def test_key_mapping(self):
        '''@brief test mapping keys to different ports'''
        keys = [11,31,13,33]
        mapping = {3:2}
        expected_keys = [11,21,12,22]
        new_keys = map_keys(keys,mapping)
        self.assertTrue(np.all(np.equal(expected_keys,new_keys)))
		
    def test_2_port_swapping(self):
        '''@brief test using swap_ports to swap 2 port files and swapping  
		@todo improve this to test 2 different data files. THis test only
			ensures data is not corrupted. It doesnt verify data is actually
			swapped at all  
		'''
        f1 = os.path.join(self.dir_path,self.test_snp_txt)
        f2 = os.path.join(self.dir_path,self.test_snp_bin)
        s1 = TouchstoneEditor(f1)
        s2 = TouchstoneEditor(f2)
        so1,so2 = swap_ports(s1,s2) #these files contain the same data
        self.assertEqual(so1,s1)
        self.assertEqual(so2,s2)
        s1c = SnpEditor(f1)
        s1.swap_ports(1,2)
        s1.swap_ports(1,2)
        self.assertEqual(s1,s1c)
        s1_11 = copy.deepcopy(s1.S[11].raw)
        s1.swap_ports(1,2)
        self.assertTrue(np.all(s1_11==s1.S[22].raw))
		
    def test_arithmetic_between_values(self):
        '''
		@brief test arithmetic operations  
		@todo add other tests besides just multiply and test multiple ports/waves  
		'''
		# test arithmetic _mult__,__add__, etc
        f1 = os.path.join(self.dir_path,self.test_snp_txt)
        f2 = os.path.join(self.dir_path,self.test_snp_bin)
        s1 = SnpEditor(f1)
        s2 = SnpEditor(f2)
        sp1 = s1.S[21]
        sp2 = s2.S[21]
        sp3 = sp1*sp2
        self.assertTrue(np.all(sp3.raw==(sp1.raw*sp2.raw)))
        s3 = s1*s2
        self.assertTrue(np.all(s3.S[21].raw==(sp1.raw*sp2.raw)))
        s4 = s1*complex(5,2)
        self.assertTrue(np.all(s4.S[21].raw==(sp1.raw*complex(5,2))))
		
    def test_new_class_creation(self):
        '''@brief test the creatino of new classes from TouchstoneEditor superclass'''
        wnp_text_path = os.path.join(self.dir_path,self.test_wnp_txt)
        wnp_bin_path  = os.path.join(self.dir_path,self.test_wnp_bin)
        w1 = TouchstoneEditor(wnp_text_path)
        w2 = TouchstoneEditor(wnp_bin_path)
        self.assertEqual(type(w1),WnpEditor)
        self.assertEqual(type(w2),WnpEditor)
        snp_text_path = os.path.join(self.dir_path,self.test_snp_txt)
        snp_bin_path  = os.path.join(self.dir_path,self.test_snp_bin)
        s1 = TouchstoneEditor(snp_text_path)
        s2 = TouchstoneEditor(snp_bin_path)
        self.assertEqual(type(s1),SnpEditor)
        self.assertEqual(type(s2),SnpEditor)      
        
    def test_create_waveform(self):
        '''@brief test creating a WaveformParameter from (freq,data) argument input'''
        freqs = np.linspace(-2*np.pi,2*np.pi,1000)
        data = np.sin(2*freqs)
        wfe = WaveformEditor()
        #wf = WaveformEditor(freqs,data)
        
    def test_plot(self):
        '''@brief test plotting'''
        f1 = os.path.join(self.dir_path,self.test_snp_txt)
        s1 = SnpEditor(f1)
        fig = s1.mag_db.plot()
        figpl = s1.plot_plotly(data_type='mag_db')
    
    def test_combine_split(self):
        '''@brief test combine_parameters and split_measurements to combine TouchstoneEditors
        @todo add split_measurements'''
        f1 = os.path.join(self.dir_path,self.test_snp_txt)
        f2 = os.path.join(self.dir_path,self.test_snp_bin)
        s1 = SnpEditor(f1)
        s2 = SnpEditor(f2)
        sc0 = combine_parameters(s1,s2)
        sc1 = combine_parameters(f1,f2)
        sc2 = combine_parameters(f1,s2)
        self.assertTrue(sc0==sc1) #check that using files and objects makes the same
        self.assertTrue(sc0==sc2)
        self.assertTrue(np.all(sc0.S[33]==s2.S[11]))
        self.assertTrue(np.all(sc0.S[11]==s2.S[11]))
        self.assertTrue(np.all(sc0.S[34]==s2.S[12]))
        #now lets separate them again
        os1,os2 = split_parameters(sc0,2)
        self.assertTrue(os1==s1)
        self.assertTrue(os2==s2)
        
    def test_to_time_domain(self):
        '''@brief Test changing to time domain data'''
        f1 = os.path.join(self.dir_path,self.test_snp_txt)
        s1 = SnpEditor(f1)
        td_data = s1.ifft()
        td_S21  = s1.S21.ifft()
        self.assertTrue(np.all(td_S21==td_data.S21))
        
            
#%% things to run when we run this file
if __name__=='__main__':
    

    suite = unittest.TestLoader().loadTestsFromTestCase(TestTouchstoneEditor)
    unittest.TextTestRunner(verbosity=2).run(suite)

    # test touchstoneParam
    myp = SnpParam([1,2,3],freqs=[4,5,6])   
    s = SnpEditor(0,columns=[1,2],index=[0,1,2])

    #geyt the current file directory for the test data
    import os 
    import copy
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path,'../analysis/support/test')
    
    test_snp_txt = 'test.s2p'
    test_snp_bin = 'test.s2p_binary'
    test_wnp_txt = 'test.w2p'
    test_wnp_bin = 'test.w2p_binary'
    
    fpath = os.path.join(dir_path,test_snp_txt)

    s = TouchstoneEditor()
    s0 = mysnp = TouchstoneEditor(os.path.join(dir_path,test_snp_txt))
    
    mytd = ifft(mysnp)
    mytds = ifft(mysnp.S21)
  
    s1 = TouchstoneEditor(os.path.join(dir_path,test_snp_bin))
    mysnp_orig = copy.deepcopy(mysnp)
    mysnp.S21.run_function_on_data(moving_average,10)
    #moving_average(mysnp.S[21],10)
    r1 = mysnp_orig.S21.raw
    r2 = mysnp.S21.raw
    #mysnp.plot([21])
    
    #comb = combine_parameters(mysnp,mysnp)
    
    #import doctest
    #doctest.testmod(extraglobs=
    #                {'mys2p':TouchstoneEditor(os.path.join(dir_path,'test.s2p')),
    #                 'myw2p':TouchstoneEditor(os.path.join(dir_path,'test.s2p'))})
        
    #myw = WaveformEditor([1,2,3],[3,2,1])
 

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
