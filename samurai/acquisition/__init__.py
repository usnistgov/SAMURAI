import sys
import importlib

import samurai.acquisition.SamuraiSystem
import samurai.acquisition.support
import samurai.acquisition.instrument_control

#now some aliasing for backward compatability
sys.modules['samurai.acquisition.SAMURAI_System'] = importlib.import_module('samurai.acquisition.SamuraiSystem')


