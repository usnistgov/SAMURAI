'''
@brief a class for a metafile gui (this will be added to a samurgui page to output a dictionary of variables)
'''

import os
import sys
import numpy as np
#sam_control_path = 'U:/67Internal/DivisionProjects/Channel Model Uncertainty/Measurements/Software/SAMURAI_Control'
#sys.path.append(sam_control_path)
from samurai_metaFile import samurai_metaFile

from support.samurai_tktools import FilePicker
from support.samurai_tktools import DirPicker
from support.samurai_tktools import EntryAndTitle
from support.samurai_tktools import CheckGroup

try: #backward compatability with 2.7
    import Tkinter as tk
    #import tkFileDialog
except ImportError:
    import tkinter as tk
    #from tkinter import filedialog as tkFileDialog
    

class MetafileGUI():
    
    def __init__(self,tkroot):

        self.tkroot = tkroot
        
        
        
        
        
        
        
        
        
        
root = tk.Tk()
cdg = MetafileGUI(root)
root.mainloop()
        