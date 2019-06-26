# -*- coding: utf-8 -*-
"""
Created on Mon May 20 15:04:22 2019

@author: ajw5
"""

import numpy as np

class SamuraiPlotter:
    '''
    @brief a class to abstract plotting between matplolib, matlab, and plotly, (and potentially others)
    '''
    def __init__(self,**arg_options):
        '''
        @brief initializer for plotting class
        @param[in/OPT] arg_options - keyword arguments as follows:
            verbose - whether or not to be verbose
            debug - extra verbose debug statements
            plot_order - list of strings for order of libs to try ['matlab','plotly','matplotlib'] acceptable
            matlab_engine - can pass an already running matlab engine
        '''
        self.options = {}
        self.options['verbose'] = False
        self.options['debug'] = True
        self.options['plot_order'] = ['matlab','plotly','matplotlib']
        self.options['matlab_engine'] = None
        for key,val in arg_options.items():
            self.options[key] = val
            
        self.matlab = None #matlab 
        self.plotly = None #plotly 
        self.matplotlib = None #matplotlib
        
    def _run_plot_function(self,plot_funct_name,*args,**kwargs):
        '''
        @brief loop through each of our programs to try and plot
        @param[in] plot_funct_name - name of plotting function (ie surf)
        @params[in] args - variable arguments to pass to pltting funciton
        @param[in] kwargs - keyword ags to pass to plotting funciton
        '''
        rv = None
        for pp in self.options['plot_order']:
            funct_name = '_'+plot_funct_name+'_'+pp
            funct = getattr(self,funct_name)
            try: 
                rv = funct(*args,**kwargs)
            except Exception as e: 
                print(e)
                print("{} Failed, trying next engine".format(pp))
        if not rv: #if nothing is returned
            raise Exception("No plotting library found or no value returned")
        return rv
        
    
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
        kwargs = {k.lower():v for k,v in kwargs.items()} #make all keys lowercase
        rv = self._run_plot_function('surf',*args,**kwargs)
        return rv
        
    def _surf_matlab(self,*args,**kwargs): 
        '''
        @brief surface plot in matlab
            These inputs are the standard matlab inputs (except name/val pairs can be keyword args)
        '''
        self._init_matlab() #initialize matlab
        #extract some arguments that require separate commands
        funct_keys = ['xlim','ylim','zlim','xlabel','ylabel','zlabel','view','shading','title','colorbar']
        funct_dict = {k:kwargs.pop(k,None) for k in funct_keys} #get our function dictionary
        funct_dict = {k:v for k,v in funct_dict.items() if v is not None} #remove none values (not provided)
        fig = self.matlab.surf(*args,**kwargs)
        self.matlab.call_functs_from_dict(funct_dict,nargout=0) #call our functions
        return fig
        
    def _surf_plotly(self,*args,**kwargs):
        '''
        @brief surface plot in plotly
        '''
        self._init_plotly()
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
            
        plotly_surf = [self.plotly_gobj.Surface(z = Y, x = X, y = Z,surfacecolor=plot_data,colorbar=cb)]
        layout = self.plotly_gobj.Layout(
            title=funct_dict.get('title',None),
            scene = dict(
                xaxis = dict(title=funct_dict.get('xlabel',None)),
                yaxis = dict(title=funct_dict.get('ylabel',None)),
                zaxis = dict(title=funct_dict.get('zlabel',None))
            ),
            autosize=True,
        )
            
        fig = self.plotly_gobj.Figure(data=plotly_surf,layout=layout)
        self.plotly.plot(fig,filename='plotly_out.html')
        return fig
    
    def _surf_matplotlib(self,*args,**kwargs):
        '''
        @brief surface plot in matplotlib
        '''
        self._init_matplotlib()
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
        
        fig = self.matplotlib.figure()
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(X,Y,Z,cmap = self.matplotlib_cm.coolwarm)
        ax.set_xlim(funct_dict.get('xlim',None))
        ax.set_ylim(funct_dict.get('ylim',None))
        ax.set_zlim(funct_dict.get('zlim',None))
        ax.set_xlabel(funct_dict.get('xlabel',None))
        ax.set_xlabel(funct_dict.get('ylabel',None))
        ax.set_xlabel(funct_dict.get('zlabel',None))
        cb = fig.colorbar(surf,ticks=xt)
        cb.ax.set_yticklabels(xtl)
        return fig

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
        kwargs = {k.lower():v for k,v in kwargs.items()} #make all keys lowercase
        rv = self._run_plot_function('plot',*args,**kwargs)
        return rv
    
    def _plot_matplotlib(self,*args,**kwargs):
        '''
        @brief 1D plot in matplotlib
        '''
        self._check_arg_count(len(args),2,2) #must have exactly 2 args
        self._init_matplotlib()
        fig = self.matplotlib.figure()
        ax = fig.gca()
        kwargs = self._matlab2matplotlib(ax,**kwargs)
        ax.plot(*args,**kwargs)
        return fig

    
    ###########################################################################
    ####### for all unimplemented, try to call from the first value in plot order
    ###########################################################################
    def __getattr__(self,name):
        '''
        @brief this function will be called when the attribute or method 
            is not found. The call will look in the first value of
            self.options['plot_order'] for the method or property
        @param[in] name - attribute name
        '''
        plotter_name = self.options['plot_order'][0]
        init_plotter_funct = getattr(self,'_init_'+plotter_name)
        init_plotter_funct() #init the plotter
        plotter = getattr(self,plotter_name) #get the plotter
        attr = getattr(plotter,name)
        return attr
        
        
    ###########################################################################
    ####### Initializer
    ###########################################################################    
    def _init_matlab(self):
        '''
        @brief initialize the matlab plotter (dont open if already open)
        '''
        if not self.matlab:
            from samurai.analysis.support.MatlabPlotter import MatlabPlotter
            self.matlab = MatlabPlotter(engine=self.options['matlab_engine'],**self.options)
            
    def _init_matplotlib(self):
        '''
        @brief initialize matplotlib plotter
        '''
        if not self.matplotlib:
            import matplotlib.pyplot as plt
            from matplotlib import cm
            self.matplotlib = plt
            self.matplotlib_cm = cm
            
    def _init_plotly(self):
        '''
        @brief initialize plotly
        '''
        if not self.plotly:
            import plotly.graph_objs as go
            import plotly.offline as ploff
            from mpl_toolkits.mplot3d import Axes3D
            self.plotly = ploff
            self.plotly_gobj = go

    ###########################################################################
    ####### generic internal funcitons
    ########################################################################### 
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
    def _matlab2matplotlib(self,ax,**kwargs):
        '''
        @brief this will run the corresponding functions for provided matlab key/val arguemnts
            (e.g. if xlim is passed, run ax.set_xlim). 
            This will only remove key value pairs with specified functions
        @param[in] ax - axis to run the arguments on
        @param[in/OPT] kwargs - keyword args to run
        @return kwargs dictionary with specified functions removed
        '''
        ax_funct_dict = {}
        #add limits to dictionary
        for d in ['x','y','z']:
            ax_funct_dict.update({'{}lim'.format(d):'set_{}lim'.format(d)})
        #add labels
        for d in ['x','y','z']:
            ax_funct_dict.update({'{}label'.format(d):'set_{}label'.format(d)})
            
        #now get a list of the functions specified and remove from kwargs
        funct_list = list(ax_funct_dict.values())
        arg_dict = {k:kwargs.pop(k,None) for k in funct_list} #get our function dictionary
        arg_dict = {k:v for k,v in arg_dict.items() if v is not None} #remove none values (not provided)
        
        #now loop through and run the functions with the arguments
        #ax_funct_return_dict = {} #return 'function':rv key/value pair
        for k,v in arg_dict.items():
            funct = getattr(ax,ax_funct_dict[k]) #now get the method to run form the axis
            rv = funct(v)
            #ax_funct_return_dict[v,rv] #matplotlib function name/return-value
        return kwargs
    
    
            
if __name__=='__main__':
    plot_test = True
    surf_test = False
    if surf_test:
        sp = SamuraiPlotter(verbose=True,plot_order=['plotly','matlab'])
        [X,Y] = np.mgrid[1:10:0.5,1:20]
        Z = np.sin(X)+np.cos(Y)
        #sp.plotly(X,Y,Z,xlim=[0,20],zlabel='X',shading='interp')
        #sp._surf_plotly(X,Y,Z,xlim=[0,20],zlabel='X',shading='interp',colorbar=('XTick',[-1,1],'XTickLabel',['A','B']))
        sp._surf_matlab(X,Y,Z,xlim=[0.,20.],zlabel='X',shading='interp',colorbar=('XTick',[-1.,1.],'XTickLabel',['A','B']))
    if plot_test:
        sp = SamuraiPlotter(verbose=True,plot_order=['matplotlib'])
        x = np.linspace(0,2*np.pi,1000)
        y = np.sin(x*5)
        sp.plot(x,y)
    
    
    
    
    
    
    
    