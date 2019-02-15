# Calibration
This directory contains code used to calibrate the synthetic apertures provided by SAMURAI


## Calibration Steps

### 1. Import metaFileController module

1. import `metaFileController.py` with the following commands or by pressing the play button in spyder with the file open in the text editor
2. run the command `evenly_split_metafile(<metafile_path>,<num_splits>)` where `<metafile_path>` is the path to the metafile to split, and `<num_splits>` is the number of measurements to evenly split it into.

### 2. Generate calibration solution

1. go to calibration folder (insert path)
2. run swap_script_s-params.py