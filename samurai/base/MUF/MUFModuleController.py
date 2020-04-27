# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 10:12:48 2019

@author: ajw5
"""

from lxml import etree as ET
import os
from samurai.base.SamuraiXML import SamuraiXML,SamuraiXMLElement
from samurai.base.generic import subprocess_generator, get_name_from_path

test_vnauncert_xml = r"./templates/template.vnauncert"
test_postproc_xml = r"../../calibration/templates/cal_template.post"

class MUFModuleController(SamuraiXML):
    '''
    @brief base class for MUF module controllers
    @param[in] menu_path - path to menu to load
    @param[in/OPT] kwargs - keyword args as follows:
        - exe_path - executable path of the module for running (default None)
        - except_no_menu - throw an exception if no menu  (default True)
        - working_directory - directory that relative paths will be respect to. Defaults to menu directory
    '''
    def __init__(self,menu_path,**kwargs):
        '''@brief default constructor'''
        super().__init__()
        self.options = {}
        self.options['exe_path'] = None
        self.options['except_no_menu'] = True
        if menu_path is not None:
            self.options['working_directory'] = os.path.dirname(menu_path) #wdir is the menu dir by default
        else:
            self.options['working_directory'] = ''
        for k,v in kwargs.items():
            self.options[k] = v
        if menu_path is not None:
            self.load(menu_path)
        else:
            if self.options['except_no_menu']:
                raise Exception('No menu path provided') #implement default menu here
        
    def load(self,*args,**kwargs):
        '''@brief load a measurement path'''
        super().load(args[0])
        self.menu_path = args[0]
        self._controls = self.find('Controls')
        
    def write(self,*args,**kwargs):
        '''@brief write to an output path and update self.meas_path'''
        rv = super().write(*args,**kwargs)
        self.meas_path = args[0]
        return rv
        
    def run(self,out_path=None,verbose=False,text_function=print,tf_args_tuple=(),tf_kwargs_dict={}):
        '''
        @brief run our module.This will also save to output_path
        @param[in/OPT] out_path - path to write the menu to before running (and to run from) default to last loaded path
        @param[in/OPT] verbose - whether or not to be verbose
        @param[in/OPT] text_function - function that the output from the post 
            processor will be passed to (in iterated format, default is print())
            First argument must be expecting a string
        @param[in/OPT] tf_args_tuple - tuple of arguments to pass to text_function
        @param[in/OPT] tf_kwargs_dict - dictionary of kwargs to pass to text_function
        '''
        if out_path is None:
            if self.menu_path is not None:
                out_path = self.menu_path
            else:
                raise Exception("No menu loaded")
        self.write(out_path)
        out_path = os.path.abspath(out_path)
        command = self.options['exe_path']+' -r '+out_path
        if verbose: print("Running : '{}'".format(command))
        exe_generator = subprocess_generator(command)
        for out_line in exe_generator:
            text_function(out_line,*tf_args_tuple,**tf_kwargs_dict)
        
    def add_item(self,parent_element,item):
        add_muf_xml_items(parent_element,[item])
        
    def add_items(self,parent_element,item_list):
        add_muf_xml_items(parent_element,item_list)
        
    def clear_items(self,parent_element):
        clear_muf_xml_items(parent_element)
        
    def create_item(self,item_name,subitem_text_list):
        return create_muf_xml_item(item_name,subitem_text_list)
    
    def _get_name_from_path(self,path):
        '''
        @brief extract a default name from a path of a file
        @param[in] path - path to the file
        '''
        return get_name_from_path(path)
    
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
            - | - None yet!
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
        '''@brief clear all items from the list'''
        self._muf_items = [] #clear the list
        if len(self._xml_element)>0:
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
        @param[in] load_funct - function to load the data given a file path (can also be a class constructor)
        @param[in] subitem_idx - which index the path is to load (typically its self[0])
        @param[in] kwargs - keyword arguements as follows
            - working_directory - root point for relative paths. Typically should be the menu file directory
            - | - The rest of the results will be passed to load_funct
        '''
        options = {}
        options['working_directory'] = ''
        for k,v in kwargs.items():
            options[k] = v
        fpath = self.get_filepath(working_directory=options['working_directory'])
        self.data = load_funct(fpath,**kwargs)
    
    def get_filepath(self,**kwargs):
        '''
        @brief getter for filepath
        @param[in/OPT] kwargs - keyword arguements as follows:
            - working_directory - working directory for relative paths (default '')
        '''
        options = {}
        options['working_directory'] = ''
        for k,v in kwargs.items():
            options[k] = v
        fpath = self[self._filepath_subitem_idx]
        return os.path.join(options['working_directory'],fpath)
    
    @property
    def filepath(self):
        '''@brief getter for filepath (not always absolute)'''
        return self.get_filepath()
    
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
    
def create_muf_xml_item(item_name,subitem_text_list=None):
    '''
    @brief create an item from a name and list of subitems in MUF format
    @param[in] item_name - name of item (Text attribute of item).
    @param[in] subitem_text_list - list of Text attribute of Subitems
    '''
    item = ET.Element('Item',attrib={"Index":"-1","Text":item_name})
    for i,sub in enumerate(subitem_text_list):
        ET.SubElement(item,'SubItem',attrib={"Index":str(i),"Text":str(sub)})
    item.attrib['Count'] = str(len(item.getchildren()))
    return item
        
            
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
    
    
    
    

            