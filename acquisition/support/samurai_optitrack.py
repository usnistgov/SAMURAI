# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:45:56 2019

@author: ajw5
"""

import numpy as np
import six
import time

from samurai.acquisition.support.NatNetClient import NatNetClient
class MotiveInterface:
    '''
    @brief This is a class to interface with the NatNet server set up by Motive
        Motive is the software for optitrack cameras. This should allow us to easily
        access our live streaming values for our rigid bodies, and markers
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief intiialize the class
        @param[in/OPT] arg_options - keyword argument input as follows:
            init_wait - wait time after runing natnet client. This ensures data is populated (default 0.01)
        '''
        options = {}
        options['init_wait'] = 0.01
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        mynat = NatNetClient() #make the natnet client
        
        self.rigid_bodies = {}
        self.labeled_markers = {}
           
        mynat.rigidBodyListener = self.__rigid_body_listener
        mynat.labeledMarkerListener = self.__labeled_marker_listener
        
        mynat.run()
        time.sleep(options['init_wait'])
        
    def get_rigid_body_data(self,name,**arg_options):
        '''
        @brief get rigid body position data and generate some statistics on it
        @param[in] name - name of the rigid body to get info on
        @param[in] arg_options - keyword arguments as follows
                    num_samples - number of samples to take (default 100)
                    sample_wait_time - wait time between samples in seconds (default 1/num_samples seconds)
        @return dicitionary with rigid body info
        '''
        options = {}
        options['num_samples'] = 100
        options['sample_wait_time'] = 1./options['num_samples'] #seconds. how long each sample will take (0.01 seems safe)
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        #take many samples
        pos = []
        rot = []
        id = self.rigid_bodies[name]['id']
        for i in range(options['num_samples']):
            pos.append(self.rigid_bodies[name]['position_mm'])
            rot.append(self.rigid_bodies[name]['rotation'])
            time.sleep(options['sample_wait_time'])
        #now calculate the statistics and return a dictionary
        pos = self.calculate_statistics(np.array(pos),**arg_options)
        rot = self.calculate_statistics(np.array(rot),**arg_options)
        return {'id':id,'num_samples':options['num_samples'],'sample_wait_time':options['sample_wait_time'],'units':'mm','position':pos,'rotation':rot}
    
    def get_labeled_marker_data(self,id,**arg_options):
        '''
        @brief get rigid body position data and generate some statistics on it
        @param[in] id - id number of the marker to get
        @param[in] arg_options - keyword arguments as follows
                    num_samples - number of samples to take (default 100)
                    sample_wait_time - wait time between samples in seconds (default 1/num_samples seconds)
        @return dicitionary with rigid body info
        '''
        options = {}
        options['num_samples'] = 100
        options['sample_wait_time'] = 1./options['num_samples'] #seconds. how long each sample will take (0.01 seems safe)
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        #take many samples
        pos = []
        res = []
        for i in range(options['num_samples']):
            pos.append(self.labeled_markers[id]['position_mm'])
            res.append(self.labeled_markers[id]['residual_mm'])
            time.sleep(options['sample_wait_time'])
        #now calculate the statistics and return a dictionary
        pos = self.calculate_statistics(np.array(pos),**arg_options)
        res = self.calculate_statistics(np.array(res),**arg_options)
        return {'id':id,'num_samples':options['num_samples'],'sample_wait_time':options['sample_wait_time'],'units':'mm','position':pos,'residual':res}
        
    def get_position_data(self,id_name_dict,**arg_options):
        '''
        @brief get position data and generate some statistics on it return will be a dictionary of the values
        @param[in] id_name_dict - dictionary containing key value pairs in the form {name:id} for markers and {name:None} for rigid bodies
                            Marker names CAN NOT be the same as a rigid body name
        @param[in] arg_options - keyword arguments as follows
                    num_samples - number of samples to take (default 100)
                    sample_wait_time - wait time between samples in seconds (default 1/num_samples seconds)
                    include_raw_data - whether or not to include the raw measured data (default false)
        @return a dictionary with data on the positions for the points provided
        '''
        options = {}
        options['num_samples'] = 10
        options['sample_wait_time'] = 0.01 #seconds. how long each sample will take (0.01 seems safe)
        options['include_raw_data'] = False
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        data_dict = {}
        #check if its a rigid body or a point
        for key,val in six.iteritems(id_name_dict):
            #get the data
            if key in self.rigid_bodies:
                data = self.get_rigid_body_data(key,**options)
            elif val in self.labeled_markers:
                data = self.get_labeled_marker_data(val,**options)
                data['id'] = val
            else:
                raise KeyError(str(key)+" not in rigid bodies -- "+str(val)+" not in labeled markers")
            data_dict[key] = data #put the data into the dictionary
        
        return data_dict
    
    def write_marker_to_file(self,id_name_dict,out_path,**arg_options):
        '''
        @brief write a marker out to a file. the data input is the same as in self.get_position_data 
        @param[in] id_name_dict - dictionary containing key value pairs in the form {name:id}
            for markers and {name:None} for rigid bodies
            Marker names CAN NOT be the same as a rigid body name
        @param[in] out_path - output path the save the data to
        @param[in/OPT] arg_options - keyword arguments as follows:
            passed to self.get_position_data (see **arg_options of that method)
        '''
        options = {}
        for key,val in six.iteritems(arg_options):
            options[key] = val
        data_dict = self.get_position_data(id_name_dict,**options)
        #now write this out to our JSON file
        with open(out_path,'w+') as fp:
            json.dump(data_dict,fp,indent=4)
            
    @staticmethod
    def calculate_statistics(data,**arg_options):
        '''
        @brief calculate statistics on positional data
        @param[in] data - 2D numpy array of data with each row as a sample
        @param[in/OPT] arg_options - keyword arguents as follows:
            include_raw_data - whether or not to include the raw data in the dict
        @return dictionary of statistics. Must be lists so json serializable
        '''
        options = {}
        options['include_raw_data'] = False
        for key,val in six.iteritems(arg_options):
            options[key] = val
        
        statistics = {}
        statistics['mean'] = np.mean(data,axis=0).tolist()
        statistics['standard_deviation'] = np.std(data,axis=0).tolist()
        statistics['covariance_matrix'] = np.cov(np.transpose(data)).tolist()
        if(options['include_raw_data']):
            statistics['raw'] = data.tolist()
        return statistics
        
     #now make our listener functions
    def __rigid_body_listener(self,client,id,pos_m,rot_quat):
        '''
        @brief listener for rigid bodies from natnet
        @param[in] client   - NatNet client that called this
        @param[in] id       - id of rigid body calling
        @param[in] pos_m    - position of body in m
        @param[in] rot_quat - rotatiton of body in quaternion
        '''
        name = client.descriptions.get_name(id).decode()
        if name is not None:
            if not name in self.rigid_bodies:
                self.rigid_bodies[name] = {}
                self.rigid_bodies[name]['id'] = id
                
            self.rigid_bodies[name]['position_mm'] = np.array(pos_m)*1000
            rot = self.__convert_rotation(rot_quat)
            self.rigid_bodies[name]['rotation'] = np.array(rot) #TODO change to azel
            
    def __labeled_marker_listener(self,client,id,pos_m,resid):
        '''
        @brief listener for labeled markers from natnet
        @param[in] client - NatNet client that called this
        @param[in] id     - id of rigid body calling
        @param[in] pos_m - position of body in m
        @param[in] resid - residual calculated from uncertainty from 3D approximation from cameras
        '''
        if id not in self.labeled_markers:
            self.labeled_markers[id] = {}
            
        self.labeled_markers[id]['position_mm'] = np.array(pos_m)*1000
        self.labeled_markers[id]['residual_mm'] = resid*1000
        
    def __convert_rotation(self,rotation_quaternion):
        '''
        @brief change quaternion from optitrack to euler angles like in positioner format
        @param[in] rotation_quaternion - measured rotation from optitrack
        '''
        rot_euler = quaternion_to_euler(rotation_quaternion)
        rot = np.zeros(3)
        #change to our dimensions
        rot[0] = rot_euler[1]
        rot[1] = rot_euler[0]
        rot[2] = -1.*rot_euler[2]
        return rot
        
        
def quaternion_to_euler(quat):
        '''
        @brief change quaternion to euler angles
        Copied from https://stackoverflow.com/questions/53033620/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr?rq=1
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
        
        
        
if __name__=='__main__':
    import json
    mymot = MotiveInterface()
    
    id_dict = {}
    #rigid bodies
    id_dict['meca_head'] = None
    id_dict['origin']    = None
    #labeled markers
    id_dict['tx_antenna'] = 50436
    id_dict['cyl_1']      = 50359
    id_dict['cyl_2']      = 50358
    
    data = mymot.get_position_data(id_dict)
    print(json.dumps(data,indent=4))
    
    