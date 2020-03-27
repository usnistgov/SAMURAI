import sys 
import importlib

sys.modules['samurai.analysis.support.MetaFileController'] = importlib.import_module('samurai.analysis.support.MetafileController')
sys.modules['samurai.analysis.support.MUFResult'] = importlib.import_module('samurai.base.MUF.MUFResult')
sys.modules['samurai.analysis.support.MUF'] = importlib.import_module('samurai.base.MUF')
