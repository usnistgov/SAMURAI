"""
Created on Fri May 17 14:08:56 2019
This template script is to setup and run a full sweep of the samurai system.
PLEASE DO NOT COMMIT EXPERIMENT SPECIFIC CHANGES TO THIS SCRIPT.
This does NOT set VNA settings so that should be done beforehand.
This does NOT use PNAGrabber by default.
Motive MUST be running and rigid bodies must be defined before running this script.
@author: ajw5
"""

from samurai.acquisition.SAMURAI_System import SAMURAI_System
from collections import OrderedDict

## configuration for motive
motive_dict = {}
motive_dict['meca_head'] = None
motive_dict['origin']    = None
motive_dict['tx_antenna'] = None
#labeled markers
motive_dict['vna_marker'] = 50716

position_file = './position_templates/samurai_planar_dp.csv'
output_dir = './'

#info to put into metafile
metafile_info_dict = {}
metafile_info_dict["experiment"] = None
metafile_info_dict["experiment_photo_path"] = "../external_data/pictures/"
rx_ant = OrderedDict()
rx_ant["name"]          = "Sage Millimeter 17dBi rectangular horn (SAR-1725-28-S2)"
rx_ant["txrx"]          = "rx"
rx_ant["location"]      = None
rx_ant["gain_dbi"]      = 17
rx_ant["beamwidth_e"]   = 23
rx_ant["beamwidth_h"]   = 24
rx_ant["serial_number"] = "14172-01"
tx_ant1 = OrderedDict()
tx_ant1["name"]          = "Sage Millimeter 17dBi rectangular horn (SAR-1725-28-S2)"
tx_ant1["txrx"]          = "tx"
tx_ant1["location"]      = None
tx_ant1["gain_dbi"]      = 17
tx_ant1["beamwidth_e"]   = 23
tx_ant1["beamwidth_h"]   = 24
tx_ant1["serial_number"] = "14172-02"
metafile_info_dict["antennas"] = [rx_ant,tx_ant1]
#metafile_info_dict["scatterers"] = "Active scatterers (sources) see \"antennas\" data" #[cyl_1,cyl_2]
metafile_info_dict["notes"] = None


mysam = SAMURAI_System()
mysam.connect_rx_positioner()
mysam.csv_sweep(output_dir,position_file,external_position_measurements=motive_dict,
                                            metafile_header_values=metafile_info_dict)
mysam.disconnect_rx_positioner()