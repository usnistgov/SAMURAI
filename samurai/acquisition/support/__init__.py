import sys
import importlib

#now some aliasing for backward compatability
sys.modules['samurai.acquisition.support.samurai_metaFile'] = importlib.import_module('samurai.acquisition.support.SamuraiMetafile')
sys.modules['samurai.acquisition.support.samurai_apertureBuilder'] = importlib.import_module('samurai.acquisition.support.SamuraiApertureBuilder')
sys.modules['samurai.acquisition.support.autoPNAGrabber'] = importlib.import_module('samurai.acquisition.instrument_control.AutoPnaGrabber')



