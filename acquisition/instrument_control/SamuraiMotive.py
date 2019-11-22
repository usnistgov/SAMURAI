# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 09:09:10 2019

@author: ajw5
"""

import numpy as np
import time
import json
from numbers import Number #for testing if its an id

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
        options['init_wait'] = 0.1
        for key,val in arg_options.items():
            options[key] = val
        super().__init__(None)
        
        self.rigid_bodies = {}    #the listeners look to these. Rigid body markers must stay static with respect to one another
        self.labeled_markers = {} #single labeled markers given by id. Used for non-static marker tracking (e.g. bislide)
         
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
                    num_samples - number of samples to take (default 100)
                    sample_wait_time - wait time between samples in seconds (default 1/num_samples seconds)
                    include_raw_data - whether or not to include the raw measured data (default false)
                    marker_name - when item is a marker id, this can be used to give a name to the marker. Default is id_#
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
        
        #else: do nothing. We should only have isinstance(item,dict)==True from here
        raw_data_dict = SamuraiDict() #raw measurement dictionary
        md = {'labeled_marker':MotiveMarkerData,
              'rigid_body'    :MotiveRigidBodyData}
        type_dict = self._get_meas_type(item_dict)
        for k,v in type_dict.items():
            raw_data_dict[k] = md[v]() #initialize the data storage
        # start our sampling here
        for i in range(options['num_samples']): #interleave all of our sampling
            for k,v in item_dict.items():
                if type_dict[k]=='labeled_marker': #if it is a number then we assume a marker id
                    sample = self._measure_single(v)
                elif type_dict[k]=='rigid_body':
                    sample = self._measure_single(k)
                else: raise Exception("Something went wrong...")
                raw_data_dict[k].append(sample)
            time.sleep(options['sample_wait_time'])
        #now pack into data struct
        for k in raw_data_dict.keys():
            raw_data_dict[k].calculate_statistics(**options)
        return raw_data_dict
    
    #alias for backward compatability
    get_position_data = _query
    
    def _measure_single(self,item,**arg_options):
        '''
        @brief query motive for position info on a given item
        @param[in] item - item to get position of. can be a rigid body name
                or the id of a marker
        @param[in/OPT] **arg_options - keyword args as follows:
            -all passed to getter function
        '''
        options = {}
        for key,val in arg_options.items():
            options[key] = val
        md = {'labeled_marker':self._get_labeled_marker_data,
              'rigid_body'    :self._get_rigid_body_data     }
        get_fun = md[self._get_meas_type(item)]
        d = get_fun(item,**arg_options)
        return d
    
    def _get_meas_type(self,item_dict):
        '''
        @brief get the type of measurement from an item_dict
        @param[in] item_dict - item dictionary to get the types from. This will also handle
            strings or numbers for fast getting of a single measurement
        @return dictionary with each key matched to either 'labeled_marker','rigid_body'
        '''
        type_dict = {}; lm_rv='labeled_marker'; rb_rv='rigid_body'
        if isinstance(item_dict,Number): return lm_rv
        if isinstance(item_dict,str)   : return rb_rv
        for k,v in item_dict.items():
            if isinstance(v,Number): type_dict[k] = lm_rv #marker
            elif v is None: type_dict[k] = rb_rv #body
            else: raise InstrumentError("No matching measurement type found for {}:{}".format(k,v))
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
                options['marker_name'] = 'id_{}'.format(item)
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
        if name not in self.rigid_bodies: #has not been measured or wrong name
            raise InstrumentError("\'{}\' is not a measured rigid body".format(name))
        #get the values
        pos = self.rigid_bodies[name]['position_mm']
        rot = self.rigid_bodies[name]['rotation']
        return pos,rot
    
    def _get_labeled_marker_data(self,id,**arg_options):
        '''
        @brief get rigid body position data and generate some statistics on it
        @param[in] id - id number of the marker to get
        @return [position,residual]
        '''
        if id not in self.labeled_markers: #has not been measured or wrong name
            raise InstrumentError("\'{}\' is not a measured marker ID".format(id))
        #get the values
        pos = self.labeled_markers[id]['position_mm']
        res = self.labeled_markers[id]['residual_mm']
        return pos,res
    
    def write_marker_to_file(self,id_name_dict,out_path,**arg_options):
        '''
        @brief write a marker out to a file. the data input is the same as in self.get_position_data 
            By default include the raw measurement data
        @param[in] id_name_dict - dictionary containing key value pairs in the form {name:id}
            for markers and {name:None} for rigid bodies
            Marker names CAN NOT be the same as a rigid body name
        @param[in] out_path - output path the save the data to
        @param[in/OPT] arg_options - keyword arguments as follows:
            passed to self.get_position_data (see **arg_options of that method)
        '''
        options = {}
        options['include_raw_data'] = True
        for key,val in arg_options.items():
            options[key] = val
        data_dict = self.get_position_data(id_name_dict,**options)
        #now write this out to our JSON file
        with open(out_path,'w+') as fp:
            json.dump(data_dict,fp,indent=4)
    
#%% Instrument commands
   
    def _connect(self,address):
        ''' @brief connect to the natnet server client '''
        mynat = NatNetClient(address)
        mynat.rigidBodyListener = self._rigid_body_listener
        mynat.labeledMarkerListener = self._labeled_marker_listener
        mynat.run()
        
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
    def _rigid_body_listener(self,client,id,pos_m,rot_quat):
        '''
        @brief listener for rigid bodies from natnet
        @param[in] client   - NatNet client that called this
        @param[in] id       - id of rigid body calling
        @param[in] pos_m    - position of body in m
        @param[in] rot_quat - rotation of body in quaternion
        '''
        name = client.descriptions.get_name(id).decode()
        if name is not None:
            if not name in self.rigid_bodies:
                self.rigid_bodies[name] = {}
                self.rigid_bodies[name]['id'] = id
                
            self.rigid_bodies[name]['position_mm'] = np.array(pos_m)*1000
            rot = self._convert_rotation(rot_quat)
            self.rigid_bodies[name]['rotation'] = np.array(rot) #TODO change to azel
            
    def _labeled_marker_listener(self,client,id,pos_m,resid):
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
    
#%% class to hold rigid body data
from samurai.acquisition.instrument_control.SamuraiPositionTrack import SamuraiPositionDataDict

class MotiveRigidBodyData(SamuraiPositionDataDict):
    '''@brief class to hold rigid body data'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self.add_data_set(['position','rotation'])
        
class MotiveMarkerData(SamuraiPositionDataDict):
    '''@brief class to hold labeled marker data'''
    def __init__(self,*args,**kwargs):
        '''@brief constructor'''
        super().__init__(*args,**kwargs)
        self.add_data_set(['position','residual'])
        
#%% some unittesting
import unittest
class TestMotiveInterface(unittest.TestCase):
    '''@brief class to test motive interface'''
    def test_get_rigid_body(self):
        mymot = MotiveInterface()
        rbname = list(mymot.rigid_bodies.keys())[0] #get the first rigid body
        #self.

#%%
if __name__=='__main__':
    testa = False #print data to json
    
    mymot = MotiveInterface()
    #time.sleep(0.5)
    a = mymot.query('meca_head')
    b = mymot.query(74027)
    c = mymot.query({'meca_head':None,'test':74027})
    
    if(testa):
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
        
        
        
        
        