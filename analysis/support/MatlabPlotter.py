# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 13:58:12 2019

@author: aweis
"""

import matlab.engine
import six
import numpy as np

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
        #else:
        #    self.engine = matlab.engine.connect_matlab(name=eng_name) #for some reason I cant connect to a started engine
    
    def surf(self,*args,**kwargs):
        '''
        @brief surface plot in MATLAB
        @param[in] X - np.array of X values
        @param[in] Y - np.array of Y values
        @param[in] Z - np.array of Z values
        @return matlab plot object
        '''
        args = self.args2matlab(*args)
        fig = self.engine.surf(*args,kwargs)
        self.engine.shading('interp',nargout=0) #without nargout=0 throws an error
        return fig
        
    def args2matlab(self,*args):
        '''
        @brief convert variable number of arguments to matlab
        @param[in] *args - variable arguments
        '''
        args_out = []
        for arg in args: #loop through each argument
            if type(arg)==np.ndarray: #convert to matlab 
                args_out.append(self.nparray2matlab(arg))
            else:
                args_out.append(arg)
                pass #otherwise do nothing
                
        return tuple(args_out)
        
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
    
    def quit(self):
        self.engine.quit()
    
    def __del__(self):
        self.engine.quit()
    
if __name__=='__main__':
    mp = MatlabPlotter(verbose=True)
    [X,Y] = np.mgrid[1:10:0.5,1:20]
    Z = np.sin(X)+np.cos(Y)
    mp.surf(X,Y,Z)