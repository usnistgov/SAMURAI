# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 09:09:10 2019

@author: ajw5
"""

import numpy as np
import time
import json
import re
from numbers import Number #for testing if its an id
from datetime import datetime #for timestamping

from samurai.acquisition.instrument_control.NatNetClient import NatNetClient
from samurai.acquisition.instrument_control.SamuraiPositionTrack import quaternion_to_euler
from samurai.acquisition.instrument_control.InstrumentControl import Instrument,InstrumentError
from samurai.base.SamuraiDict import SamuraiDict


class MotiveInterface(Instrument):
    '''
    @brief This is a class to interface with the NatNet server set up by Motive
        Motive is the software for optitrack cameras. This should allow us to easily
        access our live streaming values for our rigid bodies, and markers.
        We are still extending the Instrument class here to try and keep some sort
        of consistency even though it won't use many parts of it. Allows for isinstance(-,Instrument) to be true  
    '''
    
    def __init__(self,**arg_options):
        '''
        @brief intiialize the class  
        @param[in/OPT] arg_options - keyword argument input as follows:
            init_wait - wait time after starting natnet client. This ensures data is populated (default 0.1)  
        '''
        options = {}
        options['init_wait'] = 0.5
        for key,val in arg_options.items():
            options[key] = val
        super().__init__(None)
        
        self._rigid_bodies_dict = {}    #the listeners look to these. Rigid body markers must stay static with respect to one another
        self._labeled_markers_dict = {} #single labeled markers given by id. Used for non-static marker tracking (e.g. bislide)
         
        self.connect('127.0.0.1') #connect to the Motive software
        time.sleep(options['init_wait']) #sleep to let data be populated
        
    def _query(self,item,**arg_options):
        '''
        @brief get position data and generate some statistics on it return will be a dictionary of the values  
        @param[in] item - rigid body name, marker id, or 
                                dictionary containing key value pairs in the form {name:id} for markers,
                                {name:None} for rigid bodies, and {name:'markers'} for rigid body marker positions.
                                Marker names CAN NOT be the same as a rigid body name  
        @param[in] arg_options - keyword arguments as follows  
                    - num_samples - number of samples to take (default 100)  
                    - sample_wait_time - wait time between samples in seconds (default 1/num_samples seconds)  
                    - include_raw_data - whether or not to include the raw measured data (default false)  
                    - marker_name - when item is a marker id, this can be used to give a name to the marker. Default is id# as an int  
        @return a dictionary with data on the positions for the points requested  
        '''
        options = {}
        options['num_samples'] = 10
        options['sample_wait_time'] = 0.01 #seconds. how long each sample will take (0.01 seems safe)
        options['include_raw_data'] = False
        options['marker_name'] = None
        for key,val in arg_options.items():
            options[key] = val
        item_dict = self._get_item_dict(item)
        
        #put single query into dict
        raw_data_dict = SamuraiDict() #raw measurement dictionary
        md = {'labeled_marker'      :MotiveMarkerData,
              'rigid_body'          :MotiveRigidBodyData,
              'rigid_body_markers'  :MotiveRigidBodyMarkerData}
        type_dict = self._get_meas_type(item_dict)
        for k,v in type_dict.items():
            if v == 'rigid_body_markers' and not k.endswith('_markers'): #add _markers to key
                k+='_markers'
            raw_data_dict[k] = md[v]() #initialize the data storage
        #handle any rigid body marker groups first
        # start our sampling here of rigid bodies and markers
        for i in range(options['num_samples']): #interleave all of our sampling
            for k,v in item_dict.items():
                if type_dict[k]=='labeled_marker': #if it is a number then we assume a marker id
                    sample = self._measure_single(v)
                elif type_dict[k]=='rigid_body':
                    sample = self._measure_single(k)
                elif type_dict[k]=='rigid_body_markers':
                    sample = self._get_rigid_body_marker_data(k) #already handled outside of loop
                    if not k.endswith('_markers'):
                        k +='_markers' #append markers in case we also get the rigid body
                else: raise Exception("Something went wrong...")
                raw_data_dict[k].add_sample(sample)
            time.sleep(options['sample_wait_time'])
        #now add info
        for k,v in raw_data_dict.items():
            if k in list(item_dict.keys()): #try to get _markers key
                raw_data_dict[k]['info'] = self.get_info({k:item_dict[k]})
            else: #otherwise try and get the usual
                raw_data_dict[k]['info'] = self.get_info({k:item_dict[k.replace('_markers','')]})
        #now pack into data struct
        for k in raw_data_dict.keys():
            raw_data_dict[k].calculate_statistics(**options)
        #add timestamp
        raw_data_dict['timestamp'] = str(datetime.now())
        return raw_data_dict
    
    #alias for backward compatability
    get_position_data = _query
    
    def _measure_single(self,item,**arg_options):
        '''
        @brief query motive for position info on a given item  
        @param[in] item - item to get position of. can be a rigid body name
                or the id of a marker  
        @param[in/OPT] **arg_options - keyword args as follows:  
            - all passed to getter function  
        '''
        options = {}
        for key,val in arg_options.items():
            options[key] = val
        md = {'labeled_marker':self._get_labeled_marker_data,
              'rigid_body'    :self._get_rigid_body_data    }
        mytype = list(self._get_meas_type(item).values())[0] #assume 1 value
        get_fun = md[mytype]
        d = get_fun(item,**arg_options)
        return d
    
    def get_info(self,item,**arg_options):
        '''
        @brief query motive for info on an item  
        @param[in] item - item to get position of. can be a rigid body name
                or the id of a marker or a dict of values  
        @param[in/OPT] **arg_options - keyword args as follows:  
            - all passed to getter function  
        '''
        options = {}
        for key,val in arg_options.items():
            options[key] = val
        mytype = list(self._get_meas_type(item).values())[0] #assume 1 value
        k = list(item.keys())[0]; v = list(item.values())[0]
        if mytype=='labeled_marker': #if it is a number then we assume a marker id
            d = self._get_labeled_marker_info(v)
        elif mytype=='rigid_body':
            d = self._get_rigid_body_info(k)
        elif mytype=='rigid_body_markers':
            k = k.replace('_markers','') #remove _markers if its there
            d = self._get_rigid_body_marker_info(k) #already handled outside of loop
        else: raise Exception("no matching data type {}".format(mytype))
        return d
    
    def _get_meas_type(self,item_dict):
        '''
        @brief get the type of measurement from an item_dict  
        @param[in] item_dict - item dictionary to get the types from. This will also handle
            strings or numbers for fast getting of a single measurement  
        @return dictionary with each key matched to either 'labeled_marker','rigid_body'  
        '''
        type_dict = {}; lm_rv='labeled_marker'; rb_rv='rigid_body'
        rbm_rv = 'rigid_body_markers'
        if isinstance(item_dict,Number)  : return {item_dict:lm_rv}
        elif isinstance(item_dict,str)   : return {item_dict:rb_rv}
        elif isinstance(item_dict,dict):
            for k,v in item_dict.items():   
                if isinstance(v,Number): type_dict[k] = lm_rv #marker
                elif v == 'markers' or k.endswith('_markers'): type_dict[k] = rbm_rv
                elif v is None: type_dict[k] = rb_rv #check this last in case we have _makerser
                else: raise InstrumentError("No matching measurement type found for {}:{}".format(k,v))
        else:
            raise InstrumentError("Cannot match measurement of type {}".format(type(item_dict)))
        return type_dict
            
    def _get_item_dict(self,item,**kwargs):
        '''
        @brief get a dictionary of items (if not already)  
        @param[in] item - item input  
        '''
        options = {}
        options['marker_name'] = None
        for key,val in kwargs.items():
            options[key] = val
        if isinstance(item,Number): #then we have a marker id
            if options['marker_name'] is None:
                options['marker_name'] = item
            item_dict = {options['marker_name']:item}
        elif isinstance(item,str): #then its a single rigid body
            item_dict = {item:None}
        elif isinstance(item,dict): #if its a dict dont do anything
            item_dict = item
        else: #otherwise unsupported
            raise InstrumentError("Unsupported item type {}".format(type(item)))
        return item_dict
        
    def _get_rigid_body_data(self,name,**arg_options):
        '''
        @brief get rigid body position data and generate some statistics on it  
        @param[in] name - name of the rigid body to get info on  
        @return [position,rotation]  
        '''
        if name not in self._rigid_bodies_dict: #has not been measured or wrong name
            raise InstrumentError("\'{}\' is not a measured rigid body".format(name))
        #get the values
        pos = self._rigid_bodies_dict[name]['position_mm']
        rot = self._rigid_bodies_dict[name]['rotation']
        return pos,rot
    
    def _get_rigid_body_info(self,name,**arg_options):
        '''@brief get any other stored info of a given rigid body'''
        return self._rigid_bodies_dict[name]['info']
    
    @property
    def rigid_bodies(self):
        '''@brief return a list of the rigid bodies'''
        return list(self._rigid_bodies_dict.keys())
    
    def _get_rigid_body_marker_data(self,name,**arg_options):
        '''
        @brief get rigid body marker positions and generate some statistics on it  
        @param[in] name - name of the rigid body to get info on  
        @return dictionary of labeled marker datas  
        '''
        name = name.replace('_markers','') #remove _markers if its there
        rbd = self._get_rigid_body_data(name,**arg_options) #first get the rigid body locations
        #then get the marker offsets
        offsets = self.connection.rigid_body_descriptions[name]['marker_offsets']
        pos_list = np.array(rbd[0])+np.array(offsets)
        ret_vals = [[pval,[np.nan]] for pval in pos_list]
        #now shape this correctly
        return ret_vals
    
    def _get_rigid_body_marker_info(self,name,**arg_options):
        '''@brief get any other stored info of a given rigid body'''
        return self._rigid_bodies_dict[name]['info']
    
    def _get_labeled_marker_data(self,id,**arg_options):
        '''
        @brief get rigid body position data and generate some statistics on it  
        @param[in] id - id number of the marker to get  
        @return [position,residual]  
        '''
        if id not in self._labeled_markers_dict: #has not been measured or wrong name
            raise InstrumentError("\'{}\' is not a measured marker ID".format(id))
        #get the values
        pos = self._labeled_markers_dict[id]['position_mm']
        res = self._labeled_markers_dict[id]['residual_mm']
        return pos,res
    
    def _get_labeled_marker_info(self,id,**arg_options):
        '''@brief get any other info of a given labeled marker'''
        return self._labeled_markers_dict[id]['info']
    
    @property
    def labeled_markers(self):
        '''@brief return list of labeled marker ids'''
        return list(self._labeled_markers_dict.keys())
    
#%% Instrument commands
   
    def _connect(self,address):
        ''' @brief connect to the natnet server client '''
        self.connection = NatNetClient(address)
        #add our listeners for data
        self.connection.rigidBodyListener = self._rigid_body_listener
        self.connection.labeledMarkerListener = self._labeled_marker_listener
        #run the client
        self.connection.run()
        
    #functions that dont relate to motive
    def _write(self):
        raise Exception
    def _write_binary(self):
        raise Exception
    def _read(self):
        raise Exception
    def _read_binary(self):
        raise Exception
    def _query_binary(self):
        raise Exception

#%% natnet listeners
        
     #now make our listener functions
    def _rigid_body_listener(self,client,id,pos_m,rot_quat,**kwargs):
        '''
        @brief listener for rigid bodies from natnet  
        @param[in] client   - NatNet client that called this  
        @param[in] id       - id of rigid body calling  
        @param[in] pos_m    - position of body in m  
        @param[in] rot_quat - rotation of body in quaternion  
        '''
        name = client.rigid_body_descriptions.get_name(id)
        if name is not None:
            if not name in self._rigid_bodies_dict:
                self._rigid_bodies_dict[name] = {}
                self._rigid_bodies_dict[name]['id'] = id
                
            self._rigid_bodies_dict[name]['position_mm'] = np.array(pos_m)*1000
            rot = self._convert_rotation(rot_quat)
            self._rigid_bodies_dict[name]['rotation'] = np.array(rot)
            self._rigid_bodies_dict[name]['info'] = SamuraiDict()
            self._rigid_bodies_dict[name]['info'].update(kwargs) #any other info
           
#    def _rigid_body_markers_listener(self,client,id,mids,**kwargs):
#        '''
#        @brief listener for rigid bodies from natnet
#        @param[in] client   - NatNet client that called this
#        @param[in] id       - id of rigid body calling
#        @param[in] mid      - list of marker ids in the rigid body
#        '''
#        name = client.descriptions.get_name(id).decode()
#        if name is not None:
#            if not name in self._rigid_bodies_dict:
#                self._rigid_body_markers_dict[name] = {}
#                self._rigid_body_markers_dict[name]['id'] = id
#            #add the list of rigid bodies
#            self._rigid_body_markers_dict[name]['marker_id'] = np.array(rot)
#            self._rigid_body_markers_dict[name]['info'] = SamuraiDict()
#            self._rigid_body_markers_dict[name]['info'].update(kwargs) #any other info
            
            
    def _labeled_marker_listener(self,client,id,pos_m,resid,**kwargs):
        '''
        @brief listener for labeled markers from natnet  
        @param[in] client - NatNet client that called this  
        @param[in] id     - id of rigid body calling  
        @param[in] pos_m - position of body in m  
        @param[in] resid - residual calculated from uncertainty from 3D approximation from cameras  
        '''
        if id not in self._labeled_markers_dict:
            self._labeled_markers_dict[id] = {}
            
        self._labeled_markers_dict[id]['position_mm'] = np.array(pos_m)*1000
        self._labeled_markers_dict[id]['residual_mm'] = resid*1000
        self._labeled_markers_dict[id]['info'] = SamuraiDict()
        self._labeled_markers_dict[id]['info'].update(kwargs) #any other info
        
    def _convert_rotation(self,rotation_quaternion):
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
    
    def get_distance(self,marker_a,marker_b,**kwargs):
        '''
        @brief calculate the distance between two markers (or rigid bodies)
        @param[in] marker_a - first marker to start measurement from
        @param[in] marker_b - second marker to measure too
        @param[in/OPT] kwargs - passed to query calls
        @note This calculates marker_b-marker_a for location (no rotation)
        @return Dictionary with mean:[x,y,z] distances and euler:d (absolute euler distance)
        '''
        #first get the locations of our data
        distance_dict = SamuraiDict()
        ma_pos = self.query(marker_a,**kwargs)[marker_a]['position']
        mb_pos = self.query(marker_b,**kwargs)[marker_b]['position']
        
        #now lets get the x,y,z distances
        distance_dict['mean'] = mb_pos['mean']-ma_pos['mean']
        distance_dict['euler']  = np.sqrt(np.sum(distance_dict['mean']**2))
        distance_dict['standard_deviation'] = mb_pos['standard_deviation']+ma_pos['standard_deviation']
        distance_dict['timestamp'] = str(datetime.now())
        return distance_dict
        
        
    
#%% class to hold rigid body data
from samurai.acquisition.instrument_control.SamuraiPositionTrack import SamuraiPositionDataDict

class MotiveRigidBodyData(SamuraiPositionDataDict):
    '''@brief class to hold rigid body data'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self['units'] = 'mm'
        self.add_data_set(['position','rotation'])
        
class MotiveMarkerData(SamuraiPositionDataDict):
    '''@brief class to hold labeled marker data'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self['units'] = 'mm'
        self.add_data_set(['position','residual'])
        
class MotiveRigidBodyMarkerData(SamuraiDict):
    '''@brief class to hold list of rigid body markers'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self['units'] = 'mm'
        self['data'] = []
        #self['info'] = SamuraiDict()
        
    def add_sample(self,sample):
        '''
        @brief add a sample to our data.  
        @param[in] sample here should be a  dict with ids and marker samples (position/residual)  
        @note this needs to be a dictionary because the rigid body may not have the same markers
            on every measurement if one is lost. (we dont want to combine different markers)  
        '''
        num_markers = len(sample) #assume sample is correct size
        while len(self['data'])<num_markers: #add data if needed
            self['data'].append(MotiveMarkerData())
        for i,s in enumerate(sample):
            self['data'][i].add_sample(s) #add the sample to the marker
            
    def calculate_statistics(self,**kwargs):
        '''@brief calculate statistics'''
        for i in range(len(self['data'])):
            self['data'][i].calculate_statistics(**kwargs)
        
#%% some unittesting
import unittest
class TestMotiveInterface(unittest.TestCase):
    '''@brief class to test motive interface'''
    
    def test_get_rigid_body(self):
        #'''@brief test getting rigid body data'''
        mymot = MotiveInterface()
        rbname = mymot.rigid_bodies[0] #get the first rigid body
        try:
            mymot.query(rbname) #try to get the 
        except InstrumentError as e:
            self.fail("Exception Raised : {}".format(str(e)))
            
    def test_get_labeled_marker(self):
        #'''@brief test getting labeled marker data'''
        mymot = MotiveInterface()
        lmid = mymot.labeled_markers[0] #get the first rigid body
        try:
            mymot.query(lmid) #try to get the 
        except InstrumentError as e:
            self.fail("Exception Raised : {}".format(str(e)))
            
    def test_get_rigid_body_markers(self):
        mymot = MotiveInterface()
        rbname = mymot.rigid_bodies[0] #get the first rigid body
        try:
            v = mymot.query({rbname:'markers'}) #try to get the 
            v = mymot.query({rbname+'_markers':None})
            #print(v)
        except InstrumentError as e:
            self.fail("Exception Raised : {}".format(str(e)))


#%%
if __name__=='__main__':
    testa = False #print data to json
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMotiveInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    mymot = MotiveInterface()
    #time.sleep(3)
    #mymot.query(50336)
    #time.sleep(0.5)
    #qdict = {'meca_head_markers':'markers','meca_head':None,'marker_1':50148}
    #a = mymot.query({'meca_head':'markers'})
    #d = mymot.query(qdict)
    #b = mymot.query(74027)
    #c = mymot.query({'meca_head':None,'test':74027})
    
        
        
        
        