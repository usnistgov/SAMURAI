# Support Analysis Code
This directory contains some support code that applies to all forms of analysis

## Subdirectories
Currently this folder contains the following subdirectories
- /metafile_control - classes in MATLAB and python for controlling and manipulating metafile.json files from SAMURAI measurements
- /snp_editor - Classes for MATLAB and python for reading, manipulating, and writing data in .snp (e.g. .s2p,s4p) or .wnp (e.g. .w2p,.w4p) format

### /metafile_control
This folder contains classes and functions to manipulate and read the JSON metafiles from SAMURAI measurements. The creation of these metafiles is performed by the code in '../../acquisition/support/samurai_metaFile.py'. This directory contains the following:
- metaFileController.py - A python class and some functions for editing SAMURAI JSON metafiles
- 