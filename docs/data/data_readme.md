# Dataset Information

The folders are named in the following manner

	(month)-(date)-(year)

Within each folder there is a subfolder named '/calibrated' This folder contains the most up to date calibrated data for the run and that data 
should be used for calculations.

Each subfolder within this folder contains data from a measurement. Within each of these subfolders there exists a set of measurements named 'meas#.s2p'
and a metafile named 'metaFile.json'. This metafile contains almost all information regarding to the measurement setup and run.

##metaFile Description
The metafile is a *.json file (typically under the name metaFile.json) that provides useful information to both load and track information on the measurements
This file is easily human readable and information on the experiment can be found at the top of the file. The following set of keys are 
the most useful within the file

 - 'working_directory' : provides the path to the current directory
 - 'experiment'        : very brief info on the experiment
 - 'vna_info'          : a dictionary with information on the VNA settings used during the experiment
 - 'antennas'          : a list of dictionaries describing characteristics of the antennas used
 - 'notes'             : More information about the experiment
 - 'measurements'      : a list of dictionaries containing the following info
	- 'position_key' : what each position is
	- 'position'     : position used for each value in position_key
	- 'filename'     : location of the file (relative to working_directory) of the file

There are a few other keys within the file but these are the most useful. A 'units' key has been added in later versions to give the units of the axes

# Datasets

## Optical Table Measurements

### 4-13-2018
This day we measured a flat plane that spans the whole reach of the positioner. The steps of this are much larger than a single wavelength
and the total aperture size is >10 wavelengths. This data will probably not be used

### 5-11-2018
This was the initial day where line of sight synthetic apertures were tested. The vna was set to a frequency range of 28-30 GHz with 20MHz steps
 Both a measurement with the transmitter about 10 degrees in the azimuth direction and 5 degrees in the elevation offset from the reciever were taken
Again both are contained within the '/calibrated' folder

### 5-15-2018
Another line of sight was taken here the the transmitter both 10 degrees in the azimuth and 5 degrees in elevation at the same time
Measurements on this day were taken from 26.5 to 40GHz with a step of 10MHz and an IFBW of 10. 

### 5-24-2018
This setup was measuring a reflection off the front face (with windows) of the cabinets in a non-LOS setup

### 5-31-2018
This is the same setup as 5-24 but with a much large array size to allow for finer angular resolution.

### 12-12-2018
This was the initial day of measurements using the new SAMURAI setup with the Meca500 positioner and the optical table. In this configuration the cabinets with attached absorber were directly behind the meca500 with absorber covering the vna on the left (from behind the meca view) and absorber covering the table. There was also absorber behind the transmit antenna.

### 12-17-2018
The setup for this day was the same as 12-12-2018 but removed the absorber from the middle part of the table. 

### 12-18-2018 
The setup for this day was the same as 12-12-2018 but removed the cabinetes from behind the recieve side.

### 12-19-2018
The setup was again the same as 12-12-2018 but a small piece of absorber with spikes on it was placed in the center on top of the flat absorber to try and reduce the ground bounce from the absorber.

### 1-30-2019

### 2-1-2019
3 Planar Apertures offset in the X direction by lambda/4 @ 30GHz (2.5mm)

### 2-4-2019
3 Cylinder Apertures offset in the X direction by lambda/4 @ 30GHz (2.5mm)

### 2-6-2019
This measurement had the small spiked absorber placed in between the Tx and Rx at the ground bounce location. There was also the large aluminum (~6" ducting) cylinder placed ~10 degrees to the right when looking at the Tx from behind the Rx.
 
### 2-7-2019
This is the same as 2-6-2019 but with the small steel pipe used as a cylinder at the same location as before.

### 2-13-2019
4" aluminum Cylinder (ducting with LOS blocked and TX antenna pointed directly at cylinder)

### 2-14-2019
Same as 2-13-2019 but with small cylinder (steel pipe)

### 2-20-2019
Same as 2-13-2019 and 2-14-2019, but without a cylinder

### 3/1/2019
measured two 4" cylinders (ducting) with one on bislide at different locations

### 3/4/2019
measured two 1" steel cylinders (same as 3-1-2019 with 1" cylinders)

### 3/20/2019
first measurement with active scatterers (3 horns) at bislide=340 and 520 mm

### 6-17-2019 
Line of sight on optical table with new mount and no absorber fence behind rx

### 6-18-2019 
Line of sight on optical table with new mount and absorber fence behind rx

### 6-19-2019 
Measurement of milk crate for CUP mount

### 7-8-2019 
Line of Sight measurement with new spiked absorber on most of optical table

### 7-8-2019_cable_test 
cable bending measurement with newest SAMURAI setup. 1 Port Cal run on robotic arm (SOL)


## Conference Room Data
This data was taken in the wing 6 4604 conference room at NIST 

### 5/17/2019
Measurement in the conference room. Both Tx and Rx on opposite ends of the table facing the outside wall. 

### 5/24/2019
Second conference room measurement. Tx and Rx pointed at one another through the window

### 5/31/2019
Third and final conference room measurement. Tx at glancing angle through glass pointed toward whiteboard. Rx aperture pointing toward whiteboard inside room


## Central Utility Plant (CUP) Data
This data was taken at the the central Utility Plant (CUP) at the NIST boulder site

### 8-7-2019
First day of real measurements in CUP. THis was taken without the rack in a high multipath environement

### 8-8-2019
Second day. Large metal rack to left when looking from behind the aperture

### 8-9-2019
Third day. Weekend measurement with 5 repeats of the same measurement with TX pointed upward.

### 8-12-2019
After weekend. Today we measured with large rack in the center of the work space (blocking the control panel)

### 8-13-2019
Again the rack was removed to test the channel

### 8-16-2019
Last day. We measured 3 offset planes (offset by lambda/2 @ 40GHz) and a cylindrical cut of the same channel

