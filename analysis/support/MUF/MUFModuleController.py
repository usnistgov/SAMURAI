# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:12:48 2019

@author: ajw5
"""

from lxml import etree as ET
import os
from samurai.base.SamuraiXML import SamuraiXML,SamuraiXMLElement

test_vnauncert_xml = r"./templates/template.vnauncert"
test_postproc_xml = r"../../calibration/templates/cal_template.post"

class MUFModuleController(SamuraiXML):
    '''
    @brief base class for MUF module controllers
    '''
    def __init__(self,menu_path,**kwargs):
        '''
        @brief default constructor
        @param[in] menu_path - path to menu to load
        @param[in/OPT] kwargs - keyword args as follows:
            exe_path - executable path of the module for running
            except_no_menu - throw an exception if no menu provided
        '''
        super().__init__()
        self.options = {}
        self.options['exe_path'] = None
        self.options['except_no_menu'] = True
        for k,v in kwargs.items():
            self.options[k] = v
        if menu_path is not None:
            self.load(menu_path)
        else:
            if self.options['except_no_menu']:
                raise Exception('No menu path provided') #implement default menu here
        
    def run(self,out_path,text_function=print,tf_args_tuple=(),tf_kwargs_dict={}):
        '''
        @brief run our module.This will also save to output_path
        @param[in] out_path - path to write the menu to before running (and to run from)
        @param[in/OPT] text_function - function that the output from the post 
            processor will be passed to (in iterated format, default is print())
            First argument must be expecting a string
        @param[in/OPT] tf_args_tuple - tuple of arguments to pass to text_function
        @param[in/OPT] tf_kwargs_dict - dictionary of kwargs to pass to text_function
        '''
        self.write(out_path)
        command = self.options['exe_path']+' -r '+self.menu_path
        exe_generator = subprocess_generator(command)
        for out_line in exe_generator:
            text_function(out_line,*tf_args_tuple,**tf_kwargs_dict)
        
    def add_item(self,parent_element,item):
        add_items(parent_element,[item])
        
    def add_items(self,parent_element,item_list):
        add_items(parent_element,item_list)
        
    def clear_items(self,parent_element):
        clear_items(parent_element)
        
    def create_item(self,item_name,subitem_text_list):
        create_item(item_name,subitem_text_list)
    
    def _get_name_from_path(self,path):
        '''
        @brief extract a default name from a path of a file
        @param[in] path - path to the file
        '''
        return os.path.splitext(os.path.split(path)[-1])[0]
    
    @property
    def controls(self):
        '''
        @brief getter for MUF list of controls child elements
        '''
        return self.find('Controls')
    
    @property
    def option_items_checkbox(self):
        '''
        @brief get list menu items from MenuStripItems
        '''
        return self.find('MenuStripItems')
        
    @property
    def option_items_textbox(self):
        '''
        @brief get list menu items from MenuStripTextBoxes
        '''
        return self.find('MenuStripTextBoxes')
    
    @property
    def option_items_combobox(self):
        '''
        @brief get list menu items from MenuStripItems
        '''
        return self.find('MenuStripComboBoxes')
    
class MUFItemList:
    '''@brief class to hold a list of MUF items (e.g. Monte Carlos, Perturbed Measurements, etc.)'''
    
    def __init__(self,xml_element,**kwargs):
        '''
        @brief constructor
        @param[in] xml_element - parent element of the list to load
            If a string is passed, a new element will be created 
        @param[in/OPT] kwargs - keyword arguments as follows:
            - None yet!
        '''
        if isinstance(xml_element,str):
            xml_element = ET.Element(xml_element)
        self._xml_element = xml_element
        self._muf_items = [] #list of MUFItem classes contained in the xml list
        #now load all of the xml values in the xml if there are any
        self.load_items()
        
    def load_items(self):
        '''
        @brief load children from the current xml tree
        '''
        children = self._xml_element.getchildren()
        self.add_items(children)
        
    def add_items(self,items):
        '''
        @brief add an item to the item list. 
        @param[in] items - list of xml elements or a MUFItems
        '''
        for it in items:
            self.add_item(it)
            
    def add_item(self,item):
        '''
        @brief add an item to the item list
        @param[in] item - xml element or MUFItem
        '''
        if isinstance(item,ET._Element): #change to MUFItem
            item = MUFItem(item)
        if not isinstance(item,MUFItem): #raise exception if it is the wrong type
            raise TypeError("{} is not a MUFItem or xml element".format(type(item)))
        item._xml_element.attrib['Index'] = str(self.count)
        self._muf_items.append(item) #add the items
        self._xml_element.append(item.xml_element) #append the xml
        self.update_xml_count()
            
    def clear_items(self):
        '''
        @brief clear all items from the list
        '''
        self._muf_items = [] #clear the list
        clear_muf_xml_items(self._xml_element) #clear the xml elements
        self.update_xml_count()
        
    def update_xml_count(self):
        '''
        @brief update the count attribute of the xml
        '''
        self._xml_element.attrib['Count'] = str(self.count)
        
    @property
    def count(self):
        '''@brief return the current item count'''
        return len(self._xml_element.getchildren())
        
    @property
    def xml_element(self):
        return self._xml_element
    
    @property
    def muf_items(self):
        return self._muf_items
    
    def tostring(self,*args,**kwargs):
        '''
        @brief string representation is the xml value
        '''
        kwargs_out = {}
        kwargs_out['pretty_print'] = True
        for k,v in kwargs.items():
            kwargs_out[k] = v
        return ET.tostring(self._xml_element,*args,**kwargs_out)
    
    def __len__(self):
        '''@brief get the number of items'''
        return self.count
    
    def __getitem__(self,item_num):
        '''@brief return a _muf_item value'''
        return self._muf_items[item_num]
                
        
class MUFItem(MUFItemList):
    '''@brief class to create a MUF item with subitems'''
    
    def __init__(self,xml_element,**kwargs):
        '''
        @brief constructor
        @param[in] xml_element - xml element for the item. If a list of 
            values is passed, a new item with each value as a subitem will be created
        @param[in/OPT] kwargs - if a new element is being created, kwargs will be passed as attributes
        '''
        self.data = None #this is a placeholder for data to map to xml items (e.g. TouchstoneEditor)
        self._filepath_subitem_idx = 1 #subitem index of the filepath. Typically 1 for *.meas files
        if isinstance(xml_element,ET._Element):
            super().__init__(xml_element)
        else:
            attributes = {'Index':str(-1),'Text':'None','Count':str(0)}
            for k,v in kwargs.items():
                attributes[k] = v
            self._xml_element = ET.Element('Item',attrib=attributes)
            self.add_items(xml_element) #these are items to add then if not an xml
        
    def add_item(self,item):
        '''
        @brief add a subitem
        @param[in] item - any object with string representation
        '''
        ET.SubElement(self._xml_element,'SubItem',attrib={"Index":str(self.count),"Text":str(item)})
        self.update_xml_count()
        
    def load_items(self):
        '''@brief override the loading of items'''
        pass #dont do anything here to load
        
    def load_data(self,load_funct,**kwargs):
        '''
        @brief load the data from the path subitem to self.data
        @param[in] load_class - function to load the data (can also be a class constructor)
        @param[in] subitem_idx - which index the path is to load (typically its self[0])
        @param[in] **kwargs - keyword arguments to pass to load_funct
        '''
        self.data = load_funct(self[self._filepath_subitem_idx],**kwargs)
        
    @property
    def filepath(self):
        '''@brief getter for filepath'''
        return self[self._filepath_subitem_idx]
    
    @filepath.setter
    def filepath(self,val):
        '''@brief setter for filepath'''
        self[self._filepath_subitem_idx] = val
        
    def __getitem__(self,item_num):
        '''@brief override [] to return subitem values'''
        return self._xml_element.getchildren()[item_num].attrib['Text']
    
    def __setitem__(self,item_num,val):
        '''@brief override [] to set subitem text'''
        self._xml_element.getchildren()[item_num].attrib['Text'] = val
    
    def __getattr__(self,attr):
        '''@brief override to pass commands to data and not xml'''
        try:
            return getattr(self.data,attr)
        except:
            raise AttributeError("{} not an attribute of {}".format(attr,type(self)))
            
    
def add_muf_xml_item(parent_element,item):
    '''
    @brief add an item(Subelement) to a parent. this also changes Count and Index of the parent and item
    @param[in] parent_element - parent element to add item to (e.g. self.controls.find('BeforeCalibration'))
    @param[in] item - item (element) to add to the parente element
    '''
    add_muf_xml_items(parent_element,[item])
    
def add_muf_xml_items(parent_element,item_list):
    '''
    @brief add items(Subelements) to a parent. this also changes Count and Index of the parent and item
    @param[in] parent_element - parent element to add item to (e.g. self.controls.find('BeforeCalibration'))
    @param[in] item - item (element) to add to the parente element
    '''
    if parent_element is None:
        raise Exception('Invalid parent_element')
    cur_num_children = len(parent_element.getchildren()) #get the current number of children
    for i,item in enumerate(item_list):
        item.attrib['Index'] = str(cur_num_children+i)
        parent_element.append(item)
    parent_element.attrib['Count'] = str(len(parent_element.getchildren())) #update the count
    
def clear_muf_xml_items(parent_element):
    '''@brief remove all subelements from a parent element'''
    for child in list(parent_element.getchildren()):
        parent_element.remove(child)
    
def create_muf_xml_item(item_name,subitem_text_list):
    '''
    @brief create an item from a name and list of subitems in MUF format
    @param[in] item_name - name of item (Text attribute of item)
    @param[in] subitem_text_list - list of Text attribute of Subitems
    '''
    item = ET.Element('Item',attrib={"Index":"-1","Text":item_name})
    for i,sub in enumerate(subitem_text_list):
        ET.SubElement(item,'SubItem',attrib={"Index":str(i),"Text":str(sub)})
    item.attrib['Count'] = str(len(item.getchildren()))
    return item


from samurai.base.SamuraiDict import SamuraiDict

class MUFModelKit(SamuraiDict):
    '''
    @brief class to store information on a set of MUF models
    '''
    def __init__(self,model_kit_path,*args,**kwargs):
        '''
        @brief constructor
        @param[in] model_kit_path - path to a written out MUFModelKit (a json path)
        @param[in/OPT] *args,**kwargs passed to OrderedDict
            type - type of calkit. must be specified when model_kit_path is None
        '''
        self['type'] = None
        self['models'] = {}
        if model_kit_path is None:
            try:
                self['type'] = kwargs['type']
            except:
                raise KeyError("Please specify 'type' as a keyword argument when creating an empty kit")
        else:
            self.load(model_kit_path)
    
    def add_model(self,name,path):
        '''
        @brief add a model to the model kit. 
        @param[in] name - name of the model. also the dict key to retrieve
        @param[in] path - path to the model
        '''
        self['models'].update({name:path})
        
    def get_model(self,name):
        '''
        @brief get a model from our kit
        '''
        return self['models'][name]
        
    def __getitem__(self,item):
        '''
        @brief also check the model dictionary
        '''
        try:
            return super().__getitem__(item)
        except KeyError as e:
            try:
                return self.get_model(item)
            except KeyError:
                raise e
        
import subprocess      
def subprocess_generator(cmd):
    '''
    @brief get a generator to get the output from post processor
     From https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    '''
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        stdout_line = stdout_line.strip() #remove trailing whitespaces and newlines
        if stdout_line=='':
            continue #dont do anything
        else:
            yield stdout_line #otherwise this value we want
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd) 
        
            
if __name__=='__main__':
    
    import os
    
    ml = MUFItemList('test')
    mi = MUFItem([1,'testing123'])
    ml.add_item(mi)
    
    vumc = MUFModuleController(test_vnauncert_xml)
    vumc.option_items_checkbox
    vumc.option_items_textbox
    ppmc = MUFModuleController(test_postproc_xml)
    ppmc.option_items_checkbox
    ppmc.option_items_textbox
    
    #create model path json file for WR28
    wr28_load_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Load.model"
    wr28_short_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_Short.model"
    wr28_offsetShort_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_OffsetShort.cascade"
    wr28_offsetThru_model  = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_ShimThru.model"
    wr28_thru_model = r"\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\WR28_MUF_Models\WR28\R11644A_IdentityThru.model"
    
    mmk = MUFModelKit(None,type='WR28')
    mmk.add_model('load',wr28_load_model)
    mmk.add_model('short',wr28_short_model)
    mmk.add_model('offset_short',wr28_offsetShort_model)
    mmk.add_model('offset_thru',wr28_offsetThru_model)
    mmk.add_model('thru',wr28_thru_model)
    mmk.add_model('gthru',wr28_thru_model)
    op = os.path.join(r'C:\SAMURAI\git\samurai\analysis\support\MUF\templates','WR28.mmk')
    mmk.write(op)
    
    
    
    

            