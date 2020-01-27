"""
Created on Fri Aug  2 09:11:34 2019
This template script to automatically set many parameters of the vna
PLEASE DO NOT COMMIT EXPERIMENT SPECIFIC CHANGES TO THIS SCRIPT.
@author: ajw5
"""
from samurai.acquisition.instrument_control.PnaController import PnaController

#set our parameters to set on the VNA
if_bw = 100
sweep_delay = 0.0005
dwell_time = 0.001
start_freq = 26.5e9
stop_freq = 40e9
num_pts = 1351
pow_dbm = 0

#set the VNA visa address
visa_addr = 'TCPIP0::192.168.0.2::inst0::INSTR'

#connect to the VNA
mypna = PnaController(visa_addr)

#setup an s parameter sweep on ports 1 and 3
mypna.setup_s_param_measurement([11,31,13,33])
mypna.set_continuous_trigger('ON')

#write our parameters to the VNA
mypna.write('if_bandwidth',if_bw)
mypna.write('sweep_delay_time',sweep_delay)
mypna.write('dwell_time',dwell_time)
mypna.write('power',pow_dbm)
mypna.set_freq_sweep(start_freq,stop_freq,num_pts= num_pts)