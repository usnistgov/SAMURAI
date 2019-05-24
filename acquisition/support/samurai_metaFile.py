# -*- coding: utf-8 -*-

from collections import OrderedDict
import os
import json
import numpy as np
from datetime import datetime as dt
import samurai.acquisition.support.pnaController as pnaController
#import pnaController as pnaController
import six

#class for meta file with JSON and temp file
#import directory and file name
#also give the csv file where positions are running from to build JSON template
#Written by Alec Weiss 2018
class metaFile:
    # init our class
    def __init__(self,csv_path,pna_addr,**arg_options):

        #input options
        self.options = OrderedDict({})

        #Some default values
        self.options['root_dir'] = os.path.abspath('./')
        self.options['csv_path'] = csv_path
        self.options['metafile_name'] = 'metafile'
        self.options['pna_address'] = pna_addr
        self.options['csv_delimiter'] = ','
        
        #default calPath
        self.options['cal_path'] = './calibration.s4p'
        
        #1.02 added relative paths to working directory in metafile
        #1.03 changed most inputs to dictionary for easy setting from outside
        
        #some info about the system
        #defaults
        self.options['metafile_version']   = 1.03
        self.options['metafile_changelog'] = {
                1.03: ["Added new defaults and heavily updated the code to be more user friendly"],
                2.00: ["(5/10/2019) Updated reference frame. THIS IS VERY IMPORTANT FOR ALL USES OF MEAUSUREMENTS.\\n" 
                       "New reference frame is as follows when looking from behind the robot: \\n"
                       "      X - left/right\\n"
                       "      Y - up/down\\n"
                       "      Z - in/out (i.e. propogation direction)\\n"
                       "      converting from pre 2.00 we get X=Y,Y=Z,Z=X"]
                      }
        self.options['experiment']         = 'SAMURAI Measurements'
        self.options['experiment_version'] = 1.0
        self.options['positioner']         = 'Meca500'
        self.options['positioner_rotation_format'] = "X\'Y\'Z\'"
        self.options['user']               = 'ajw'
        self.options['units']              = 'mm'
        self.options['position_key']       = ['X','Y','Z','alpha','beta','gamma']
        self.options['vna_info']           = {'info':'NO VNA QUERIED',"start":26.5e9,"stop":40e9,"step":20e6,"ifbw":10,"power":0}
        self.options['antennas']           = []
        
        #get our vna information if possible
        self.get_vna_params(pna_addr=pna_addr)

        #this is an example. should allow user to add in antenna
        antenna1 = OrderedDict()
        antenna1["name"]          = "Sage Millimeter 17dBi rectangular horn"
        antenna1["txrx"]          = "tx"
        antenna1["location"]      = "Far end of table on optical post"
        antenna1["gain_dbi"]      = 17
        antenna1["beamwidth_e"]   = 23
        antenna1["beamwidth_h"]   = 24
        antenna1["serial_number"] = "14172-02"
        antenna2 = OrderedDict()
        antenna2["name"]          = "Sage Millimeter 17dBi rectangular horn"
        antenna2["txrx"]          = "rx"
        antenna2["location"]      = "Mounted on Meca500 Positioner"
        antenna2["gain_dbi"]      = 17
        antenna2["beamwidth_e"]   = 23
        antenna2["beamwidth_h"]   = 24
        antenna2["serial_number"] = "14172-01"
        self.add_antenna(antenna1)
        self.add_antenna(antenna2)

        #write any input options
        for key,value in six.iteritems(arg_options):
            if(key=='root_dir'): #get abspath if rootdir
                value = os.path.abspath(value)
            self.options[key] = value

        #delimeter of csv file (typically ',')

        #build our file names
        self.make_file_names()
    
    def add_antenna(self,antenna,idx=None):
        '''
        @brief add info on an antenna. This can be in whatever format
        @param[in] antenna - information on antenna (usually a dictionary)
        @param[in] OPTIONAL idx - if provided, overwrite given slot in antenna
        '''
        if(idx):
            self.options['antennas'][idx] = antenna
        else:
            self.options['antennas'].append(antenna)

    def set_options(self,**options):
        '''
        @brief set values in the options dictionary.
        @param[in] options - key value pairs of options to set
        '''
        for key,value in six.iteritems(options):
            self.options[key] = value

     #clean and create file names
    def make_file_names(self,clean=True):
        '''
        @brief clean (increment name) and create file names for json and raw files
        @param[in] clean - flag on whether or not to clean the file (change the name if it exists)
        '''
        #tmp path is used to prevent unneccessary writes
        #to json file but save in case of crash
        self.jsonPath = os.path.join(self.options['root_dir'],self.options['metafile_name']+'.json')
        self.tmpfPath = os.path.join(self.options['root_dir'],self.options['metafile_name']+'.raw')
        self.raw_path = self.tmpfPath
        self.csvPath  = self.options['csv_path']
        #build JSON template
        #first check if we already have a metaFile rename if needed
        if(clean):
            [self.jsonPath,iij]=clean_file_name(self.jsonPath)
            [self.tmpfPath,_  ]=clean_file_name(self.tmpfPath,iij)
    #alias
    makeFileNames = make_file_names    
    
    #get parameters from vna
    def get_vna_params(self,pna_addr):
        '''
        @brief get parameters from the VNA if we can
        @param[in] pna_addr - visa address of vna
        '''
        try:
            pnaCont = pnaController.pnaController(pna_addr)
            pnaCont.getParams()
            self.options['vna_info'].update({'info':pnaCont.info})
            self.options['vna_info'].update({'start':pnaCont.freq_start})
            self.options['vna_info'].update({'stop':pnaCont.freq_stop})
            self.options['vna_info'].update({'step':pnaCont.freq_step})
            self.options['vna_info'].update({'ifbw':pnaCont.ifbw})
            self.options['vna_info'].update({'num_pts':pnaCont.num_pts})
            self.options['vna_info'].update({'dwell_time':pnaCont.dwell_time})
            self.options['vna_info'].update({'sweep_delay':pnaCont.sdelay_time})
            self.options['vna_info'].update({'power':pnaCont.power})
            self.options['vna_info'].update({'sweep_type':pnaCont.sweep_type})
            self.options['vna_info'].update({'sweep_time':pnaCont.sweep_time})
        except:
            print("Unable to get parameters from VNA, Using defaults")
        
    #init function to be called after all values set by user
    #This will call init JSON and other files to build template.
    #parameters after this cannot be changed
    def init(self,**additional_header_info):
        '''
        @brief initialize after values set by user to create the json template
        @param[in/OPT] additional_header_info - keyword arguments to be added to the header
        '''
        #build our json file template
        self.build_json_template(**additional_header_info)
        #init our continuation file in case of failure
 #       self.initContFile();

        
    #build the initial template for our json file
    def build_json_template(self,**additional_header_info):
        '''
        @brief build our json template with header and positions
        @param[in/OPT] additional_header_info - keyword arguments to be added to the header
        '''
        #first build header
        jhd = OrderedDict({})
        jhd["working_directory"]  = self.options['root_dir']
        jhd['metafile_path']      = os.path.relpath(self.jsonPath,self.options['root_dir'])
        jhd['rawfile_path']       = os.path.relpath(self.tmpfPath,self.options['root_dir'])
        jhd["metafile_version"]   = self.options['metafile_version']
        jhd['experiment']         = self.options['experiment']
        jhd['experiment_version'] = self.options['experiment_version']
        jhd['positioner']         = self.options['positioner']
        jhd['user']               = self.options['user']
        jhd['vna_info']           = self.options['vna_info']
        jhd['antennas']           = self.options['antennas']
        jhd['notes']              = None

        for key,val in six.iteritems(additional_header_info):
            jhd[key] = val
            
        #now loop through json file to add measurements
        self.jsonData = jhd  #add the header data
        self.jsonData['total_measurements']     = 0
        self.jsonData['completed_measurements'] = 0
        self.jsonData['measurements']           = [] #now add the measurement data

        with open(self.csvPath,'r') as csvfile:
            for line in csvfile:
                #make sure the line isnt emtpy
                if(line.strip()):
                    if(line.strip()[0]=='#'): #then its a comment
                       continue
                    self.jsonData['total_measurements']+=1
                    locId = self.jsonData['total_measurements']-1
                    #extract our position from the csv file
                    strArr = line.split(self.options['csv_delimiter'])
                    pos = [float(i) for i in strArr]
                    self.jsonData['measurements'].append(OrderedDict({'ID':locId}))
                    self.jsonData['measurements'][locId].update({'position_key':self.options['position_key']})
                    self.jsonData['measurements'][locId].update({'position':pos})
                    self.jsonData['measurements'][locId].update({'units':self.options['units']})
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
            raw_file_path = self.tmpfPath
        #first build header
        jhd = OrderedDict({})
        jhd["working_directory"]  = self.options['root_dir']
        jhd['metafile_path']      = os.path.relpath(self.jsonPath,self.options['root_dir'])
        jhd['rawfile_path']       = os.path.relpath(self.tmpfPath,self.options['root_dir'])
        jhd["metafile_version"]   = self.options['metafile_version']
        jhd['experiment']         = self.options['experiment']
        jhd['experiment_version'] = self.options['experiment_version']
        jhd['positioner']         = self.options['positioner']
        jhd['user']               = self.options['user']
        jhd['vna_info']           = self.options['vna_info']
        jhd['antennas']           = self.options['antennas']
        jhd['notes']              = None
        
        for key,val in six.iteritems(additional_header_info):
            jhd[key] = val

        #now loop through json file to add measurements
        self.jsonData = jhd
        rfp = os.path.join(self.options['root_dir'],raw_file_path)
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
                    fname  = os.path.relpath(ls[2].strip(),self.options['root_dir'])
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
                    #strArr = line.split(self.options['csv_delimiter']);
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
            cal_file_path - location of the calibration file 
            note - note to add to the measurement
            measID - id of the measurement (default -1 autodetects)
            dict_data - dicitionary of extra data to write to the measurement piece
        '''
        defaults = {'cal_file_path':self.options['cal_path'],'note':'none','measID':-1}
        defaults['dict_data'] = None 
        options = {}
        for key, value in six.iteritems(defaults):
            options[key] = value
        for key, value in six.iteritems(arg_options):
            options[key] = value
        #open and append our data to our text file        
        if(os.path.isfile(self.tmpfPath)!=True): #see if the file doesnt already exist
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
        with open(self.tmpfPath,writeType) as metafile:
            line = ('|   '+str(measID)+ "    |    "+os.path.relpath(file_path,self.options['root_dir'])+"    |    "+os.path.relpath(options['cal_file_path'],self.options['root_dir'])+'   |   '
                    +str(dt.now())+"    |    "+str(position)+ "    |    "+options['note']+"   |   "+json.dumps(options['dict_data'])+"   |\n")
            metafile.write(headerLine)
            metafile.write(line)
            
        
    #take the data from our temporary metaFile and put into JSON file
    def finalize(self):
        '''
        @brief write our data from our temp file back to the json file
            This finishes the measurement. After this is called the data from 
            the '.raw' measurement file will be put into our json file
        '''
        #load json data
        jsonFile = open(self.jsonPath,'r')
        jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
        jsonFile.close()
        #fill JSON Data from tmpFile
        with open(self.tmpfPath,'r') as tmpFile:
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
        #remove temp metafile
        #os.remove(self.jsonPath+'.tmp');
        
        
    #laod from previous session
    def load_session(self,metaName):
        print("DO THIS")
        #build file with info to continue then delete at end when finished
        
     
    #get the file id of the last entry
    def get_last_meas_id(self):
        with open(self.tmpfPath,'r') as fp:
            #get last line
            for line in fp:
                pass
            #get id from last line
            return int(line.split('|')[1])


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

#alias
MetaFile = metaFile    

#os.chdir('U:/67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\VNA_Drift/3-16-18_driftData\processed_data')
#mf = metaFile();
#mf.buildJsonFromRaw('metaFile.raw')
