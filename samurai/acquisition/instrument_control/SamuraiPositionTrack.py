# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:45:56 2019

@author: ajw5
"""

import numpy as np
import time
import json

from samurai.base.SamuraiDict import SamuraiDict

#%% class for Dictionary of SamuraiPositionData classes
class SamuraiPositionDataDict(SamuraiDict):
    '''@brief a class to hold a list of samurai position data'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        self.data_sets = [] #separately hold names of data sets
        super().__init__(*args,**kwargs)
        self['info'] = SamuraiDict() #location for any extra information
        
    def load(self,*args,**kwargs):
        '''@brief load but change items to SamuraiPositionData'''
        super().load(*args,**kwargs)
        for k in self.keys(): #change to position data
            if k in self.data_sets:
                self[k] = SamuraiPositionData(self[k])
        
    def add_data_set(self,names):
        '''
        @brief add a new data set to the list  
        @param[in] names - name(s) to use as keys for data set(s)  
        '''
        if not np.ndim(names): #make sure we always have a list
            names = [names] 
        for n in names:
            self[n] = SamuraiPositionData()
            self.data_sets.append(n)
            
    def calculate_statistics(self,**arg_options):
        '''
        @brief calculate statistics from self.raw_data and save to self  
        @param[in/OPT] arg_options - keyword values as follows:  
            - include_raw_data - whether or not to include raw data  
        '''
        for k in self.keys():
            if k!='info' and k!='units':
                self[k].calculate_statistics(**arg_options)
            
    def add_sample(self,data,**kwargs):
        '''
        @brief add a raw data sample or samples.   
        @param[in] data - sample to add. This should be a list of 
                lists where len(data[i])==len(self). This assumes input ordering 
                is the same as self.keys  
        @param[in/OPT] arg_options - keyword args as follows  
            - key_order - list of key orders to save the data. otherwise just get self.keys()
        '''
        options = {}
        options['key_order'] = [k for k in self.keys() if k!='info' and k!='units']
        for k,v in kwargs.items():
            options[k] = v
        #now add it to our sets
        for i,k in enumerate(options['key_order']): #iterate through each list item
            self[k].add_sample(data[i])
    
    #alias
    append = add_sample

#%% class for data from position tracking

from samurai.base.SamuraiDict import SamuraiDict
class SamuraiPositionData(SamuraiDict):
    '''@brief class to store position data and calculate info on it'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self.raw = [] #initialize raw data array
        
    def add_sample(self,data,**arg_options):
        '''
        @brief add a raw data sample  
        @param[in] data - sample to add (one at a time)  
        @param[in/OPT] arg_options - keyword args as follows  
            - None yet!
        '''
        self.raw.append(data)
    #alias
    append = add_sample
        
    def set(self,raw_data,**arg_options):
        '''
        @brief set the raw data for the position_data and calculate statistics  
        @param[in] raw_data - 2D numpy array of raw data with each row as a sample  
        @param[in/OPT] arg_options - keyword args passed to self._calculate_statistics()  
            - include_raw_data - whether or not to include raw data in dictionary (default false)
        @note right now these are not actually part of the dictionary  
        '''
        self.raw = raw_data
        self.calculate_statistics(**arg_options)
        
    def calculate_statistics(self,**arg_options):
        '''
        @brief calculate statistics from self.raw_data and save to self  
        @param[in/OPT] arg_options - keyword values as follows:  
            - include_raw_data - whether or not to include raw data
        '''
        options = {}
        options['include_raw_data'] = True
        for key,val in arg_options.items():
            options[key] = val
            
        if not len(self.raw):
            raise Exception("No data in self.raw")
            
        raw = np.array(self.raw)
        
        self['mean'] = np.mean(raw,axis=0)
        self['standard_deviation'] = np.std(raw,axis=0)
        #self['covariance_matrix'] = np.cov(np.transpose(raw))
        if(options['include_raw_data']):
            self['raw'] = raw
        
    
        
#%% some useful spatial functions
            
def quaternion_to_euler(quat):
        '''
        @brief change quaternion to euler angles  
        @cite https://stackoverflow.com/questions/53033620/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr?rq=1  
        '''
        x = quat[0]
        y = quat[1]
        z = quat[2]
        w = quat[3]
        import math
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        X = math.degrees(math.atan2(t0, t1))

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        Y = math.degrees(math.asin(t2))

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        Z = math.degrees(math.atan2(t3, t4))

        return X, Y, Z
        
    
def rotate_3d(axis,angle,coords):
    '''
    @brief rotate a set of 3d points given in X,Y,Z  
    @param[in] axis - 'x','y','z', or a string (e.g. 'xyz') of them to generate the rotation matrix  
    @param[in] angle - value or list of values(for len(axis)>1) in degrees to rotate   
    @param[in] coords - list of [x,y,z] (i.e. [[x1,y1,z1],[x2,y2,z2],...]) coordinate values to rotate
        Should be of shape (n,3) where n is the number of coordinates  
    '''
    R = generate_rotation_matrix_3d(axis,angle)
    rotated_coords = np.matmul(coords,R.transpose()) #same as np.matmul(R,coords.transpose()).transpose()
    return rotated_coords

def generate_rotation_matrix_3d(axis,angle):
    '''
    @brief generate a rotation matrix for a set of rotations  
    @param[in] axis - 'x','y','z', or a string (e.g. 'xyz') of them to generate the rotation matrix  
    @param[in] angle - value or list of values(for len(axis)>1) in degrees to rotate (just like alpha beta gamma of meca)   
    '''
    if not hasattr(angle,'__iter__'):
        angle = [angle] #make sure we can iterate over
    rot_mats = [] #list of individual rotation matrices
    for i,ax in enumerate(axis): #generate individual rotation matrices
        cur_angle = angle[i]
        if ax=='x':
            rm = np.array([[1,0                             ,0                            ],
                           [0,np.cos(np.deg2rad(cur_angle)),-np.sin(np.deg2rad(cur_angle))],
                           [0,np.sin(np.deg2rad(cur_angle)), np.cos(np.deg2rad(cur_angle))]])
            rot_mats.append(rm)
        if ax=='y':
            rm = np.array([[ np.cos(np.deg2rad(cur_angle)),0,np.sin(np.deg2rad(cur_angle))],
                           [0                            ,1,0                             ],
                           [-np.sin(np.deg2rad(cur_angle)),0,np.cos(np.deg2rad(cur_angle))]])
            rot_mats.append(rm)
        if ax=='z':
            rm = np.array([[ np.cos(np.deg2rad(cur_angle)),-np.sin(np.deg2rad(cur_angle)),0],
                           [ np.sin(np.deg2rad(cur_angle)), np.cos(np.deg2rad(cur_angle)),0],
                           [0                             ,0                            ,1]])
            rot_mats.append(rm)
    #now multiply to get our rotation matrix
    R = np.array([[1,0,0], #start with identity matrix
                  [0,1,0],
                  [0,0,1]])
    for rm in rot_mats: #generate rotational matrix
        R = np.matmul(R,rm)
    return R

import unittest
class TestPositionTrack(unittest.TestCase):
    '''@brief unittesting for Position tracking'''
    def test_generate_rotation_matrix_3d(self):
        rot_axis_orders = [] #rotation axis orders
        rot_angle_list  = [] #angles [alpha,beta,gamma] to rotate
        rot_comp_list   = [] #correct matrices to compare to
        #rotation 1
        rot_axis_orders.append('xyz')
        rot_angle_list.append([0,0,0])
        rot_comp_list.append(np.array([[ 1.000, 0.000, 0.000],
                                       [ 0.000, 1.000, 0.000],
                                       [ 0.000, 0.000, 1.000]]))
        #rotation 2
        rot_axis_orders.append('xyz')
        rot_angle_list.append([0,0,25])
        rot_comp_list.append(np.array([[ 0.906,-0.423, 0.000],
                                       [ 0.423, 0.906, 0.000],
                                       [ 0.000, 0.000, 1.000]]))
        #rotation 3
        rot_axis_orders.append('xyz')
        rot_angle_list.append([0,-33,25])
        rot_comp_list.append(np.array([[ 0.760,-0.354,-0.545],
                                       [ 0.423, 0.906, 0.000],
                                       [ 0.494,-0.230, 0.839]]))
        #rotation 4
        rot_axis_orders.append('xyz')
        rot_angle_list.append([32,-33,25])
        rot_comp_list.append(np.array([[ 0.760,-0.354,-0.545],
                                       [ 0.097, 0.891,-0.444],
                                       [ 0.643, 0.285, 0.711]]))
        #now calculate the values
        rot_data = zip(rot_axis_orders,rot_angle_list,rot_comp_list)
        for rot_ax,rot_ang,rot_comp in rot_data:
            rot_mat = generate_rotation_matrix_3d(rot_ax,rot_ang)
            fail_msg = 'Failure with rotation {}:{}.\n {} \nNOT EQUAL\n {}'.format(rot_ax,rot_ang,np.round(rot_mat,3),rot_comp)
            self.assertTrue(np.all(np.round(rot_mat,3)==rot_comp),msg=fail_msg)
            
    def test_position_data(self):
        #'''@brief test position data class'''
        pd = SamuraiPositionData()
        np.random.seed(1234)
        data = np.random.rand(10)
        mean = np.mean(data)
        std  = np.std(data)
        for d in data:
            pd.add_sample(d)
        pd.calculate_statistics()
        self.assertEqual(mean,pd['mean'])
        self.assertEqual(std,pd['standard_deviation'])
        
    def test_position_data_dict(self):
        pdd = SamuraiPositionDataDict()
        pdd.add_data_set(['test1','test2'])
        np.random.seed(1234)
        data = np.random.rand(10,2,2)
        mean = np.mean(data,axis=0)
        std  = np.std(data,axis=0)
        for dd in data:
            pdd.add_sample(dd)
        pdd.calculate_statistics()
        pddv = [v for k,v in pdd.items() if k!='info']
        for i,v in enumerate(pddv):
            self.assertTrue(np.all(mean[i]==v['mean']))
            self.assertTrue(np.all(std[i]==v['standard_deviation']))
            
    
        
if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPositionTrack)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    testb = False #test rotational matrix

    if(testb):
        #this is checked with https://mecademic.com/resources/Euler-angles/Euler-angles.html
        #should be identity matrix
        print("\n----------------\n Test A")
        rota_ax = 'xyz'
        rota_an = [0,0,0]
        rota = generate_rotation_matrix_3d(rota_ax,rota_an)
        print(rota)
        print("Should be")
        rc = np.array([[ 1.000, 0.000, 0.000],
                        [ 0.000, 1.000, 0.000],
                        [ 0.000, 0.000, 1.000]])
        print(rc, np.all(rc==np.round(rota,3)))
        
        #should be
        print("\n----------------\n Test B")
        rotb_ax = 'xyz'
        rotb_an = [0,0,25]
        rotb = generate_rotation_matrix_3d(rotb_ax,rotb_an)
        print(rotb)
        print("\nShould be")
        rc =np.array([[ 0.906,-0.423, 0.000],
                        [ 0.423, 0.906, 0.000],
                        [ 0.000, 0.000, 1.000]])
        print(rc, np.all(rc==np.round(rotb,3)))
    
        #should be
        print("\n----------------\n Test C")
        rotc_ax = 'xyz'
        rotc_an = [0,-33,25]
        rotc = generate_rotation_matrix_3d(rotc_ax,rotc_an)
        print(rotc)
        print("\nShould be")
        rc = np.array([[ 0.760,-0.354,-0.545],
                        [ 0.423, 0.906, 0.000],
                        [ 0.494,-0.230, 0.839]])
        print(rc, np.all(rc==np.round(rotc,3)))
    
        #should be
        print("\n----------------\n Test D")
        rotd_ax = 'xyz'
        rotd_an = [32,-33,25]
        rotd = generate_rotation_matrix_3d(rotd_ax,rotd_an)
        print(rotd)
        print("\nShould be")
        rc = np.array([[ 0.760,-0.354,-0.545],
                        [-0.604,-0.077,-0.793],
                        [ 0.239, 0.932,-0.273]])
        print(rc, np.all(rc==np.round(rotd,3)))
    
        
    
    