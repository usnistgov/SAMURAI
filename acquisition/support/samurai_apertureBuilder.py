# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:44:35 2019

@author: ajw5
"""

import six
import numpy as np

class ApertureBuilder():
    '''
    @brief class to help build apertures for use with samurai system
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief initializer for the class
        @param[in/OPT] arg_options - keyword arguments as follows:
            trf_pos - position of tool reference frame (default is typical)
            wrf_pos - position of world reference frame (default is typical)
            comment_character - character to use for comments and header (default '#')
        '''
        #parse input arguments
        tool_length = 131 #length of tool off face in mm. Change for weird tools (or mounts)
        self.options['trf_pos'] = [0,0,tool_length,0,0,90] #tool reference frame (-90 to align axes with wrf). THE frame here is different and seems to be in ([z,y,z,gamma,beta,alpha]) compared to world frame
        self.options['wrf_pos'] = [tool_length+190,0,0,0,90,90]
        self.options['comment_character'] = '#'
        for key,val in six.iteritems(self.options):
            self.options[key] = val
        #initialize some other properties
        self.positions = None

    def add_positions(self,positions,**arg_options):
        '''
        @brief add positions to our aperture. 
            The positions should be a 6 element list or array in the form
            [X,Y,Z,Alpha,Beta,Gamma]. A list of these lists is also acceptable (or 2D array)
        @param[in] positions - single position or list of positions in format [X,Y,Z,Alpha,Beta,Gamma]
        @param[in/OPT] arg_options - keyword arguments for options as follows:
                None yet!
        '''
        positions = np.array(positions) #make a numpy array regardless
        if positions.shape[-1] != 6: #make sure number of positions is correct
            Exception("Malformed positions. Ensure positions have 6 elements." 
                      "For 2D arrays the second dimension should be of size 6")
        if not self.positions: #if no positions
            self.positions = positions
        else: #else concatenate
            self.positions = np.concatenate((self.positions,positions))
        
    #def 
        
            
       



  
#----------Some positionering things------------------#
        
    
def demo_planar():
    #start_pos_1 = [250,-100,80,0,90,0];
    #with trf = [0,0,131,0,-90,0] and wrf=[321,0,0,0,0,0]
    #with trf at tool tip and wrf directly below tip at base level when zeroed
    start_pos_1 = [60,-100,80,0,0,0]#x offset here from original by -190
    size_mm_1 = [0,200,200]
    step_size_mm_1 = [1,5,5]
    vals = gen_scan_grid_planar(start_pos_1,size_mm_1,step_size_mm_1)
    return vals

def demo_planar_center():
    sing_offset = 1 #offset to avoid singularity
    center_pos = [60+sing_offset,0,200+sing_offset,0,0,0]
    step       = [0,3,3]
    size       = [0,102,102]
    vals = gen_scan_grid_planar_from_center_point(center_pos,size,step)
    return vals
        
#generate from center point
def gen_scan_grid_planar_from_center_point(center_point,size_mm,step_size_mm):
    #just translate to edge position
    size_2 = np.zeros(6)
    size_2[0:3] = np.array(size_mm,dtype=float)/2
    start_position = np.array(center_point,dtype=float)-(np.array(size_2,dtype=float))
    return gen_scan_grid_planar(start_position,size_mm,step_size_mm)
        
#start position should be a 6 value location for MovePose
#this will start at start_position and move for the required step_size_mm [x,y,z]
#until it reaches the size_mm [x,y,z] values
#just generates the value
def gen_scan_grid_planar(start_position,size_mm,step_size_mm):
    if(len(start_position)!=6): #they all seem to require 6 args
        print("ERROR: Start position requires 6 elements")
        return -1
    #extract our values from inputs
    x_sp = start_position[0]
    y_sp = start_position[1]
    z_sp = start_position[2]
    alph = start_position[3]
    bet  = start_position[4]
    gam  = start_position[5]
    x_sm = size_mm[0]
    y_sm = size_mm[1]
    z_sm = size_mm[2]
    x_ssm = step_size_mm[0]
    y_ssm = step_size_mm[1]
    z_ssm = step_size_mm[2]
        #check if zero step (meaning we dont move)
    if not x_ssm:
        x_ssm=1; x_sm = 0
    if not y_ssm:
        y_ssm=1; y_sm = 0
    if not z_ssm:
        z_ssm=1; z_sm = 0
    #now build arrays for each dimension including last point
    x_pos = np.arange(x_sp,x_sp+x_sm+x_ssm,x_ssm)
    y_pos = np.arange(y_sp,y_sp+y_sm+y_ssm,y_ssm)
    z_pos = np.arange(z_sp,z_sp+z_sm+z_ssm,z_ssm)
    #now generate all of the points
    MG = np.meshgrid(x_pos,y_pos,z_pos,alph,bet,gam)
    #now reshape into an easily iterable thing
    point_list = np.transpose(MG).reshape((-1,6))
    return point_list


#shift all values by a given array of shift_value
def shift_scan_grid(vals,shift_value):
    if(len(shift_value)!=6): #they all seem to require 6 args
        print("ERROR: Start position requires 6 elements")
        return -1
    shifted_vals = vals+np.array(shift_value)
    return shifted_vals


def shift_scan_grid_csv(csv_name_in,shift_value,csv_name_out=''):
    '''
    @brief - shift values in a csv file
    @param[in] csv_name_in - name of input file to shift
    @param[in] sfhit_value - amount to shift positoins by
    @param[in] csv_name_out - output name. By default will overwrite input file
    @return - shifted values
    '''
    if(csv_name_out==''):
        csv_name_out = csv_name_in #overwrite
    pts = read_points_from_csv(csv_name_in) #read points
    shift_pts = shift_scan_grid(pts,shift_value) #shift points
    write_nparray_to_csv(csv_name_out,shift_pts)
    return shift_pts
   

def gen_offset_positions(start_plane,shift_value_list,flip_flg=True):
    '''
    @brief - This generates a set of positions with multiple planes using a list of shift values
    @param[in] - start_plane - reference plane from which everything is shifted
    @param[in] - shift_value_list - list of shift values to include in the output postitions
    @note - this function does not automatically include the start_plane in the output positions.
             [0,0,0,0,0,0] must be entered as an item in shift_value_list
    @param[in] - flip_flg - flip every other plane so we dont have to move back to the beginning
    @return - List of positoins for the robot to go to of the planes appended to one another
    '''
    shifted_planes = []
    i = 0 #shift plane count
    for shift_val in shift_value_list:
        positions = shift_scan_grid(start_plane,shift_val)
        if flip_flg: #if the flag tells, flip every other
            if i%2: #if odd plane
                positions = np.flipud(positions)
            i+=1
        shifted_planes.append(positions) #and write them to our list
        
    #now join into numpy array
    return np.concatenate(shifted_planes),shifted_planes

def minimize_point_distance(pts):
    '''
    @brief - change point order to minimize distance between each point
    @param[in] - pts - points to reorder
    @return - new_pts - copy of pts reordered to minimize distance traveled
    '''
    pts_new = pts.copy()
    return pts_new

def gen_offset_position_csv(csv_name_in, shift_value_list,flip_flg=True):
    '''
    @brief - Generate shifted csv file from input file positions. Outputs will be csv 
              files of separate shifted planes named as <csv_name_in>_shift_#.csv and all
              shifted plane positions together in <csv_name_in>_shift_full.csv
    @param[in] - csv_name_in - name of input csv positions to shift
    @param[in] - shift_value_list - list of shifts performed on the input positions
        @note - shift_value_list must inlcude [0,0,0,0,0,0] in order to include original positoins
    @param[in] - flip_flg - flip every other plane so we dont have to move back to the beginning
    '''
    start_plane = read_points_from_csv(csv_name_in) #read in data
    [shift_full,shift_list] = gen_offset_positions(start_plane,shift_value_list,flip_flg) #shifted values
    fname_no_extension = os.path.join(os.path.split(csv_name_in)[0],os.path.split(csv_name_in)[-1].split('.')[0]) #safely remove extension
    write_nparray_to_csv(fname_no_extension+'_shift_full.csv',shift_full) #write out full
    
    #now write out each shifted file in case we need it
    ind_shift_dir = os.path.join(os.path.split(csv_name_in)[0],'individual_shift_files')
    if not os.path.exists(ind_shift_dir):
        os.mkdir(ind_shift_dir) #make the directory
    for i in range(len(shift_list)):
        write_nparray_to_csv(os.path.join(ind_shift_dir,fname_no_extension)+'_shift_'+str(i)+'.csv',shift_list[i])
    return shift_full
    

def cat_positions_csv(csv_path_1,csv_path_2,csv_out_path,flip_flg=True):
    '''
    @brief - concatenate positions in two files
    @param[in] csv_path_1 - first file to concatenate
    @param[in] csv_path_2 - second file to concatenate
    @param[in] csv_out_path - output file name
    @param[in/optional] flip_flg - DEFAULT=True - do we flip(reverse) the second csv data
    '''
    #load the data
    data_1 = read_points_from_csv(csv_path_1)
    data_2 = read_points_from_csv(csv_path_2)
    if(flip_flg):
        data_2 = np.flipud(data_2) #reverse data if requested
    cat_data = np.concatenate((data_1,data_2)) #concatenate data
    write_nparray_to_csv(csv_out_path,cat_data) #write out
    return cat_data
    

#generate cylindrical scan grid around a given center point. Sweep -sweep_angle/2 to +sweep_angle/2 from origin
#sweep angle in degrees. Height in mm, radius in mm. step in degrees
#currently just for z axis
def gen_scan_grid_cylindrical(origin,radius,height,height_step_size_mm,sweep_angle,angle_step_size_degrees):
    #origin is given as [x,y,z,alpha,beta,gamma]
    if(len(origin)!=6): #they all seem to require 6 args
        print("ERROR: Origin requires 6 elements")
        return -1
    #unpack the values
    xo = float(origin[0])
    yo = float(origin[1])
    zo = float(origin[2])
    alpho = float(origin[3])
    beto  = float(origin[4])
    gamo  = float(origin[5])
    #along z axis gamma is our theta value
    #first calculate our angles
    #range is gamma+sweep/2 to gamma-sweep/2
    theta_start = gamo-float(sweep_angle)/2
    theta_end   = gamo+float(sweep_angle)/2
    theta_vals  = np.arange(theta_start,theta_end+angle_step_size_degrees,angle_step_size_degrees)
    #now calculate where our outer circle is
    #x = rcos(theta)+xo, y=rsin(theta)+yo, z=z;
    #start with the x,y values
    x = radius*np.cos(theta_vals*np.pi/180.)+xo; y = radius*np.sin(theta_vals*np.pi/180.)+yo
    #now generate z from origin to origin+height
    z = np.arange(zo,zo+height+height_step_size_mm,height_step_size_mm)
    #now combine to get all of our values
    #now tile this for the number of z locations
    x_tot     = np.tile(x,len(z))
    y_tot     = np.tile(y,len(z))
    z_tot  = np.repeat(z,len(theta_vals)) #repeat z for every theta
    theta_tot = np.tile(theta_vals,len(z))
    alph_tot  = np.repeat(alpho,theta_tot.size)
    bet_tot   = np.repeat(beto,theta_tot.size)
    #finally combine into positoins
    pos_vals = np.array([x_tot,y_tot,z_tot,alph_tot,bet_tot,theta_tot]).transpose()
    return pos_vals
    
    
def curve_planar_array_z(pts,curve_radius_mm):
    '''
    @brief - generate cylindrical array from planar array around z axis. This will curve about the center of the planar array
    @param[in] - pts - points for the planar array. Assuming a single array
    @param[in] - curve_radius - radius to curve along in millimeters
    @return - new curved cylindrical array
    '''
    planar_center = (np.max(pts,axis=0)-np.min(pts,axis=0))/2+np.min(pts,axis=0) #find the center of the points
    center_normal_angle_rad = np.arctan2(planar_center[1],planar_center[0]) #(y,x)
    pos_from_center = pts-planar_center #position relative to center
    
    #Our z wont change but we will calculate the new x and y from the old x and y
    x_pos_from_center = pos_from_center[:,0] #extract x values
    y_pos_from_center = pos_from_center[:,1] #extract y values
    dist_from_center = np.sqrt(x_pos_from_center**2+y_pos_from_center**2) #arc length along the new mapped circle
    angle_from_center_rad = dist_from_center/curve_radius_mm #angle by tracing arc length along mapped circle
    angle_sign = np.arctan2(y_pos_from_center,x_pos_from_center)+1e-20; angle_sign /= np.abs(angle_sign)
    circle_angle = (angle_from_center_rad+center_normal_angle_rad) #angle along circle for each point
    theta_vals = np.rad2deg(circle_angle) #theta angle of our robot in degrees
    x_shift = curve_radius_mm*(1-np.cos(circle_angle))
    y_shift = dist_from_center - np.sqrt(dist_from_center**2-x_shift**2)
    
    #now set the output
    pts_out = pts.copy() #make a copy of the input
    pts_out[:,5] = theta_vals*angle_sign #set the pointing of the horn
    pts_out[:,0] = pts[:,0]-x_shift #x change (ONLY WORKS FOR YZ PLANE RIGHT NOW)
    pts_out[:,1] = pts[:,1]-y_shift*angle_sign #y change
    return pts_out
    
#add points to stop at 
#def add_safety_manuever
    
#flip
def flip_alternate_rows(pts,row_length):
    '''
    @brief flip alternating rows for better pattern
    @param[in] - pts - points in aperture to flip rows
    @param[in] - row_length - number of points per aperture row (same as num columns)
    '''
    pts_new = pts.copy()
    num_rows = int(np.size(pts,0)//row_length)
    for i in range(1,num_rows,2): #every other row
        cur_row_st = i*35
        cur_row_end = ((i+1)*35)
        cur_row_vals = pts[cur_row_st:cur_row_end] #get the values of the current row
        flip_cr = np.flipud(cur_row_vals) #flip the values
        pts_new[cur_row_st:cur_row_end] = flip_cr
    return pts_new
    
#cylinder demo
def demo_cylinder():
    origin = [-50,0,100,0,0,0]
    sweep_angle = 90
    height = 100
    angle_step_size_degrees = 5
    height_step_size_mm = 20
    radius = 100
    return gen_scan_grid_cylindrical(origin,radius,height,height_step_size_mm,sweep_angle,angle_step_size_degrees)
    
#set our pose from a list of poses
#def move_pos_list
def write_nparray_to_csv(fname,np_array_vals):
    np.savetxt(fname,np_array_vals,delimiter=',')
    
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
#plot the points x,y,z,alpha,beta,gamma
def plot_points(data_points,fig_handle='default',magnitude=10):
    if(fig_handle=='default'): #if not provided, generate a figure
        fig = plt.figure()
    else:
        fig = fig_handle
    ax = fig.gca(projection='3d')
    [x,y,z] = data_points.transpose()[0:3]
    [u,v,w] = robot_to_vector(data_points,magnitude)
    ax.quiver(x,y,z,u,v,w)
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_zlabel('Z (mm)')
    ax.set_xlim(-175,175)   ; ax.set_ylim(-175,175)  ; ax.set_zlim(0,350)
    ax.scatter3D(0,0,0); ax.scatter3D(0,0,190)
    ax.text3D(0,0,190,'TCP Origin\n (Tip of antenna w/\n all joints zero)',horizontalalignment='left')
    ax.text3D(0,0,0,'WRF Origin',horizontalalignment='left')
    return fig

def plot_points_csv(csv_fname,fig_handle='default',magnitude=10):
    '''
    @brief - plot positions from a CSV file
    @param[in] csv_fname - file name of CSV positions
    @param[in] OPTIONAL fig_handle - what figure handle to use
    @param[in] OPTIONAL mangnitude - mangitude of plotted vectors
    '''
    data_points = read_points_from_csv(csv_fname)
    return plot_points(data_points,fig_handle,magnitude)
    

#load values in from CSV
def read_points_from_csv(fname):
    vals = np.loadtxt(fname,delimiter=',')
    return vals
    
#data in list of x,y,z,alpha,beta,gamma positions 
 #change robot positions to vector of antenna for plotting
def robot_to_vector(data_points,magnitude=1): #alpha beta gamma to normalized vector
    #assuming z axis is up, y is toward tx, and x is side to side. This does not calculate anything with y axis
    data = data_points.transpose() #make each direction (x,y,z,alpha,...) its own list of values
    alpha = np.array(data[3])/180.*np.pi; gamma = np.array(data[5])/180.*np.pi
    theta = gamma; phi = alpha
    u = magnitude*np.cos(phi)*np.cos(theta)
    v = magnitude*np.cos(phi)*np.sin(theta)
    w = np.sin(alpha)
    return np.array([u,v,w])
    
        
        
     