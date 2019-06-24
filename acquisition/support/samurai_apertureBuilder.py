# -*- coding: utf-8 -*-
"""
Created on Fri May 10 11:44:35 2019

@author: ajw5
"""

import six
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import os

#positional index constants
x_index = 0
y_index = 1
z_index = 2
elevation_index = 3
azimuth_index = 4
polarization_index = 5

v1_to_v2_convert = np.array([[0,1,0,0,0,0],
                             [0, 0,1,0,0,0],
                             [1, 0,0,0,0,0],
                             [0, 0,0,1,0,0],
                             [0, 0,0,0,0,1],
                             [0, 0,0,0,1,0]]).transpose()

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
        self.options = {}
        self.options['trf_pos'] = [0,0,tool_length,0,0,90] #tool reference frame (-90 to align axes with wrf). THE frame here is different and seems to be in ([z,y,z,gamma,beta,alpha]) compared to world frame
        self.options['wrf_pos'] = [tool_length+190,0,0,0,90,90]
        self.options['input_units'] = 'mm'
        self.options['output_units'] = 'mm'
        self.options['comment_character'] = '#'
        for key,val in six.iteritems(self.options):
            self.options[key] = val
        #initialize some other properties
        self.positions = None
       
    def load(self,file_path):
        '''
        @brief load in csv file positions (overwrite any current positions)
        @param[in] file_path - path of file to load (assume csv for now)
        '''
        ext = os.path.splitext(file_path)[-1].strip('.')
        if ext=='csv':
            #load values in from CSV
            self.positions = np.loadtxt(file_path,delimiter=',',comments=self.options['comment_character'])
            

    def write(self,file_path):
        '''
        @brief write out file positions
        @param[in] file_path - path of file to write to 
        '''
        ext = os.path.splitext(file_path)[-1].strip('.')
        header = self.build_header()
        if ext=='csv':
            np.savetxt(file_path,self.positions,delimiter=',',header=header,comments=self.options['comment_character'])
            
    def build_header(self):
        '''
        @brief build our output header
        @return string of the output header
        '''
        header_lines = []
        header_lines.append('TRF = '+str(self.options['trf_pos']))
        header_lines.append('WRF = '+str(self.options['wrf_pos']))
        header_str = ''
        for l in header_lines:
            header_str += l+' \n'
        return header_str
        
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
        self.validate_position(positions)
        if not np.array(self.positions).shape: #if no positions
            self.positions = positions
        else: #else concatenate
            self.positions = np.concatenate((self.positions,positions))
            
    def shift_positions(self,shift_value):
        '''
        @brief shift our positions by a given amount. shifts self.positions
        @param[in] shift_value - value to shift each positino by in [x,y,z,alpha,beta,gamma]
        '''
        self.validate_position(shift_value)
        self.positions += np.array(shift_value)
        
    def gen_planar_aperture(self,start_position,size=None,step=None,numel=None):
        '''
        @brief generate a planar aperture given a start position,size, and step, or number of elements
            at least two of the three (size,step,numel) must be specified
        @param[in] start_position - [x,y,z,alpha,beta,gamma] position for corner
        @param[in/OPT] size - total size of the aperture in input units (default mm) [x,y,z]
        @param[in/OPT] step - step size in input units (default mm) [x,y,z]
        @param[in/OPT] numel - number of elements in each direction of the array [x,y,z]
        @note overwrites self.positions
        '''
        self.validate_position(start_position)
        #ensure we have enough inputs to run
        input_array = np.array([size,step,numel])
        if len(np.where(input_array!=None))<2:
            raise Exception("At least two keyword arguments must be specified")
        if (np.array([size])==None).any(): #if none
            size = (np.array(numel)-1)*np.array(step) #-1 to account for arange +1
        elif (np.array([step])==None).any(): #if none
            size = np.array(size)/np.array(numel)
        #extract our values from inputs
        x_sp = start_position[0]
        y_sp = start_position[1]
        z_sp = start_position[2]
        alph = start_position[3]
        bet  = start_position[4]
        gam  = start_position[5]
        x_sm = size[0]
        y_sm = size[1]
        z_sm = size[2]
        x_ssm = step[0]
        y_ssm = step[1]
        z_ssm = step[2]
            #check if zero step (meaning we dont move)
        if not x_ssm:
            x_ssm=1; x_sm = 0
        if not y_ssm:
            y_ssm=1; y_sm = 0
        if not z_ssm:
            z_ssm=1; z_sm = 0
        #now build arrays for each dimension including last point
        x_pos = np.arange(x_sp,x_sp+x_sm+x_ssm*.5,x_ssm) #the 0.5 prevents rounding errors
        y_pos = np.arange(y_sp,y_sp+y_sm+y_ssm*.5,y_ssm)
        z_pos = np.arange(z_sp,z_sp+z_sm+z_ssm*.5,z_ssm)
        #now generate all of the points
        MG = np.meshgrid(x_pos,y_pos,z_pos,alph,bet,gam,indexing='ij') #traverse x positions first
        #now reshape into an easily iterable thing
        point_list = np.transpose(MG).reshape((-1,6))
        self.positions = point_list
    
    def gen_planar_aperture_from_center(self,center_point,size=None,step=None,numel=None):
        '''
        @brief generate a planar aperture given an aperture center point,size, and step
        @param[in] center point - [x,y,z,alpha,beta,gamma] position of center
        @param[in] size - total size of the aperture in input units (default mm) [x,y,z]
        @param[in] step - step size in input units (default mm) [x,y,z]
        @note overwrites self.positions
        '''
        size_2 = np.zeros(6)
        if np.array(size)==None:
            size = (np.array(numel)-1)*np.array(step)
        size_2[0:3] = np.array(size,dtype=float)/2
        start_position = np.array(center_point,dtype=float)-(np.array(size_2,dtype=float))
        self.gen_planar_aperture(start_position,size,step,numel)
    
    def gen_cylindrical_aperture(self,origin,radius,height,height_step_size_mm,sweep_angle,angle_step_size_degrees):
        '''
        @brief generate a cylindrical aperture
        @param[in] origin - [x,y,z,alpha,beta,gamma] position for cylinder center
        @param[in] radius - radius of cylinder in mm
        @param[in] height - height of the cylinder to generate
        @param[in] height_step_size_mm - step size in vertical direction in mm
        @param[in] sweep_angle - angle to sweep in degrees
        @param[in] angle_step_size_degrees - azimuthal angular step in degrees
        @return 2D array of positions
        '''
        self.validate_position(origin)
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
        z = radius*np.cos(theta_vals*np.pi/180.)+zo; x = radius*np.sin(theta_vals*np.pi/180.)+xo
        #now generate z from origin to origin+height
        y = np.arange(yo,yo+height+height_step_size_mm,height_step_size_mm)
        #now combine to get all of our values
        #now tile this for the number of z locations
        #these x,y,z values are swapped because of the changed reference frame
        z_tot     = np.tile(z,len(z))
        x_tot     = np.tile(x,len(z))
        y_tot  = np.repeat(y,len(theta_vals)) #repeat z for every theta
        theta_tot = np.tile(theta_vals,len(y))
        alph_tot  = np.repeat(alpho,theta_tot.size)
        bet_tot   = np.repeat(beto,theta_tot.size)
        #finally combine into positoins
        pos_vals = np.array([x_tot,y_tot,z_tot,alph_tot,bet_tot,theta_tot]).transpose()
        return pos_vals
            
    def curve_array(self,curve_radius_mm):
        '''
        @brief - curve our current points into a cylinder. Ideally this will be a planar array to start
        @param[in] - curve_radius - radius to curve along in millimeters
        '''
        pts = self.positions
        planar_center = (np.max(pts,axis=0)-np.min(pts,axis=0))/2+np.min(pts,axis=0) #find the center of the points
        center_normal_angle_rad = np.arctan2(planar_center[1],planar_center[0]) #(y,x)
        pos_from_center = pts-planar_center #position relative to center
        
        #Our z wont change but we will calculate the new x and y from the old x and y
        x_pos_from_center = pos_from_center[:,x_index] #extract x values
        y_pos_from_center = pos_from_center[:,y_index] #extract y values
        dist_from_center = np.sqrt(x_pos_from_center**2+y_pos_from_center**2) #arc length along the new mapped circle
        angle_from_center_rad = dist_from_center/curve_radius_mm #angle by tracing arc length along mapped circle
        angle_sign = np.arctan2(y_pos_from_center,x_pos_from_center)+1e-20; angle_sign /= np.abs(angle_sign)
        circle_angle = (angle_from_center_rad+center_normal_angle_rad) #angle along circle for each point
        theta_vals = np.rad2deg(circle_angle) #theta angle of our robot in degrees
        x_shift = curve_radius_mm*(1-np.cos(circle_angle))
        y_shift = dist_from_center - np.sqrt(dist_from_center**2-x_shift**2)
        
        #now set the output
        self.positions[:,azimuth_index] = theta_vals*angle_sign #set the pointing of the horn
        self.positions[:,x_index] = pts[:,x_index]-x_shift #x change (ONLY WORKS FOR YZ PLANE RIGHT NOW)
        self.positions[:,y_index] = pts[:,y_index]-y_shift*angle_sign #y change
    
    def get_vectors(self,mag=1):
        '''
        @brief get positions in vector format
        @param[in/OPT] mag - magnitude of vectors
        @return [x,y,z,u,v,w] vectors
        '''
        data = self.positions.transpose() #make each direction (x,y,z,alpha,...) its own list of values
        [x,y,z] = data[0:3] #get x,y,z values (they dont change for vectors)
        alpha = np.array(data[3])/180.*np.pi
        beta  = np.array(data[4])/180.*np.pi
        #gamma = np.array(data[5])/180.*np.pi
        theta = np.deg2rad(alpha); phi = np.deg2rad(beta)
        u = mag*np.sin(phi)*np.sin(theta)
        w = mag*np.sin(phi)*np.cos(theta)
        v = np.cos(alpha)
        return np.array([x,y,z,u,v,w])
    
    def get_polarization_lines(self,mag=5):
        '''
        @brief get xyzuvw coordinates of a quiverplot line to show the polarization at each position
        @param[in/OPT] mag - magnitude of the line (+- the point)
        @return np.array([x,y,z,u,v,w])
        '''
        #default quiver options for drawing these lines
        default_quiver_opts = dict(pivot='middle')
        #now get our vectors to go through out position
        data = self.positions.transpose() #make each direction (x,y,z,alpha,...) its own list of values
        [x,y,z] = data[0:3] #get x,y,z values (they dont change for vectors)
        alpha = np.array(data[3])/180.*np.pi
        beta  = np.array(data[4])/180.*np.pi
        #gamma = np.array(data[5])/180.*np.pi
        theta = np.deg2rad(alpha+90); phi = np.deg2rad(beta+90)
        u = np.cos(theta)
        v = mag*np.sin(phi)*np.sin(theta)
        w = mag*np.sin(phi)*np.cos(theta)
        return np.array([x,y,z,u,v,w]),default_quiver_opts
        
    def plot(self,fig_handle=None,magnitude=5):
        '''
        @brief plot the aperture points. We flip y and z for nicer view angle
        @param[in/OPT] fig_handle - handle to figure to plot points on
        @param[in/OPT] magnitude - magnitude of vector positions to plot
        '''
        if not fig_handle: #if not provided, generate a figure
            fig = plt.figure()
        else:
            fig = fig_handle
        ax = fig.gca(projection='3d')
        [x,y,z,u,v,w] = self.get_vectors(mag=magnitude) #flip y and z so z is horizontal direction
        ax.quiver(x,z,y,u,v,w)
        #ax.plot(x,y,z)
        ax.set_xlabel('X (mm)'); ax.set_ylabel('Z (mm)'); ax.set_zlabel('Y (mm)')
        ax.set_xlim(-175,175)   ; ax.set_ylim(-175,175)  ; ax.set_zlim(0,350)
        ax.scatter3D(0,0,0); ax.scatter3D(0,0,190)
        ax.text3D(0,0,190,'TCP Origin\n (Tip of antenna w/\n all joints zero)',horizontalalignment='left')
        ax.text3D(0,0,0,'WRF Origin',horizontalalignment='left')
        [[xp,yp,zp,up,vp,wp],quivp_params] = self.get_polarization_lines(mag=2)
        ax.quiver(xp,zp,yp,up,wp,vp,color='g',arrow_length_ratio=0,**quivp_params)
        return fig
    
    def plot_path_2D(self,fig_handle=None):
        '''
        @brief plot the 2D path of the robot for the points provided
        @param[in/OPT]fig_handle - handle to figure to plot points on
        '''
        if not fig_handle: #if not provided, generate a figure
            fig = plt.figure()
        else:
            fig = fig_handle
        ax = fig.gca()
        [x,y] = self.get_vectors()[:2] #get xy
        ax.scatter(x,y,s=10,c='blue')
        #now plot arrows
        xd = np.diff(x); yd = np.diff(y)
        mag = np.sqrt(xd**2+yd**2)
        u = xd/mag; v = yd/mag
        xa = x[:-1]+u; ya = y[:-1]+v
        arrow_mod = 4
        xa = xa[::arrow_mod]; ya = ya[::arrow_mod]
        u = u[::arrow_mod]; v = v[::arrow_mod]
        ax.quiver(xa,ya,u,v,color='r',width=0.0025,angles='xy',scale=100)
        ax.plot(x,y,c='r')
        [[xp,yp,zp,up,vp,wp],quivp_params] = self.get_polarization_lines()
        ax.quiver(xp,yp,up,vp,color='g',headlength=0,headaxislength=0,**quivp_params)
        return fig
    
    def optimize_aperture(self):
        '''
        @brief optimize our aperture by making the robot travel the smallest distance possible
        @todo implement 2-opt https://en.wikipedia.org/wiki/2-opt to solve traveling saleman problem here
        '''
        pass
    
    def flip_alternate_rows(self,row_length):
        '''
        @brief flip alternating rows for better pattern with cylinder and planar data
        @param[in] - row_length - number of points per aperture row (same as num columns)
        '''
        pts = self.positions.copy()
        num_rows = int(np.size(pts,0)//row_length)
        for i in range(1,num_rows,2): #every other row
            cur_row_st = i*row_length
            cur_row_end = ((i+1)*row_length)
            cur_row_vals = pts[cur_row_st:cur_row_end] #get the values of the current row
            flip_cr = np.flipud(cur_row_vals) #flip the values
            self.positions[cur_row_st:cur_row_end] = flip_cr
    
    def validate_position(self,position):
        '''
        @brief validate positional input (for now just check shape)
        @param[in] position - position to validate (or list of positions/2D array)
        '''
        if np.array(position).shape[-1] != 6:
            raise Exception("Positions must have 6 elements ([x,y,z,alpha,beta,gamma])")
            
    def concatenate(self,ap2):
        '''
        @brief add concat 2 apertures
        @param[in] ap2 - second aperture to concatenate with
        '''
        self.add_positions(ap2.positions)
        
    def change_reference_frame(self,rotation_matrix,external_positions=None):
        '''
        @brief change our reference frame using a rotation matrix. This matrix should be 6 by 6
        @param[in] rotation_matrix - 6 by 6 matrix for rotation
        @param[in/OPT] external_positions - external positions to change. If none operate on self.positions
        '''
        if external_positions is None:
            self.positions = np.matmul(self.positions,rotation_matrix)
        else:
            return np.matmul(external_positions,rotation_matrix)
        
    def flipud(self):
        '''
        @brief reverse the order of positions (flip up/down)
        '''
        self.positions = np.flipud(self.positions)


  
#----------Some functions that might not be best in the class------------------#
    
def convert_v1_file_to_v2_file(in_path,out_path):
    '''
    @brief convert original tool reference frame of samurai (metafile v1) to new reference frame (metafile v2)
    @param[in] in_path - v1 input file path
    @param[in] out_path - v2 output file path
    '''
    myap = ApertureBuilder()
    myap.load(in_path)
    myap.change_reference_frame(v1_to_v2_convert)
    myap.write(out_path)

def shift_scan_grid_file(shift_value,in_path,out_path):
    '''
    @brief - shift values in a csv file
    @param[in] in_path - name of input file to shift 
    @param[in] out_path - output name to write to 
    @param[in] shift_value - amount to shift positoins by
    '''
    myap = ApertureBuilder()
    myap.load(in_path)
    myap.shift_positions(shift_value)
    myap.write(out_path)

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
    pass
    '''
    @todo reimpliment with class
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
    '''

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
    '''
    @todo in class
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
    '''
    pass

def cat_positions_file(in_path_1,in_path_2,out_path,flip_flg=True):
    '''
    @brief - concatenate positions in two files
    @param[in] csv_path_1 - first file to concatenate
    @param[in] csv_path_2 - second file to concatenate
    @param[in] csv_out_path - output file name
    @param[in/OPT] flip_flg - do we flip(reverse) the second set of points (default True)
    '''
    myap1 = ApertureBuilder()
    myap2 = ApertureBuilder()
    myap1.load(in_path_1)
    myap2.load(in_path_2)
    if(flip_flg):
        myap2.flipud()
    myap1.concatenate(myap2)
    myap1.write(out_path)
    

def plot_points_file(in_path,mag=10):
    '''
    @brief - plot positions from a file and plot 2D path
    @param[in] in_path - path to position file
    @param[in/OPT] fig_handle - what figure handle to use
    @param[in/OPT] mangnitude - mangitude of plotted vectors
    @return 3D plot of points, 2D plots of path the points will be run in
    '''
    myap = ApertureBuilder()
    myap.load(in_path)
    fig_3d = myap.plot(magnitude=mag)
    path_fig = myap.plot_path_2D()
    return fig_3d,path_fig
    

if __name__=='__main__':
    myap = ApertureBuilder()
    myap2 = ApertureBuilder()
    '''
    #load from file
    v1_planar_path = r'C:\SAMURAI\git\samurai\acquisition\support\sweep_files\v1\positions_SAMURAI_planar.csv'
    myap.load(v1_planar_path)
    myap2.load(v1_planar_path)
    myap.change_reference_frame(v1_to_v2_convert)
    myap2.change_reference_frame(v1_to_v2_convert)
    '''
    #about lambda/2 at 40GHz
    lam_at_forty = 2.99e8/40e9/2*1000 #lambda at 40GHz in mm
    myap.gen_planar_aperture_from_center([0,125,60,0,0,0],step=[lam_at_forty,lam_at_forty,0],numel=[35,35,1])
    myap.flip_alternate_rows(row_length=35)
    #myap.concatenate(myap2)
    #myap.plot()
    #myap.plot_path_2D()
    fout1 = 'sweep_files/samurai_planar_vp.csv'
    myap.write(fout1)
    myap.shift_positions([0,0,0,0,0,90])
    fout2 = 'sweep_files/samurai_planar_hp.csv'
    myap.write(fout2)
    fout_dp = 'sweep_files/samurai_planar_dp.csv'
    cat_positions_file(fout1,fout2,fout_dp)
    
    #myap.load(fout_dp)
    #myap.plot_path_2D()
    

        
        
     