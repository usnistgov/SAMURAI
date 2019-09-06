# -*- coding: utf-8 -*-
"""
Created on Mon May 20 15:04:22 2019

@author: ajw5
"""

import numpy as np
from samurai.base.SamuraiDict import SamuraiDict,update_nested_dict

class SamuraiPlotter:
    '''
    @brief a class to abstract plotting between matplolib, matlab, and plotly, (and potentially others)
    '''
    def __init__(self,plot_program=None,*args,**arg_options):
        '''
        @brief initializer for plotting class
        @param[in/OPT] plot_program - What program to use to plot 
            ('matlab','matplotlib','plotly')
            some plotting types may only be supported with some programs
        @param[in/OPT] *args - arguments to pass to plot_program initailzer
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose - whether or not to be verbose
            debug - extra verbose debug statements
            matlab_engine - can pass an already running matlab engine if matlab 
                is being used
        '''
        self.set_plot_program(plot_program)
        
        #some options
        self.options = {}
        self.options['verbose'] = False
        self.options['debug'] = True
        self.options['plot_program_class_dict'] = {'matlab':MatlabPlotter,'matplotlib':MatplotlibPlotter,'plotly':PlotlyPlotter}
        self.options['plot_program_dict'] = {} #this holds the engine classes after initialization
        for key,val in arg_options.items():
            self.options[key] = val
        #also intialize the plotter and pass the arguments to the init
        if self.plot_program is not None:
            self._init_plot_program()
        
    def _run_plot_function(self,plot_funct_name,*args,**kwargs):
        '''
        @brief loop through each of our programs to try and plot
        @param[in] plot_funct_name - name of plotting function (ie surf)
        @params[in] args - variable arguments to pass to pltting funciton
        @param[in] kwargs - keyword ags to pass to plotting funciton
        '''
        self._init_plot_program() #ensure we are initialized
        kwargs = {k.lower():v for k,v in kwargs.items()} #make all keys lowercase
        funct = getattr(self._get_plot_program_object(),plot_funct_name) 
        rv = funct(*args,**kwargs)
        return rv
    
    def set_plot_program(self,plot_program):
        '''
        @brief change the plot program in use
        @param[in] plot_program - what program to plot with
        '''
        self.plot_program = plot_program
        

    ###########################################################################
    ####### Surface Plots
    ########################################################################### 
    def surf(self,*args,**kwargs):
        '''
        @brief abstracted surface plotting function
        @param[in] args - arguments for the plot function (in MATLAB fasion)
        @param[in] kwargs - keyword arguments will be used as name/value pairs
            again in MATLAB format except for the following special keywords:
                xlim,ylim,zlim - set the x,y,z limits on the plot
                xlabel,ylable,zlabel - set the x,y,z labels on the plot
                view - set the plot view
                shading - set the shading (for matlab. usually 'interp')
                title - title of the plot
                colorbar - arguements (as a tuple) to pass to the colorbar function
        '''
        rv = self._run_plot_function('surf',*args,**kwargs)
        return rv

    ###########################################################################
    ####### regular 2D plots
    ###########################################################################
    def plot(self,*args,**kwargs):
        '''
        @brief abstracted 2D plotting function
        @param[in] args - arguments for the plot function (in MATLAB fasion)
        @param[in] kwargs - keyword arguments will be used as name/value pairs
            again in MATLAB format except for the following special keywords:
                xlim,ylim,zlim - set the x,y,z limits on the plot
                xlabel,ylable,zlabel - set the x,y,z labels on the plot
                view - set the plot view
                shading - set the shading (for matlab. usually 'interp')
                title - title of the plot
                colorbar - arguements (as a tuple) to pass to the colorbar function
        '''
        rv = self._run_plot_function('plot',*args,**kwargs)
        return rv
    
    ###########################################################################
    ####### for all unimplemented, try to call from the first value in plot order
    ###########################################################################
    def __getattr__(self,attr):
        '''
        @brief this function will be called when the attribute or method 
            is not found. The call will look in the first value of
            self.options['plot_order'] for the method or property
        @param[in] name - attribute name
        '''
        self._init_plot_program()
        plotter = self._get_plot_program_object()
        attr = getattr(plotter,attr)
        return attr
        
        
    ###########################################################################
    ####### Initializer
    ###########################################################################    
    def _init_plot_program(self,*args,**kwargs):
        '''
        @brief initialize the current device whos name is in self.plot_program
        @param[in/OPT] *args,**kwargs - all input arguements passed to initializer
        '''
        if self.plot_program is None:
            raise Exception("No plot program defined")
        #first check if its already initialized
        cur_plotter = self.options['plot_program_dict'].get(self.plot_program,None)
        if cur_plotter is not None: #already initialized
            return
        #now lets initialize if we make it here
        plot_class = self.options['plot_program_class_dict'].get(self.plot_program,None)
        if plot_class is None: #then its not supported
            raise Exception(("'{}' is not a supported plotting program,"
             'please set self.plot_program to one of the'
             ' following {}').format(self.plot_program,list(self.options['plot_program_class_dict'].keys())))
        else: #otherwise lets initialize
            plotter = plot_class(*args,**kwargs)
            self.options['plot_program_dict'][self.plot_program] = plotter  

    ###########################################################################
    ####### generic internal funcitons
    ########################################################################### 
    def _get_plot_program_object(self):
        '''
        @brief return the handle to the current plot program handle
        '''
        plotter = self.options['plot_program_dict'][self.plot_program]
        return plotter
    
    @property
    def plotter(self):
        '''
        @brief getter _get_plot_program_object
        '''
        return self._get_plot_program_object()
    
    def _check_arg_count(self,arg_count,min_args,max_args):
        '''
        @brief check for a minimum and maximum *args count
        @param[in] arg_count - number of arguemnts recieved
        @param[in] min_args - minimum number of arguements required
        @param[in] max_args - maximum number of arguments possible
        '''
        if arg_count<min_args: 
            raise TypeError("At least 3 input arguments required")
        if arg_count>max_args: 
            raise TypeError("Too many arguments (3 or 4 expected, {} recieved)".format(arg_count))    
    
    ###########################################################################
    ####### argument translation
    ########################################################################### 
    
    
class SamuraiPlotEngine:
    '''
    @brief superclass for defining a plot program
        The process of plotting here is figure(),(plot_function)(),show()
        These three steps allow working with most plotting library flows
    '''
    def __init__(self):
        self.options = {}
        self.options['engine'] = None
        self._translation_dict = SamuraiDict()
        self._set_translation_dict() #init translation_dict
        
    def _set_translation_dict(self):
        '''
        @brief dictionary translation between commands
        '''
        pass
        
    def __getattr__(self,attr):
        '''
        @brief pass any nonexistant attributes to the engine
        '''
        return getattr(self.options['engine'],attr)
        
    def surf(self,*args,**kwargs):
        '''
        @brief default function for surf
        '''
        raise NotImplementedError
        
    def plot(self,*args,**kwargs):
        '''
        @brief default function for 2D plot
        '''
        raise NotImplementedError
        
    def scatter(self,*args,**kwargs):
        '''
        @brief default function for scatterplot
        '''
        raise NotImplementedError
        
    def figure(self,*args,**kwargs):
        '''
        @brief default function for creating a figure
        '''
        fig = self.engine.figure()
        return fig
        
    def show(self,fig,*args,**kwargs):
        '''
        @brief show the figure. in most cases this function wont do anything
        '''
        pass
    
    def _translate_arguments(self,**kwargs):
        '''
        @brief translate arguments dictionary based on our translation_dictionary
        @param[in] kwargs - name/param arguements to translate
        @note this can also translate to functions
        '''
        #now get a list of the functions specified and remove from kwargs
        arg_dict = SamuraiDict()
        for k,v in self._translation_dict.items():
            val = kwargs.pop(k,None)
            if val is not None:
                arg_dict[v] = val 
        return dict(arg_dict)         
    
    def _run_arg_functions_on_object(self,obj,**kwargs):
        '''
        @brief take a list of input kwargs. If the object has that attribute, 
            run the function with the value of that function key and remove it from
            the argument dictionary. Otherwise leave it
        @param[in] obj - object to run functions on
        @param[in] **kwargs - arguemenbt dictionary to find functions from
        '''
        for k,v in kwargs.items():
            if hasattr(obj,k):
                funct_args = kwargs.pop(k) #get the arguemnts and remove the function
                funct = getattr(obj,k)
                funct(funct_args)
            #otherwise do nothing
        return kwargs #return the keyword arguement dictionary
    
    @property
    def engine(self):
        '''
        @brief getter for self.options['engine']
        '''
        return self.options['engine']
    
    @engine.setter
    def engine(self,val):
        '''
        @brief setter for self.options['engine']
        '''
        self.options['engine'] = val
        
        
class MatplotlibPlotter(SamuraiPlotEngine):
    '''
    @brief plotting class for matplotlib abstraction
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief initialize the class
        @param[in/OPT] args - currently no required arguments
        @param[in/OPT] kwargs - keyword args as follows:
            engine - matlab engine to use
        '''
        import matplotlib.pyplot as plt
        from matplotlib import cm
        super().__init__(*args,**kwargs)
        self.options['engine'] = plt
        self.options['cm'] = cm
        for k,v in kwargs.items():
            self.options[k] = v
            
    def surf(self,*args,**kwargs):
        '''
        @brief surface plot in matplotlib
        '''
        if len(args)<3: raise Exception("At least 3 input arguments required")
        if len(args)>4: raise Exception("Too many arguments (3 or 4 expected, {} recieved)".format(len(args)))
        if len(args)==3: plot_data = args[2] #make Z
        if len(args)==4: plot_data = args[3] #make C
        X = args[0]
        Y = args[1]
        Z = args[2]
        funct_keys = ['xlim','ylim','zlim','xlabel','ylabel','zlabel','view','shading','title','colorbar']
        funct_dict = {k:kwargs.pop(k,None) for k in funct_keys} #get our function dictionary
        funct_dict = {k:v for k,v in funct_dict.items() if v is not None} #remove none values (not provided)
        
        if funct_dict.get('colorbar',None): #colorbar settings
            cb_args = funct_dict['colorbar']
            try:    xt  = cb_args[cb_args.index('XTick')+1] 
            except: xt =None
            try:    xtl = cb_args[cb_args.index('XTickLabel')+1] 
            except: xtl=None
            cb = dict(tickvals=xt,ticktext=xtl)
        else: cb=None
        
        fig = self.engine.figure()
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(X,Y,Z,cmap = self.options['cm'].coolwarm)
        ax.set_xlim(funct_dict.get('xlim',None))
        ax.set_ylim(funct_dict.get('ylim',None))
        ax.set_zlim(funct_dict.get('zlim',None))
        ax.set_xlabel(funct_dict.get('xlabel',None))
        ax.set_xlabel(funct_dict.get('ylabel',None))
        ax.set_xlabel(funct_dict.get('zlabel',None))
        cb = fig.colorbar(surf,ticks=xt)
        cb.ax.set_yticklabels(xtl)
        return fig
    
    def plot(self,*args,**kwargs):
        '''
        @brief 1D plot in matplotlib
        '''
        #self._check_arg_count(len(args),2,2) #must have exactly 2 args
        #fig = self.matplotlib.figure()
        ax = self.engine.gca()
        kwargs = self._translate_arguments(**kwargs)
        kwargs = self._run_arg_functions_on_object(ax,**kwargs)
        self.engine.plot(*args,**kwargs)
        return ax
    
    def _set_translation_dict(self):
        '''
        @brief set the dictionary for parameter translation
        '''
        for d in ['x','y','z']:
            self._translation_dict.update({'{}lim'.format(d):'set_{}lim'.format(d)}) #limits
            self._translation_dict.update({'{}label'.format(d):'set_{}label'.format(d)}) #labels 
        self._translation_dict.update({'displayname':'label'})
        
class PlotlyPlotter(SamuraiPlotEngine):
    '''
    @brief plotting abstraction for plotly
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief init the class
        @param[in/OPT] args - currently no required arguments
        @param[in/OPT] kwargs - keyword args as follows:
            engine - matlab engine to use
        '''
        import plotly.graph_objects as go
        from mpl_toolkits.mplot3d import Axes3D
        super().__init__(*args,**kwargs)
        self.options['engine'] = go
        for k,v in kwargs.items():
            self.options[k] = v
            
    def surf(self,*args,**kwargs):
        '''
        @brief surface plot in plotly
        '''
        if len(args)<3: raise Exception("At least 3 input arguments required")
        if len(args)>4: raise Exception("Too many arguments (3 or 4 expected, {} recieved)".format(len(args)))
        if len(args)==3: plot_data = args[2] #make Z
        if len(args)==4: plot_data = args[3] #make C
        X = args[0]
        Y = args[1]
        Z = args[2]
        funct_keys = ['colorbar']
        funct_dict = {k:kwargs.pop(k,None) for k in funct_keys} #get our function dictionary
        funct_dict = {k:v for k,v in funct_dict.items() if v is not None} #remove none values (not provided)
        
        if funct_dict.get('colorbar',None): #colorbar settings
            cb_args = funct_dict['colorbar']
            try:    xt  = cb_args[cb_args.index('XTick')+1] 
            except: xt =None
            try:    xtl = cb_args[cb_args.index('XTickLabel')+1] 
            except: xtl=None
            cb = dict(tickvals=xt,ticktext=xtl)
        else: cb=None
            
        plotly_surf = [self.engine.Surface(x=X, y=Y, z=Z,surfacecolor=plot_data,colorbar=cb)]
        layout = self.engine.Layout(
            scene=None,
            autosize=True,
        )
        fig_dict = dict({'data':plotly_surf,'layout':layout})
        kwarg_trans = self._translate_arguments(**kwargs)
        update_nested_dict(fig_dict,kwarg_trans,overwrite_values=True)
        fig = self.engine.Figure(fig_dict)
        #fig = self.engine.FigureWidget(fig)
        self.show(fig)
        return fig
    
    def _set_translation_dict(self):
        '''
        @brief set the dictionary for parameter translation
        '''
        for d in ['x','y','z']:
            lab_name = '{}axis'.format(d)
            self._translation_dict.update({'{}lim'.format(d):['layout','scene',lab_name,'range']}) #limits
            self._translation_dict.update({'{}label'.format(d):['layout','scene',lab_name,'title']}) #labels 
        self._translation_dict.update({'displayname':['layout','title']})
    
    def show(self,fig,*args,**kwargs):
        '''
        @brief show the plot. Currently this is done and saved out to 'filename'
            kwarg
        @param[in] *args,**kwargs - all passed to plotly.offline.plot() (self.engine.plot())d
        '''
        fig.show()
        
    def write(self,fig,out_path,*args,**kwargs):
        '''
        @brief write out the plot
        '''
        fig.write_html(out_path)
        return out_path
                 
        
class MatlabPlotter(SamuraiPlotEngine):
    '''
    @brief further plotting abstraction for matlab
    '''
    def __init__(self,*args,**kwargs):
        '''
        @brief init the class
        @param[in/OPT] args - currently no required arguments
        @param[in/OPT] kwargs - keyword args as follows:
            engine - already initialized SamuraiMatlab class to use
        '''
        from samurai.base.SamuraiMatlab import SamuraiMatlab
        super().__init__(*args,**kwargs)
        self.options['engine'] = None
        for k,v in kwargs.items():
            self.options[k] = v
        if self.engine is None: #do this so we dont start up the engine to early
            self.engine = SamuraiMatlab(**self.options)

    def help(self,*args,**kwargs):
        print(self.engine.help(*args,**kwargs))
        
    def surf(self,*args,**kwargs): 
        '''
        @brief surface plot in matlab
            These inputs are the standard matlab inputs (except name/val pairs can be keyword args)
        '''
        #extract some arguments that require separate commands
        kwargs,funct_dict = self._clean_kwargs(**kwargs)
        fig = self.engine.surf(*args,**kwargs)
        self.engine.call_functs_from_dict(funct_dict,nargout=0) #call our functions
        return fig
    
    def plot(self,*args,**kwargs):
        '''
        @brief 2D plot in matlab
        '''
        #extract some arguments that require separate commands
        kwargs,funct_dict = self._clean_kwargs(**kwargs)
        fig = self.engine.plot(*args,**kwargs)
        self.engine.hold('on')
        self.engine.call_functs_from_dict(funct_dict,nargout=0) #call our functions
        return fig
    
    def _clean_kwargs(self,**kwargs):
        '''
        @brief this will extract a set of kwargs to run when provided as input parameters (e.g. xlim)
        @return normal kwargs, dictionary of extracted functions
        '''
          #extract some arguments that require separate commands
        funct_keys = ['xlim','ylim','zlim','xlabel','ylabel','zlabel','view','shading','title','colorbar']
        funct_dict = {k:kwargs.pop(k,None) for k in funct_keys} #get our function dictionary
        funct_dict = {k:v for k,v in funct_dict.items() if v is not None} #remove none values (not provided)
        return kwargs,funct_dict
        
    def is_figure(self,obj):
        '''
        @brief test whether an object is a figure
        @param[in] obj - the object to test
        @return true if is a figure, false otherwise
        '''
        return self.engine.get(obj,'type')=='figure'
    
    def is_axes(self,obj):
        '''
        @brief test whether an object is an axis
        @param[in] obj - the object to test
        @return true if is an axis, false otherwise
        '''
        return self.engine.get(obj,'type')=='axes'
            
if __name__=='__main__':
    surf_test = True
    plot_test = False
    translate_test = False
    if surf_test:
        sp = SamuraiPlotter('matlab')
        [X,Y] = np.mgrid[1:10:0.5,1:20]
        Z = np.sin(X)+np.cos(Y)
        fig = sp.surf(X,Y,Z,xlim=[0,20],zlabel='\lambda',shading='interp',colorbar=('XTick',[-1,1],'XTickLabel',[5,7]))
        #args = sp._translate_arguments(zlabel='X',shading='interp')
        #sp._surf_plotly(X,Y,Z,xlim=[0,20],zlabel='X',shading='interp',colorbar=('XTick',[-1,1],'XTickLabel',['A','B']))
        #sp._surf_matlab(X,Y,Z,xlim=[0.,20.],zlabel='X',shading='interp',colorbar=('XTick',[-1.,1.],'XTickLabel',['A','B']))
    if plot_test:
        sp = SamuraiPlotter('matlab',verbose=True)
        x = np.linspace(0,2*np.pi,1000)
        y = np.sin(x*5)
        sp.plot(x,y,displayname='test')
        sp.legend()
    if translate_test:
        #test translating our arguments
        sp = SamuraiPlotter('matplotlib')
        kargs = {'xlim':[0,20],'ylim':[10,20],'xlabel':'test'}
        rv = sp._run_plot_function('_translate_arguments',**kargs)
        print(rv)
    
    
    
    
    
    
    
    