# -*- coding: utf-8 -*-

from collections import OrderedDict
import os
import json
import numpy as np
from datetime import datetime as dt
import support.pnaController as pnaController
import six

#class for meta file with JSON and temp file
#import directory and file name
#also give the csv file where positions are running from to build JSON template
#Written by Alec Weiss 2018
class metaFile:
    # init our class
    def __init__(self,csvFile,pna_addr,wdir='./', metaDir='./',metaName='metaFile'
                 ,csvDir='./',delimiter=',',calPath='./calibration.s4p',**options):
        #change directory
        os.chdir(wdir)
        #set csv dir and metadir to root dir unless specified
        if(wdir[-1]!='/'):
            wdir = wdir+'/'
        if(csvDir=='./'):
            csvDir = wdir
        if(metaDir=='./'):
            metaDir = wdir
        
        #Data used for later continuation of process
        self.rootdir = os.path.abspath(wdir)
        self.csvFile = csvFile
        self.csvDir  = csvDir
        self.metaDir = metaDir
        self.metaName = metaName
        self.pna_addr = pna_addr
        
        #default calPath
        self.calpath = calPath
        
        #1.02 added relative paths to working directory in metafile
        #1.03 changed most inputs to dictionary for easy setting from outside
        
        #some info about the system
        self.jsonHeader         = {} #just initialize our header
        #defaults
        self.metafile_version   = 1.03
        self.experiment         = 'software testing'
        self.experiment_version = 1.0
        self.positioner         = 'Meca500'
        self.user               = 'ajw'
        self.units              = 'mm'
        self.posKey             = ['X','Y','Z','alpha','beta','gamma']
        self.vnaInfo            = {'info':'NO VNA QUERIED',"start":26.5e9,"stop":40e9,"step":20e6,"ifbw":10,"power":0}
        self.antennas           = []
        
        #get our vna information if possible
        self.get_vna_params(pna_addr=pna_addr)

        #this is an example. should allow user to add in antenna
        antenna1 = OrderedDict({"name":"Sage_mm 17dBi rectangular horn"})
        antenna1.update({"txrx":"tx","Location":"Back wall"})
        antenna1.update({"gain": 17,"beamwidth_e":23,"beamwidth_h":24})
        antenna1.update({"serial_number":"12345"})
        antenna2 = OrderedDict({"name":"Sage_mm 17dBi rectangular horn"})
        antenna2.update({"txrx":"rx","Location":"Mounted on Meca500 Positioner"})
        antenna2.update({"gain": 17,"beamwidth_e":23,"beamwidth_h":24})
        antenna2.update({"serial_number":"54321"})
        self.antennas.append(antenna1)
        self.antennas.append(antenna2)
        #delimeter of csv file (typically ',')
        self.delimiter = delimiter
        #build our file names
        self.makeFileNames(csvFile=csvFile,metaName=metaName,csvDir=csvDir,metaDir=metaDir)
    
     #clean and create file names
    def makeFileNames(self,csvFile,metaName='metaFile',csvDir='./',metaDir='./',clean=1):
        #build file paths
        #tmp path is used to prevent unneccessary writes
        #to json file but save in case of crash
        self.jsonPath = os.path.join(self.metaDir,metaName+'.json')
        self.tmpfPath = os.path.join(self.metaDir,metaName+'.raw')
        self.raw_path = self.tmpfPath
        self.csvPath  = os.path.join(self.csvDir,csvFile)
        #build JSON template
        #first check if we already have a metaFile rename if needed
        if(clean==1):
            [self.jsonPath,iij]=cleanFileName(self.jsonPath)
            [self.tmpfPath,iit]=cleanFileName(self.tmpfPath,iij)
        
    #get parameters from vna
    def get_vna_params(self,pna_addr):
        
        try:
            pnaCont = pnaController.pnaController(pna_addr)
            pnaCont.getParams()
            self.vnaInfo.update({'info':pnaCont.info})
            self.vnaInfo.update({'start':pnaCont.freq_start})
            self.vnaInfo.update({'stop':pnaCont.freq_stop})
            self.vnaInfo.update({'step':pnaCont.freq_step})
            self.vnaInfo.update({'ifbw':pnaCont.ifbw})
            self.vnaInfo.update({'num_pts':pnaCont.num_pts})
            self.vnaInfo.update({'dwell_time':pnaCont.dwell_time})
            self.vnaInfo.update({'sweep_delay':pnaCont.sdelay_time})
            self.vnaInfo.update({'power':pnaCont.power})
            self.vnaInfo.update({'sweep_type':pnaCont.sweep_type})
            self.vnaInfo.update({'sweep_time':pnaCont.sweep_time})
        except:
            print("Unable to get parameters from VNA, Using defaults")
        
    #init function to be called after all values set by user
    #This will call init JSON and other files to build template.
    #parameters after this cannot be changed
    def init(self,notes='none'):
        #build our json file template
        self.buildJsonTemplate(notes=notes)
        #init our continuation file in case of failure
 #       self.initContFile();

        
    #build the initial template for our json file
    def buildJsonTemplate(self,notes='none'):
        #first build header
        if(self.extJsonHeader):
            print("External JSON Header Used")
            self.jsonHeader = self.extJsonHeader
        else: #else we use our default
            jhd = OrderedDict({"working_directory":self.rootdir})
            jhd.update({'metafile_path':os.path.relpath(self.jsonPath,self.rootdir)})
            jhd.update({'rawfile_path':os.path.relpath(self.tmpfPath,self.rootdir)})
            jhd.update({"metafile_version":self.metafile_version})
            jhd.update({'experiment':self.experiment})
            jhd.update({'experiment_version':self.experiment_version})
            jhd.update({'positioner':self.positioner})
            jhd.update({'user':self.user})
            jhd.update({'vna_info':self.vnaInfo})
            jhd.update({'antennas':self.antennas})
            jhd.update({'notes':notes})
            self.jsonHeader=jhd
            
        #now loop through json file to add measurements
        self.jsonData = self.jsonHeader
        self.jsonData.update({'total_measurements':0})
        self.jsonData.update({'completed_measurements':0})
        self.jsonData.update({'measurements':[]})

        with open(self.csvPath,'r') as csvfile:
            for line in csvfile:
                #make sure the line isnt emtpy
                if(line.strip()):
                    self.jsonData['total_measurements']+=1
                    locId = self.jsonData['total_measurements']-1
                    #extract our position from the csv file
                    strArr = line.split(self.delimiter)
                    pos = [float(i) for i in strArr]
                    self.jsonData['measurements'].append(OrderedDict({'ID':locId}))
                    self.jsonData['measurements'][locId].update({'position_key':self.posKey})
                    self.jsonData['measurements'][locId].update({'position':pos})
                    self.jsonData['measurements'][locId].update({'units':self.units})
                    self.jsonData['measurements'][locId].update({'notes':'none'})
                    self.jsonData['measurements'][locId].update({'filename':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'timestamp':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'calibration_file':'INCOMPLETE'})
                    self.jsonData['measurements'][locId].update({'calibrated':False})

            
        #now write this out to our JSON file
        with open(self.jsonPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4)
            
    #can be built after all raw measurements have been taken
    def buildJsonFromRaw(self,rawFilePath='default',notes='none'):
        if(rawFilePath=='default'):
            rawFilePath = self.tmpfPath
        #first build header
        if(self.extJsonHeader):
            print("External JSON Header Used")
            self.jsonHeader = self.extJsonHeader
        else: #else we use our default
            jhd = OrderedDict({"working_directory":self.rootdir})
            jhd.update({'metafile_path':os.path.relpath(self.jsonPath,self.rootdir)})
            jhd.update({'rawfile_path':os.path.relpath(self.tmpfPath,self.rootdir)})
            jhd.update({"metafile_version":self.metafile_version})
            jhd.update({'experiment':self.experiment})
            jhd.update({'experiment_version':self.experiment_version})
            jhd.update({'positioner':self.positioner})
            jhd.update({'user':self.user})
            jhd.update({'vna_info':self.vnaInfo})
            jhd.update({'antennas':self.antennas})
            jhd.update({'notes':notes})
            self.jsonHeader=jhd
        #now loop through json file to add measurements
        self.jsonData = self.jsonHeader
        rfp = os.path.join(self.rootdir,rawFilePath)
        #GET number of measurements from raw file
        rawLineCount = 0
        with open(rfp,'r') as rawfile:
            for line in rawfile:
                rawLineCount+=1
            rawLineCount-=1 #remove header
            
        self.jsonData.update({'total_measurements':0})
        self.jsonData.update({'completed_measurements':0})
        self.jsonData.update({'measurements':[]})

        with open(rfp,'r') as rawfile:
            next(rawfile) #skip header
            for line in rawfile:
                #make sure the line isnt emtpy
                if(line.strip()):
                    self.jsonData['total_measurements']+=1
                    locId = self.jsonData['total_measurements']-1
                    ls = line.split('|')
                    measId = int(ls[1])
                    fname  = os.path.relpath(ls[2].strip(),self.rootdir)
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
                    #strArr = line.split(self.delimiter);
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
 
    
    #update temporary metaFile
    def update(self,filePath,position,**arg_options):#,calFilePath='default',note='none',measID=-1):
        defaults = {'cal_file_path':self.calpath,'note':'none','measID':-1}
        options = {}
        for key, value in six.iteritems(defaults):
            options[key] = value
        for key, value in six.iteritems(arg_options):
            options[key] = value
        #open and append our data to our text file        
        if(os.path.isfile(self.tmpfPath)!=True): #see if the file doesnt already exist
            #if it doesnt exist make it and create header
            writeType = 'w+'
            headerLine = "|   ID   |   FILENAME   |   CALFILE   |   TIME   |   POSITION   |   NOTES   |\n"
            measID=0
        else: #else it already exists
            #find the measID if not given
            if(options['measID']==-1):
                measID=self.getLastMeasID()+1
            writeType = 'a'
            headerLine = ''
            
        #build the file line from our parameters
        with open(self.tmpfPath,writeType) as metafile:
            line = ('|   '+str(measID)+ "    |    "+os.path.relpath(filePath,self.rootdir)+"    |    "+os.path.relpath(options['cal_file_path'],self.rootdir)+'   |   '
                    +str(dt.now())+"    |    "+str(position)+ "    |    "+options['note']+'   |\n')
            metafile.write(headerLine)
            metafile.write(line)
            
        
    #take the data from our temporary metaFile and put into JSON file
    def finalize(self):
       
        #load json data
        jsonFile = open(self.jsonPath,'r')
        jsonData = json.load(jsonFile, object_pairs_hook=OrderedDict)
        jsonFile.close()
        #json.dumps(jsonData)
        #make copy in case something goes wrong
        #os.rename(self.jsonPath,self.jsonPath+'.tmp')
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
                #increment filled measurements
                self.jsonData['completed_measurements']+=1
        #now write out new json data
        with open(self.jsonPath,'w+') as jsonFile:
            json.dump(self.jsonData,jsonFile,indent=4)
        #remove temp metafile
        #os.remove(self.jsonPath+'.tmp');
        
        
    #laod from previous session
    def loadSession(self,metaName):
        print("DO THIS")
        #build file with info to continue then delete at end when finished
        
     
    #get the file id of the last entry
    def getLastMeasID(self):
        with open(self.tmpfPath,'r') as fp:
            #get last line
            for line in fp:
                pass
            #get id from last line
            return int(line.split('|')[1])
  

      
#check if file exists and change name if it does
def cleanFileName(fileName,num=-1):
    fout=fileName
    i=0
    if(num==-1):
        while(os.path.isfile(fout)==True):
            i+=1
            #remove number if there was one
            fout = fout.split('/')[-1]
            if(len(fout.split('('))>1):
                fout = fout.split('(')[0]+fout.split(')')[-1]
            fout = fout.split('.')[0]+'('+str(i)+').'+fout.split('.')[1]
            fout = '/'.join(fileName.split('/')[0:-1])+'/'+fout
    elif(num==0):#no need to add thing on
        fout = fileName
    else:
        i=num
        fout = fout.split('/')[-1]
        fout = fout = fout.split('.')[0]+'('+str(i)+').'+fout.split('.')[1]
        fout = '/'.join(fileName.split('/')[0:-1])+'/'+fout
    return fout,i

#alias
MetaFile = metaFile    

#os.chdir('U:/67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\VNA_Drift/3-16-18_driftData\processed_data')
#mf = metaFile();
#mf.buildJsonFromRaw('metaFile.raw')
