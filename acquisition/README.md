# Acquisition Code
This directory contains the code required to run the SAMURAI system. This currently requires a direct path and connection to the U:/ network drive. This code has been tested lately with python 3.6 but should be backward compatable with 2.7.

## dependencies
- Anaconda with python 3.X
- pyvisa
- cannot remember the last one

### Installing Anaconda and Dependencies
- Install Anaconda 
    1. Go to the download page at https://www.anaconda.com/distribution/#download-section
    2. Select the correct operating system and installer
    3. Download and run the executable and follow the installer to install Anaconda 3.X
- Install pyvisa 
    1. Type into the windows search 'Anaconda Prompt' and run the program
    2. In the terminal run 'conda install -c conda-forge pyvisa' to install pyvisa

## Subdirectories

### /support
This subdirectory contains multiple classes and functions to run the SAMURAI system including control for the VNA and Meca500 Robot arm. This contains the following files
- /support/autoPNAGrabber.py 
    - python control of PNAGrabber. Requires PNAGrabber executable to be run from command line with '-r' flag to 'press' the 'meas all' button without opening the UI
- /support/Meca500.py 
    - Class for controlling Meca500 Robot
- /support/metaFileController.py 
    - Class for interacting with already written metafile from a measurement
- /support/pnaController.py 
    - Class to interact with PNA to get various settings and set some things on it
- /support/samurai_metaFile.py 
    - Class for creating metafile for SAMURAI measurements
- /support/samurai_support.py 
    - Some support functions to use. (mainly functions used when USC came out in Aug. 2018 for phased array calibration)

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
- Junkosha 2.4mm (M-M) 3m Cables
    - info (link datasheet)
- Junkosha 2.4mm (M-M) 0.25m Cables
    - info (link datasheet)

### Adapters
- Sage-millimeter 2.4mm to WR-28 Adapters

## Networking
Currently, the samurai system is run over a custom local network run through a simple network switch. This connects to the VNA, Meca500 Robot arm, and eventually cameras.

### Remote PNA-X control
-Info on Remote KVM setup

### IP and VISA Addresses
- PNA-X = 10.0.0.2
    - VISA Address = 'TCPIP0::10.0.0.2::inst0::INSTR'
- Meca500 = 10.0.0.5
    - VISA Address = Could not get VISA to work correctly! Connect using sockets.

# Running the SAMURAI Software
This section covers the steps required to run a SAMURAI measurement

## Running from python command line interface (CLI)
The following steps are to run a SAMURAI measurement from the python command line interface (CLI). The steps using the python CLI here are valid for the integrated command line within the spyder IDE. While these steps will be similar using a basic python setup, the importing of the SAMURAI classes and libraries may be a bit more complex.

### 1. Create a new SAMURAI measurement directory

### 2. Perform 2 Port VNA Calibration

### 3. Import the SAMURAI_System Module

### 4. Create a SAMURAI_System Object

### 5. Change directory to measurement directory

### 6. Mount the Antennas

### 7. Run the Synthetic Aperture Sweep

### 8. Unmount the Antennas 

### 9. Collect and Save data

## Running from the Graphical User Interface (GUI) SAMURGUI
This code needs to be finished