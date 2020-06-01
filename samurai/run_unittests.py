# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 16:14:52 2019
run different unittests
@author: ajw5
"""
import unittest
#%% initialize some things
test_list = [] #classes of unittests to run

#%% SamuraiDict Testing
from samurai.base.SamuraiDict import TestSamuraiDict
test_list.append(TestSamuraiDict)

#%% Touchstone Editor unit testing
from samurai.base.TouchstoneEditor import TestTouchstoneEditor
test_list.append(TestTouchstoneEditor)

#%% MUF Result testing
from samurai.base.MUF.MUFResult import TestMUFResult
test_list.append(TestMUFResult)

#%% SamuraiMeasurement Testing
from samurai.base.SamuraiMeasurement import TestSamuraiMeasurement
test_list.append(TestSamuraiMeasurement)

#%% now run them all
import time
time.sleep(0.5) #sleep for a bit to let loaded modules be printed
loader = unittest.TestLoader()
suite_list = [loader.loadTestsFromTestCase(tc) for tc in test_list]
unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))
