# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:58:12 2019
Class to help plot matlab figures.
Funny enough, this class is actually generic enough where it makes using
all matlab interfaces easier by automatically converting some types of values
to the matlab values and adding little arguments like nargin=0
NAMED ARGUMENTS DO NOW WORK HERE
@author: aweis
"""

import matlab.engine
import six
import numpy as np
from itertools import chain

class MatlabPlotter:
    '''
    @brief class for plotting figures using matlab engine
        This class will start a matlab engine when initiated and close it when
        deleted
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief initialize the class and start our MATLAB engine
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose - be verbose in our plotting (default False)
        '''
        self.options = {}
        self.options['verbose'] = False
        for key,val in six.iteritems(arg_options):
            self.options[key]=val
        if self.options['verbose']: print("Starting MATLAB Engine")
        #running_engines = matlab.engine.find_matlab()
        #eng_name = 'PyMatPlottingEngine'
        #if not eng_name in running_engines: #check if the engine is running and start it if is
        #self.engine = matlab.engine.start_matlab('-r "matlab.engine.shareEngine(\''+eng_name+'\')"') #connect to an engine, or start if needed
        self.engine = matlab.engine.start_matlab()
        self.beep('off')
        #import io
        #out = io.StringIO()
        #err = io.StringIO()
        #ret = self.engine.dec2base(2**60,16,stdout=out,stderr=err)
        #else:
        #    self.engine = matlab.engine.connect_matlab(name=eng_name) #for some reason I cant connect to a started engine
    
    def call_matlab_funct(self,funct_name,*args,**kwargs):
        '''
        @brief call a matlab function given by name funct_name
        @param[in] funct_name - name of function to call
        @param[in/OPT] *args - variable arguments to pass to matlab funciton
        @parma[in/OPT] **kwargs - keyword args to pass to matlab function (all except nargout)
        '''
        funct = getattr(self.engine,funct_name)
        args,kwargs = self.args2matlab(*args,**kwargs)
        return funct(*args,**kwargs)
    
    def call_functs_from_dict(self,funct_dict,**kwargs):
        '''
        @brief call a set of matlab functions from a dictionary
        @param[in] funct_dict - dictionary of function:argument pairs
            multiple arguments MUST be provided as tuple
        @param[in/OPT] kwargs - keyword arguments to be passed to call_matlab_funct for all values
            nargout - typically called for functions that have no outputs use 'nargout=0'
        @return list of function returns
        '''
        rv = []
        for k,v in funct_dict.items():
            if type(v) is not tuple:
                v=(v,) #then make it a tuple
            rvc = self.call_matlab_funct(k,*v,**kwargs)
            rv.append(rvc)
        return rv

    def args2matlab(self,*args,**kwargs):
        '''
        @brief convert variable number of arguments to matlab
            kwargs will also be converted to name/value pairs
        @param[in] *args - variable arguments
        @param[in/OPT] **kwargs - kwargs will be converted to name/value pairs
        @return tuple of variable args (*args) and dict for keyword arguments
            kwargs will just have special required keyword args like nargout
        '''
        args_out = []
        for arg in args: #loop through each argument
            if type(arg)==np.ndarray: arg = arg.tolist()
            if type(arg)==tuple:      arg = list(arg)
            #now convert lists to matlab
            if type(arg)==list: #this assumes consistent values across list
                if type(arg[0]==float):
                    args_out.append(matlab.double(arg))
                elif type(arg[0]==int):
                    args_out.append(matlab.int32(arg))
            else:
                args_out.append(arg)
        #keyword args
        if kwargs:
            kargs,kwargs = self.__kwargs2matlab(**kwargs)
            args_out+=kargs
        
        return tuple(args_out),kwargs
    
    def __kwargs2matlab(self,**kwargs):
        '''
        @brief convert kwargs to list of name/value pairs
        @note the following special values will be passed back as a dictionary
        and should be passed to matlab as kwargs
                nargout - number of output arguments required to be 0 for some functions
        '''
        special_kwargs = ['nargout']
        spec_kwargs_dict = {k:kwargs.pop(k,None) for k in special_kwargs} #get our function dictionary
        spec_kwargs_dict = {k:v for k,v in spec_kwargs_dict.items() if v is not None} #remove none values (not provided)
        name_list = list(kwargs.keys())
        vals_list = list(kwargs.values())
        vals_list = list(self.args2matlab(*tuple(vals_list))) #change to matlab stuff
        name_val_pairs = list(chain.from_iterable(zip(name_list, vals_list)))
        return name_val_pairs,spec_kwargs_dict
    
    def nparray2matlab(self,mynparray):
        '''
        @brief change a numpy array to a MATLAB array
        @param[in] mynparray - a numpy array of any number of dimensions
        @return mlarray.double
        '''
        return matlab.double(mynparray.tolist())
    
    def is_figure(self,obj):
        '''
        @brief test whether an object is a figure
        @param[in] obj - the object to test
        @return true if is a figure, false otherwise
        '''
        return self.eng.get(obj,'type')=='figure'
    
    def is_axes(self,obj):
        '''
        @brief test whether an object is an axis
        @param[in] obj - the object to test
        @return true if is an axis, false otherwise
        '''
        return self.eng.get(obj,'type')=='axes'
    
        
    def __getattr__(self,name):
        '''
        @brief This is the MOST IMPORTANT METHOD. It allows all matlab functions to 
        be called from self. This is not ideal because if nargout must=0 then we have to 
        run the funciton twice (this can be sped up by manually passing nargout=0)
        '''
        def default_method(*args,**kwargs):
            try:
                rv = self.call_matlab_funct(name,*args,**kwargs) #matlab errors ding
            except matlab.engine.MatlabExecutionError as err: #if nargin must be zero lets except
                if str(err).strip().split('\n')[-1]=='Too many output arguments.':
                    self.call_matlab_funct(name,*args,**kwargs,nargout=0)
                    rv = None
                else:
                    raise err
            return rv
        return default_method
                
                
    def quit(self):
        self.engine.quit()
    
    def __del__(self):
        self.engine.quit()
    
if __name__=='__main__':
    #try:
    #    raise Exception("This dinging is annoying")
    #except Exception as exc:
    #    print("I handled it")
    '''
    #surf test
    mp = MatlabPlotter(verbose=True)
    [X,Y] = np.mgrid[1:10:0.5,1:20]
    Z = np.sin(X)+np.cos(Y)
    mp.surf(X,Y,Z)
    mp.xlim([0,20])
    mp.zlabel('X')
    mp.shading('interp')
    '''
    
    #1D plotting test
    mp = MatlabPlotter(verbose=True)
    x = np.linspace(0,3.*np.pi,1000)
    y = np.cos(x)
    args = mp.args2matlab(x,y,DisplayName='testing',xlim=[0,10])
    #kargs = mp.kwargs2matlab(DisplayName='testing',xlim=[0,10])
    #print(kargs)
    mp.figure()
    mp.plot(x,y,DisplayName='testing')
    mp.legend('show')
    
    
    
    