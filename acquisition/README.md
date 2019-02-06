# Acquisition Code
This directory contains the code required to run the SAMURAI system. This currently requires a direct path and connection to the U:/ network drive.

## Subdirectories

### /support
This subdirectory contains multiple classes and functions to run the SAMURAI system including control for the VNA and Meca500 Robot arm. This contains the following files
- /support/autoPNAGrabber.py - python control of PNAGrabber. Requires PNAGrabber executable to be run from command line with '-r' flag to 'press' the 'meas all' button without opening the UI
- /support/Meca500.py - Class for controlling Meca500 Robot
- /support/metaFileController.py - Class for interacting with already written metafile from a measurement
- /support/pnaController.py - Class to interact with PNA to get various settings and set some things on it
- /support/samurai_metaFile.py - Class for creating metafile for SAMURAI measurements
- /support/samurai_support.py - Some support functions to use. (mainly functions used when USC came out in Aug. 2018 for phased array calibration)

# SAMURAI Hardware Information

(PICTURE OF SETUP)
## Hardware

### Meca 500 6 axis positioner
Info here

### Keysight PNA-X (N5245A)
Info here

### Antennas
- Sage-millimeter 17dBi WR-28 Horn antenna
    - info here (link datasheet)
- Sage-millimeter 23dBi WR-28 Horn antenna
    - info here (link datasheet)

### Cables
- Junkosha 3m
    - info (link datasheet)
- Junkosha 0.25m (link datasheet)
    - info (link datasheet)

## Networking Information
Currently, the samurai system is run over a custom local network run through a simple network switch. This connects to the VNA, Meca500 Robot arm, and eventually cameras. The IP addresses for these are as follows:
- PNA-X = 10.0.0.2
    - VISA Address = 'TCPIP0::10.0.0.2::inst0::INSTR'
- Meca500 = 10.0.0.5
    - VISA Address = Could not get VISA to work correctly! Connect using sockets.



# Running the SAMURAI Software
This section covers the steps required to run a SAMURAI measurement
## Running from python command line interface (CLI)