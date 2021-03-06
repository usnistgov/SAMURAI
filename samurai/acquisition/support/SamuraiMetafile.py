# -*- coding: utf-8 -*-
'''
@brief class to create a metafile and update its values during measurement. 
This works by creating a json template from the provided measurement positions.
While measuring, information is then stored in a raw text file to prevent python from parsing the json on every measurement.
After completion of the measurement, this raw text file is then used to populate the final json measurement file 
@author ajw5
@date 2018
'''

from collections import OrderedDict
import os
import json
import numpy as np
from datetime import datetime as dt
import six
import getpass

from samurai.base.SamuraiDict import SamuraiDict

#%% Default values
DEFAULT_SAGE_WR28_PHORN_17DBI = SamuraiDict({
    'name':"Sage Millimeter 17dBi rectangular horn",
    'txrx':'N/A',
    'location':'N/A',
    'gain_dbi':17,
    'beamwidth_e':23,
    'beamwidth_h':24,
    'serial_number':'14172-0[1,2]'
    })

DEFAULT_ANTENNA = SamuraiDict({
    'name':"N/A",
    'txrx': 'N/A',
    'location': "N/A",
    'gain_dbi':'N/A',
    'beamwidth_e':'N/A',
    'beamwidth_h':'N/A',
    'serial_number':'N/A'
    })
DEFAULT_ANTENNAS = [DEFAULT_ANTENNA]*2

DEFAULT_METADATA_DICT = SamuraiDict({
    'working_directory':'./',
    'metafile_name':'metafile',
    'csv_delimiter':',',
    'cal_path':'./calibration.s4p', #default calibration path
    
    'metafile_version':2.01,
    'metafile_changelog':{
                1.03: ["Added new defaults and heavily updated the code to be more user friendly"],
                2.00: ["(5/10/2019) Updated reference frame. THIS IS VERY IMPORTANT FOR ALL USES OF MEAUSUREMENTS.\\n" 
                       "New reference frame is as follows when looking from behind the robot: \\n"
                       "      X - left/right\\n"
                       "      Y - up/down\\n"
                       "      Z - in/out (i.e. propogation direction)\\n"
                       "      converting from pre 2.00 we get X=Y,Y=Z,Z=X"],
                2.01: ["external positions now have units property and all 'position_mm' changed to 'position' and 'residual_mm' changed to 'residual'"]      
                }, 
    'experiment':'SAMURAI Measurements',
    'experiment_version':1.0,
    
    #some system info
    'positioner':'Meca500',
    'positioner_rotation_format':"X\'Y\'Z\'",
    'user':getpass.getuser(),
    'units':'mm',
    'position_key':['X','Y','Z','alpha','beta','gamma'],
    'vna_info':{'info':'NO VNA QUERIED'},
    'antennas': DEFAULT_ANTENNAS,
    
    'total_measurements':0,
    'completed_measurements':0,
    'measurements':[]
    })

#%% Some useful functions
def extract_data_from_raw(raw_path):
    '''
    @brief extract a list of dictionary data from a \*.raw file
    @param[in] raw_path - path to the \*.raw file to get data from
    @return List of dictionaries for each entry in the file
    '''
    meas_list = []
    with open(raw_path,'r') as raw_fp:
        next(raw_fp) #skip the first line
        for line in raw_fp:
            line_split = line.split('|')[1:] #skip initial whitespace
            #names of the data
            data_names = ['ID','filename','calibration_file',
                          'timestamp','position','notes','extra_data']
            data_dict = SamuraiDict()
            for data_name,line_val in zip(data_names,line_split):
                data_dict[data_name] = line_val  
            data_dict['ID'] = int(data_dict['ID']) #change to int
            data_dict['position'] = eval(data_dict['position']) #change to actual list
            #now get and add any additional data
            extra_data = SamuraiDict()
            extra_data.loads(data_dict.pop('extra_data'))
            for k,v in extra_data.items():
                data_dict[k] = v
            meas_list.append(data_dict) #add it to the list of measurements
    return meas_list


#%% The actual class
class SamuraiMetafile(OrderedDict):
    '''
	@brief class to create a metafile and add measurements to it during a full measurement sweep  
    @note This is aliased with both samurai.acquisition.support.samurai_metaFile.metaFile and 
        samurai.acquisition.support.SamuraiMetafile.MetaFile for backward compatability
	@param[in] csv_path - path to file for positions of measurement (used to generate json template)  
	@param[in] pna_addr - visa address of pna to get information from  
	@param[in/OPT] arg_options - keyword arguments will replace any input key with provided value  
	'''
    def __init__(self,csv_path,pna_addr,**arg_options):
        '''@brief Constructor'''
        #input options
        super().__init__() #initialize ordereddict
        
        #add default values
        for k,v in DEFAULT_METADATA_DICT.items():
            self[k] = v

        #Some other input values
        self['csv_path'] = csv_path
        self['pna_address'] = pna_addr
        
        #get our vna information if possible
        if pna_addr is not None:
            self.get_vna_params(pna_addr=pna_addr)  
        
        #write any input options
        for key,value in six.iteritems(arg_options):
            self[key] = value

        #build our file names
        self.make_file_names()
    
    def add_antenna(self,antenna,idx=None):
        '''
        @brief add info on an antenna. This can be in whatever format   
        @param[in] antenna - information on antenna (usually a dictionary)   
        @param[in] OPTIONAL idx - if provided, overwrite given slot in antenna   
        '''
        if(idx):
            self['antennas'][idx] = antenna
        else:
            self['antennas'].append(antenna)

    def set_options(self,**options):
        '''
        @brief set values in the options dictionary.  
        @param[in] options - key value pairs of options to set  
        '''
        for key,value in six.iteritems(options):
            self[key] = value

     #clean and create file names
    def make_file_names(self,clean=True):
        '''
        @brief clean (increment name) and create file names for json and raw files  
        @param[in] clean - flag on whether or not to clean the file (change the name if it exists)  
        '''
        #tmp path is used to prevent unneccessary writes
        #to json file but save in case of crash
        self.jsonPath = os.path.join(self['working_directory'],self['metafile_name']+'.json')
        self.raw_path = os.path.join(self['working_directory'],self['metafile_name']+'.raw')
        self.raw_path = self.raw_path
        self.csvPath  = self['csv_path']
        #build JSON template
        #first check if we already have a metaFile rename if needed
        if(clean):
            [self.jsonPath,iij]=clean_file_name(self.jsonPath)
            [self.raw_path,_  ]=clean_file_name(self.raw_path,iij)
    #alias
    makeFileNames = make_file_names    
    
    def get_vna_params(self,pna_addr):
        '''
        @brief get parameters from the VNA if we can  
        @param[in] pna_addr - visa address of vna  
        '''     
        from samurai.acquisition.instrument_control.PnaController import PnaController
        from samurai.acquisition.instrument_control.InstrumentControl import InstrumentConnectionError
        try:
            pnaCont = PnaController(pna_addr)
            pnaCont.get_params() #update the parameters
            self['vna_info'].update(pnaCont) #write to metafile
        except InstrumentConnectionError: #only accespt instrument conection error
            print("Connection Error. Unable to get parameters from VNA.")
            
    def init(self,**additional_header_info):
        '''
        @brief initialize after values set by user to create the json template  
        @param[in/OPT] additional_header_info - keyword arguments to be added to the header  
        '''
        #build our json file template
        self.build_json_template(**additional_header_info)
        #init our continuation file in case of failure
 #       self.initContFile();

    def load_json_template(self,metafile_path):
        '''
        @brief Load an already created json template (metafile without measurements). 
            This is usually done in case of failure of a measurement. It will overwrite our options for this class too.  
        @param[in] metafile_path - path to the metafile template (*.json) to load  
        '''
        #load the json data
        self.jsonPath = metafile_path
        with open(self.jsonPath,'r') as jsonFile:
            jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
        self.jsonData = jsonData
        options_omit_keys = ['measurements'] #json keys to omit when we overwrite self.options
        for key,val in self.jsonData.items():
            if key not in options_omit_keys:
                self[key] = val
        
    def load_raw_file(self,raw_path):
        '''
        @brief 'load' an already created raw (*.raw) file from a measurement.
            Again usually used in case self.finalize is not reached in a measurement. 
            This actually just sets the self.tempfpath property.  
        @param[in] raw_path - path to the raw (*.raw) file  
        '''
        self.raw_path = raw_path
        
    #build the initial template for our json file
    def build_json_template(self,**additional_header_info):
        '''
        @brief build our json template with header and positions  
        @param[in/OPT] additional_header_info - keyword arguments to be added to the header  
        '''
        #first build header
        jhd = OrderedDict({})
        jhd['metafile_path']      = os.path.relpath(self.jsonPath,self['working_directory'])
        jhd['rawfile_path']       = os.path.relpath(self.raw_path,self['working_directory'])
        jhd.update(self)  #update with all of our input options
        jhd['notes']              = None

        for key,val in six.iteritems(additional_header_info):
            jhd[key] = val
            
        #now loop through json file to add measurements
        self.jsonData = jhd  #add the header data

        with open(self.csvPath,'r') as csvfile:
            for line in csvfile:
                #make sure the line isnt emtpy
                if(line.strip()):
                    if(line.strip()[0]=='#'): #then its a comment
                       continue
                    self.jsonData['total_measurements']+=1
                    locId = self.jsonData['total_measurements']-1
                    #extract our position from the csv file
                    strArr = line.split(self['csv_delimiter'])
                    pos = [float(i) for i in strArr]
                    self.jsonData['measurements'].append(OrderedDict({'ID':locId}))
                    self.jsonData['measurements'][locId].update({'position_key':self['position_key']})
                    self.jsonData['measurements'][locId].update({'position':pos})
                    self.jsonData['measurements'][locId].update({'units':self['units']})
                    self.jsonData['measurements'][locId].update({'notes':'none'})
                    self.jsonData['measurements'][locId].update({'filename':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'timestamp':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'calibration_file':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'calibrated':False})

        #now write this out to our JSON file
        with open(self.jsonPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4)
    #alias
    buildJsonTemplate = build_json_template
            
    #can be built after all raw measurements have been taken
    def build_json_from_raw(self,raw_file_path='default',**additional_header_info):
        '''
        @brief build a json template from a raw json file  
        @param[in] raw_file_path - location of raw file to create json from  
        @param[in/OPT] additional_header_info - keyword arguments to be added to the header  
        '''
        if(raw_file_path=='default'):
            raw_file_path = self.raw_path
        #first build header
        jhd = OrderedDict({})
        jhd["working_directory"]  = self['working_directory']
        jhd['metafile_path']      = os.path.relpath(self.jsonPath,self['working_directory'])
        jhd['rawfile_path']       = os.path.relpath(self.raw_path,self['working_directory'])
        jhd["metafile_version"]   = self['metafile_version']
        jhd['experiment']         = self['experiment']
        jhd['experiment_version'] = self['experiment_version']
        jhd['positioner']         = self['positioner']
        jhd['user']               = self['user']
        jhd['vna_info']           = self['vna_info']
        jhd['antennas']           = self['antennas']
        jhd['notes']              = None
        
        for key,val in six.iteritems(additional_header_info):
            jhd[key] = val

        #now loop through json file to add measurements
        self.jsonData = jhd
        rfp = os.path.join(self['working_directory'],raw_file_path)
        #GET number of measurements from raw file
        rawLineCount = 0
        with open(rfp,'r') as rawfile:
            for line in rawfile:
                rawLineCount+=1
            rawLineCount-=1 #remove header
            
        self.jsonData['total_measurements']     = 0
        self.jsonData['completed_measurements'] = 0
        self.jsonData['measurements']           = []

        with open(rfp,'r') as rawfile:
            next(rawfile) #skip header
            for line in rawfile:
                #make sure the line isnt emtpy
                if(line.strip()):
                    self.jsonData['total_measurements']+=1
                    locId = self.jsonData['total_measurements']-1
                    ls = line.split('|')
                    measId = int(ls[1])
                    fname  = os.path.relpath(ls[2].strip(),self['working_directory'])
                    cfname = ls[3]
                    time   = ls[4]
                    notes  = ls[6]
                    posStr = ls[5]
                    posStr = posStr.strip()
                    posStr = posStr.strip(']')
                    posStr = posStr.strip('[')
                    posStr = posStr.split(',')
                    #test to see if we can parse the data. 
                    #otherwise assume ther eis no positioner attached
                    try:
                        pos = [float(i) for i in posStr]
                        pos_out = str(pos)
                    except ValueError:
                        pos_out = 'NO Positioner'
                    #extract our position from the csv file
                    #strArr = line.split(self['csv_delimiter']);
                    #pos = [float(i) for i in strArr];
                    self.jsonData['measurements'].append(OrderedDict({'ID':measId}))
                    self.jsonData['measurements'][locId].update({'position_key':'Unknown'})
                    self.jsonData['measurements'][locId].update({'position':pos_out})
                    self.jsonData['measurements'][locId].update({'units':'Unknown'})
                    self.jsonData['measurements'][locId].update({'notes':notes})
                    self.jsonData['measurements'][locId].update({'filename':fname})
                    self.jsonData['measurements'][locId].update({'timestamp':time})
                    self.jsonData['measurements'][locId].update({'calibration_file':cfname})
                    self.jsonData['measurements'][locId].update({'calibrated':False})

        #now write this out to our JSON file
        with open(self.jsonPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4)
    #alias
    buildJsonFromRaw = build_json_from_raw


    #update temporary metaFile
    def update(self,file_path,position,**arg_options):
        '''
        @brief update the temporary metafile data  
        @param[in] file_path - path of the measurement file  
        @param[in] position  - position of the positoiner for the measurement  
        @param[in] arg_options - keyword arguments as follows:  
            - cal_file_path - location of the calibration file   
            - note - note to add to the measurement  
            - measID - id of the measurement (default -1 autodetects)  
            - dict_data - dicitionary of extra data to write to the measurement piece  
        '''
        defaults = {'cal_file_path':self['cal_path'],'note':'none','measID':-1}
        defaults['dict_data'] = SamuraiDict()
        options = {}
        for key, value in six.iteritems(defaults):
            options[key] = value
        for key, value in six.iteritems(arg_options):
            options[key] = value
        #open and append our data to our text file        
        if(os.path.isfile(self.raw_path)!=True): #see if the file doesnt already exist
            #if it doesnt exist make it and create header
            writeType = 'w+'
            headerLine = "|   ID   |   FILENAME   |   CALFILE   |   TIME   |   POSITION   |   NOTES   | DICT_DATA\n"
            measID=0
        else: #else it already exists
            #find the measID if not given
            if(options['measID']==-1):
                measID=self.get_last_meas_id()+1
            writeType = 'a'
            headerLine = ''
            
        #build the file line from our parameters
        with open(self.raw_path,writeType) as metafile:
            line = ('|   '+str(measID)+ "    |    "+os.path.relpath(file_path,self['working_directory'])+"    |    "+os.path.relpath(options['cal_file_path'],self['working_directory'])+'   |   '
                    +str(dt.now())+"    |    "+str(position)+ "    |    "+options['note']+"   |   "+options['dict_data'].dumps(indent=None)+"   |\n")
            metafile.write(headerLine)
            metafile.write(line)
            
        
    #take the data from our temporary metaFile and put into JSON file
    def finalize(self,json_path=None,raw_path=None):
        '''
        @brief Write our data from our temp file back to the json file. 
            This finishes the measurement. After this is called the data from 
            the '.raw' measurement file will be put into our json file.  
        @param[in/OPT] json_path - path to json file. If None (default) get from self.jsonPath
        @param[in/OPT] raw_path - path to \*.raw file. If None (default) get from self.raw_path
        '''
        #load json data
        if json_path is None:
            json_path = self.jsonPath
        jsonData = SamuraiDict(json_path)
        #fill JSON Data from tmpFile
        if raw_path is None:
            raw_path = self.raw_path
        with open(raw_path,'r') as tmpFile:
            next(tmpFile)
            for line in tmpFile:
                ls = line.split('|')
                measId = int(ls[1])
                fname  = ls[2]
                cfname = ls[3]
                time   = ls[4]
                notes  = ls[6]
                posStr = ls[5]
                dict_data = json.loads(ls[7]) #extra data
                posStr = posStr.strip()
                posStr = posStr.strip(']')
                posStr = posStr.strip('[')
                posStr = posStr.split(',')
                pos = [float(i) for i in posStr]
                #double check the location
                json_pos = jsonData['measurements'][measId]['position']
                pos_check_limit = 0.05 #lowest bound in mm that must match
                if(any((np.array(pos)-np.array(json_pos))>pos_check_limit)):
                    print("WARNING: Positions do not match json file!")
                #now fill json structure
                self.jsonData['measurements'][measId]['notes'] = notes
                self.jsonData['measurements'][measId]['filename'] = fname
                self.jsonData['measurements'][measId]['timestamp'] = time
                self.jsonData['measurements'][measId]['calibration_file'] = cfname
                if dict_data is not None:
                    for key,val in six.iteritems(dict_data):
                        self.jsonData['measurements'][measId][key] = val
                #increment filled measurements
                self.jsonData['completed_measurements']+=1
        #now write out new json data
        
        with open(self.jsonPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4)
        
    def load_session(self,metaName):
        '''
		@brief load a previously incomplete measurement session 
		@todo IMPLEMENT THIS FUNCTION
		'''
        raise NotImplementedError
        #build file with info to continue then delete at end when finished
        
     
    #get the file id of the last entry
    def get_last_meas_id(self):
        '''@brief get the id of the last file saved in the raw file'''
        with open(self.raw_path,'r') as fp:
            #get last line
            for line in fp:
                pass
            #get id from last line
            return int(line.split('|')[1])

#alias
metaFile = SamuraiMetafile
MetaFile = metaFile

import re
#check if file exists and change name if it does
def clean_file_name(file_path,num=-1):
    '''
    @brief clean the file name so if the file exists at an ending  
    @param[in] file_path - path/to/file to clean name of  
    @param[in/OPT] num - number to add (-1 finds the next lowest unused number)  
    '''
    [mydir,fname] = os.path.split(file_path)
    i=0
    if(num==-1):
        while(os.path.isfile(os.path.join(mydir,fname))==True):
            i+=1
            #jump to next number
            fname = re.sub('(\([0-9+]\))*\.','('+str(i)+').',fname) #remove number and replace with current i value
    elif(num==0):#no need to add thing on
        i=num
    else:
        i=num
        fname = re.sub('(\([0-9+]\))*\.','('+str(i)+').',fname) 
    fout = os.path.join(mydir,fname)
    return fout,i

def finalize_metafile(metafile_path,raw_path,**kwargs):
    '''
    @brief Finalize a metafile in case of failure. 
        This will finalize a metafile given the metafile path and the raw data path.  
    @param[in] metafile_path - path to the metafile (.json) template create at the beginning of the measurement  
    @param[in] raw_path - path to the raw file (.raw) created from the mesaurements taken  
    '''
    mymf = MetaFile(None,None)
    mymf.load_json_template(metafile_path)
    mymf.load_raw_file(raw_path)
    mymf.finalize()


import unittest

class TestSamuraiMetafile(unittest.TestCase):
    '''@brief Unit testing for SamuraiMetafile class'''
    
    def test_metafile_measurement(self):
        '''@brief Test typical creation, updating, and finalize for a measurement'''
        pass
    

if __name__=='__main__':
    import os
    mydir = r'\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\6-17-2019\synthetic_aperture'
    finalize_metafile(os.path.join(mydir,'metafile.json'),os.path.join(mydir,'metafile.raw'))




