# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:45:56 2019

@author: ajw5
"""

import numpy as np

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
            None yet!
        '''
        mynat = NatNetClient() #make the natnet client
        
        self.rigid_bodies = {}
        self.labeled_markers = {}
           
        mynat.rigidBodyListener = self.__rigid_body_listener
        mynat.labeledMarkerListener = self.__labeled_marker_listener
        
        mynat.run()
        
     #now make our listener functions
    def __rigid_body_listener(self,client,id,pos_m,rot_quat):
        '''
        @brief listener for rigid bodies from natnet
        @param[in] client - NatNet client that called this
        @param[in] id     - id of rigid body calling
        @param[in] pos_m - position of body in m
        @param[in] rot_quat - rotatiton of body in quaternion
        '''
        name = client.descriptions.get_name(id).decode()
        if name is not None:
            if not name in self.rigid_bodies:
                self.rigid_bodies[name] = {}
                self.rigid_bodies[name]['id'] = id
                
            self.rigid_bodies[name]['position_mm'] = np.array(pos_m)*1000
            self.rigid_bodies[name]['rotation'] = np.array(rot_quat) #TODO change to azel
            
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
            
        self.labeled_markers[id]['pos_mm'] = np.array(pos_m)*1000
        self.labeled_markers[id]['residual_mm'] = resid*1000
        
        
        
if __name__=='__main__':
    import time
    #test this out
    mymot = MotiveInterface()
    time.sleep(.1) #give time to get everything
    print(mymot.labeled_markers)
    
    