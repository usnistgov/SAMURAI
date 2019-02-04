# Acquisition Code
This directory contains the code required to run the SAMURAI system. This currently requires a direct path and connection to the U:/ network drive.

## Subdirectories

### /support
This subdirectory contains multiple classes and functions to run the SAMURAI system including control for the VNA and Meca500 Robot arm. This contains the following files
- autoPNAGrabber.py
- Meca500.py
- metaFileController.py
- pnaController.py
- samurai_metaFile.py
- samurai_support.py

## SAMURAI Setup Information
Currently, the samurai system is run over a custom local network run through a simple network switch. This connects to the VNA, Meca500 Robot arm, and eventually cameras. The IP addresses for these are as follows:
- PNA-X = 10.0.0.2
- Meca500 = 10.0.0.5