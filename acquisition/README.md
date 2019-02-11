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
    1. Type into the windows search 'anaconda prompt' and run the program
    2. In the terminal run `conda install -c conda-forge pyvisa` to install pyvisa

## Subdirectories

### /support
This subdirectory contains multiple classes and functions to run the SAMURAI system including control for the VNA and Meca500 Robot arm. This contains the following files
- /support/autoPNAGrabber.py 
    - python control of PNAGrabber. Requires PNAGrabber executable to be run from command line with `-r` flag to 'press' the 'meas all' button without opening the UI
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
```mermaid
graph TD;
  A-->B;
  A-->C;
  B-->D;
  C-->D;
```
(PICTURE OF SETUP)
## Hardware

### Meca 500 6 axis positioner
Small 6 axis positioner.
- [Website](https://www.mecademic.com/products/Meca500-small-robot-arm)
- [User Guide](hardware/datasheets/Meca500-R3-User-Manual.pdf)
- [Programming Manual](hardware/datasheets/Meca500-R3-Programming-Manual.pdf)

### Keysight PNA-X (N5245A)
10MHz to 50GHz VNA. Ports are 2.4mm Male typically with 2.4mm F-F connector savers on them.
- [Datasheet](hardware/datasheets/N5245.pdf)

### Antennas
- Sage-millimeter 17dBi WR-28 Horn antenna
    - [Datasheet](hardware/datasheets/17dBi_horn_sagemillimeter.pdf)
- Sage-millimeter 23dBi WR-28 Horn antenna
    - [Datasheet](hardware/datasheets/23dBi_horn_sagemillimeter.pdf)

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
- PNA-X = [10.0.0.2](http://10.0.0.2)
    - VISA Address = 'TCPIP0::10.0.0.2::inst0::INSTR'
- Meca500 = [10.0.0.5](http://10.0.0.5)
    - VISA Address = Could not get VISA to work correctly! Connect using sockets.

# Running the SAMURAI Software
This section covers the steps required to run a SAMURAI measurement

## Running from python command line interface (CLI)
*[CLI]: Command Line Interface  
*[IDE]: Integrated Development Environment (e.g. Spyder)  
The following steps are to run a SAMURAI measurement from the python CLI. The steps using the python CLI here are valid for the integrated command line within the Spyder IDE. While these steps will be similar using a basic python setup, the importing of the SAMURAI classes and libraries may be a bit more complex.

### 1. Create a new SAMURAI measurement directory
1. Make a copy of 'meas_template' in the directory `U:\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture`
2. Rename the copy to the current date in the format `mm-dd-yyyy`
    - From here on, this newly created directory will be referred to as `<working-directory>`

### 2. Perform 2 Port VNA Calibration
1. In the windows file explorer navigate to `<working-directory>/cal/calibration_pre`
2. double click on 'cal.pnagrabber' to start PNAGrabber for the calibration.
3. Attach each of the standards to the calibration plane with the naming convention `<standard-port-1>_<standard-port-2>.s2p`
    - (e.g. load_short.s2p is load on port 1 and short on port 2)
4. When the calibration is completed, make a copy of each of the `.s2p` files generated and put them into the `<working-directory>/cal/calibration_pre/raw` folder

### 3. Import the SAMURAI_System Module
1. Open the python CLI (e.g. the command window in Spyder)
2. With the file opened in the Spyder IDE, click the green play button on the top toolbar OR type the code below where `<dir-of-code>` is the directory where `SAMURAI_System.py` is located on the system.
```
runfile('<dir-of-code>/SAMURAI_System.py')
```  


### 4. Create a SAMURAI_System Object
1. With the SAMURAI_System module imported, create a SAMURAI_System object by typing `mysam = SAMURAI_System()` into the CLI.

### 5. Change directory to measurement directory
1. Change the directory to `<working-directory>/synthetic_aperture/raw` by running the following set of commands:
``` 
import os
os.chdir(<working-directory>/synthetic_aperture/raw)
```
OR in certain iPython CLIs  
```
cd <working-directory>/synthetic_aperture/raw
```

### 6. Mount the Antennas
1. Mount the Tx Antenna (usually port 2) to the fixed holder
2. Move the SAMURAI Robot to the mountain position using the commands below 
    - The `mysam` object must exist for this step to work
    - Keep in mind, after this code the positioner is still connected and activated after these commands
```
mysam.connect_rx_positioner() #connect and home the positioner
mysam.move_to_mounting_position() #move to an easy position to mount the antenna
```
3. Use the four m3 screws to attach the Antenna to the Meca500
    

### 7. Run the Synthetic Aperture Sweep
Before running the sweep we can perform the extra step of viewing the robot's movement and status through its web monitoring interface.
To open up the web monitoring interface:
1. Open a web browser (tested in chrome)
2. type http://10.0.0.5 into the address bar
3. In the web interface, click the 'Connection' button on the top toolbar.
4. In the pop-up window select 'Monitoring' and click 'Connect'
Now we can begin the sweep


### 8. Unmount the Antennas 

### 9. Collect and Save data
1. copy data to raw

## Running from the Graphical User Interface (GUI) SAMURGUI
This code needs to be finished

# Measurement TODO List
- [x] Line of Sight Measurements
- [ ] Cylinder Measurement


# Code Editing TODO List