# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 08:36:19 2019

@author: ajw5
"""

import scipy.interpolate as interp
import numpy as np

def increase_meshing(X,multiplier=4):
    '''
    @brief increase the mesh density of a 2D data set. We will interpolate between the points
    @param[in] X meshgrid of X values
    @return Xn the value with increased meshing
    '''
    X = np.array(X)
    #first lets get larger meshes for x and y. Here we want to include the original points through
    grid_old = np.meshgrid(np.arange(0,X.shape[0],1),np.arange(0,X.shape[1],1)) #grid for the original points
    #new grid has 4 times the points
    grid_new_x = np.arange(0,X.shape[0],1/multiplier)
    grid_new_y = np.arange(0,X.shape[1],1/multiplier)
    #now lets get a new meshing from these shapes
    tck = interp.bisplrep(grid_old[0],grid_old[1],X) #must be on grid to use this
    Xn  = interp.bisplev (grid_new_x,grid_new_y,tck).transpose()
    return Xn

def increase_meshing_3D(X,Y,Z,multiplier=4):
    '''
    @breif increase meshing of 3D data set (eg beamformed data)
    @param[in] X x data (2d array meshgrid)
    @param[in] Y y data (2d array meshgrid)
    @param[in] Z z data (2d array values)
    @return Xn,Yn,Zn data with increased (interpolated) mesh
    '''
    #get densified x and y meshes
    Xn = increase_meshing(X,multiplier)
    Yn = increase_meshing(Y,multiplier)
    #now interp our z (assume arbitrary grid)
    points = np.array([X.flatten(),Y.flatten()]).transpose()
    new_points = np.array([Xn.flatten(),Yn.flatten()]).transpose()
    Zn = interp.griddata(points,Z.flatten(),new_points)
    Zn = np.reshape(Zn,Xn.shape)
    return Xn,Yn,Zn
    

#function test
if __name__=="__main__":
    
    
    [X,Y] = np.meshgrid(range(35),range(35))
    Z = np.meshgrid(range(35),range(35))[0]
    Xna = increase_meshing(X)
    Yna = increase_meshing(Y)
    
    [Xnb,Ynb,Zn] = increase_meshing_3D(X,Y,Z)
    
    #now plot
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X,Y,Z,
                       linewidth=0, antialiased=False)
    ax.plot_surface(Xnb,Ynb,Zn,
                       linewidth=0, antialiased=False)
    