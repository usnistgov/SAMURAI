# -*- coding: utf-8 -*-
"""
Created on Wed Sep 05 14:12:07 2018
aweiss tk gui tools
@author: ajw5
"""

try: #backward compatability with 2.7
    import Tkinter as tk
    import tkFileDialog
except ImportError:
    import tkinter as tk
    from tkinter import filedialog as tkFileDialog
#import tkFileDialog
import os

#class Al_TkTools():

#Class that gives an input and browse button for choosing a file
class FilePicker(tk.Frame):
    def __init__(self,root,title,default_val='Enter Value',prompt="Select File",width=100,filetypes=(('All Files','*.*'),),**kwargs):
        #print(kwargs)
        tk.Frame.__init__(self,root,kwargs)
        self.prompt = prompt
        self.main_frame = self
        self.title = tk.Label(self.main_frame,text=title,width=width)
        self.title.pack()
        self.picker_frame = tk.Frame(self.main_frame)
        self.entry = tk.Entry(self.picker_frame,width=width)
        self.entry.insert(0,default_val)
        self.entry.pack(side=tk.LEFT)
        self.browse_but = tk.Button(self.picker_frame,text='...',command=lambda: self.browse_file(filetypes))
        self.browse_but.pack(side=tk.LEFT)
        self.picker_frame.pack()
        
        self.default_val = default_val
    
    
    def browse_file(self,filetypes=(('All Files','*.*'),)):
         search_start = os.path.split(self.entry.get())[0]
         path = tkFileDialog.askopenfilename(initialdir=search_start,title=self.prompt,filetypes=filetypes)
         if(os.path.isabs(path)):
             self.entry.delete(0,tk.END)
             self.entry.insert(0,path)
         
    def get(self):
        return self.entry.get()
    
class DirPicker(tk.Frame):
    def __init__(self,root,title,default_val='Enter Value',prompt="Select File",width=100,**kwargs):
        #print(kwargs)
        tk.Frame.__init__(self,root,kwargs)
        self.prompt = prompt
        self.main_frame = self
        self.title = tk.Label(self.main_frame,text=title,width=width)
        self.title.pack()
        self.picker_frame = tk.Frame(self.main_frame)
        self.entry = tk.Entry(self.picker_frame,width=width)
        self.entry.insert(0,default_val)
        self.entry.pack(side=tk.LEFT)
        self.browse_but = tk.Button(self.picker_frame,text='...',command=self.browse_dir)
        self.browse_but.pack(side=tk.LEFT)
        self.picker_frame.pack()
        
        self.default_val = default_val
        
    def browse_dir(self):
         path = tkFileDialog.askdirectory(initialdir=self.get(),title='Select Working Directory')
         self.entry.delete(0,tk.END)
         self.entry.insert(0,path)
         
    def get(self):
        return self.entry.get()
        
#calDir   = os.path.join(wdir,'./preCal_vnauncert_Results/')
class EntryAndTitle(tk.Frame):

    def __init__(self,tkroot,title,default_entry='default',title_loc=tk.TOP,width=10,**kwargs):
        self.root=tkroot
        tk.Frame.__init__(self,tkroot,kwargs)
        self.title_loc = title_loc
        self.width = width
        self.frame = self
        self.label_var = tk.StringVar()
        self.title = tk.Label(self.frame,text=title,textvariable=self.label_var,width=width)
        self.label_var.set(title)
        self.title.pack()
        self.entry = tk.Entry(self.frame,width=width)
        self.entry.insert(0,default_entry)
        self.entry.pack()
        
    #redefinitions of some entry stuff. Not sure I could inherit because
    #it needs to be a frame. could inherit from frame but didnt
    def delete(self,idx,stop):
        self.entry.delete(idx,stop)
    def insert(self,idx,item):
        self.entry.insert(idx,item)
    def get(self):
        return self.entry.get()
    
class CheckGroup(tk.LabelFrame):
    def __init__(self,root,title,check_button_name_list,pack_side=tk.LEFT,**kwargs):
        tk.LabelFrame.__init__(self,root,kwargs,text=title)
        self.check_button_name_list = check_button_name_list
        self.num_buttons = len(check_button_name_list)
        self.button_vars = [tk.IntVar() for i in range(self.num_buttons)] 
        self.buttons = []
        for i in range(self.num_buttons):
            self.buttons.append(tk.Checkbutton(self,text=self.check_button_name_list[i],variable=self.button_vars[i]))
            self.buttons[i].pack(side=pack_side)
            
    #button can be passed as name of button or number
    def get_button_state(self,button):
        if type(button)==str: #get th index if its a string
            button_num = self.check_button_name_list.index(button)
        else: #else we passed a number
            button_num = button
        return self.button_vars[button_num].get()
    
    get = get_button_state #alias
    
    def print_debug(self):
        print("Check Group Debug")
        print("   %d total buttons" %(self.num_buttons))
        print("   ---Button States---")
        for i in range(self.num_buttons):
            print("      %s : %d" %(self.check_button_name_list[i],self.get_button_state(i)))
            
class ButtonGroup(tk.LabelFrame):
    def __init__(self,root,title,button_name_list,button_function_list,pack_side=tk.LEFT,**kwargs):
        tk.LabelFrame.__init__(self,root,kwargs,text=title)
        self.button_name_list = button_name_list;
        self.button_function_list = button_function_list
        self.num_buttons = len(button_name_list)
        self.button_vars = [tk.IntVar() for i in range(self.num_buttons)] 
        self.buttons = []
        for i in range(self.num_buttons):
            self.buttons.append(tk.Button(self,text=self.button_name_list[i],command=self.button_function_list[i]))
            self.buttons[i].pack(side=pack_side)
            
class NotificationGroup(tk.LabelFrame):
    """
    @brief: class to hold information on status of system this will update every given amount of time
    """
    def __init__(self,root,title,notification_name_list,notification_value_list,pack_side=tk.BOTTOM,**kwargs):
        tk.LabelFrame.__init__(self,root,kwargs,text=title)
        self.num_notifications = len(notification_name_list) #number of notificaitons
        self.notifications = {} #dicitionary holding the key value combos
        self.notification_vars = {}
        self.notification_value_list = notification_value_list
        self.notification_name_list = notification_name_list
        self.sv = tk.StringVar()
        self.sv.set("Testing")  
        for name in notification_name_list: #generate text boxes
            self.notification_vars[name] = tk.StringVar()
            self.notifications[name] = tk.Label(root,textvariable=self.notification_vars[name])
            self.notifications[name].pack(side=pack_side);
            self.notification_vars[name].set("Not set")
        self.update_from_list(notification_value_list)
        #self.sv.set("Testing")  
        
    def update_from_list(self,value_list):
        """ 
        @brief update from list of variables (assuming correct order)
        """
        self.notification_value_list = value_list
        i=0;
        for key in self.notifications:
            value = self.notification_value_list[i]
            self.notification_vars[key].set("%15s : %10s" %(str(key),str(value)))
            i+=1
        
    def update_from_dict(self,value_dict):
        """
        @brief update from dictionary
        """
        for key,value in value_dict:
            self.notification_vars[key].set("%15s : %10s" %(str(key),str(value)))
            
    def get(self):
        """ 
        @brief get a dictionary of our values
        """
        rv = {}
        for key in self.notifications:
            rv[key] = self.notification_vars[key].get();
        return rv;
            
#button that will open a new window and display help
class HelpButton(tk.Button):
    
    def __init__(self,root,help_text,button_text='Need Help? Click Me.',help_window_title='Help Window',**kwargs):
        tk.Button.__init__(self,root,kwargs=kwargs,text=button_text,command=self.open_help_window)
        self.root = root
        self.help_window_title = help_window_title
        self.help_text = help_text
        
    def open_help_window(self):
        self.help_window = tk.Toplevel(self)
        self.help_window.wm_title(self.help_window_title)
        l = tk.Label(self.help_window, text=self.help_text,justify=tk.LEFT)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)

    
        