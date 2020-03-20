

Processing and Viewing the Data
=======================================
Here we discuss how to take a measured set of data and quickly create plots from it after a sweep has completed.

After a sweep has completed, the file in which the data was output should contain a number of \*.snp files equal to the number of positions that were swept over.
This file should also contain a 'metafile.json' and a 'metafile.raw' file. If the sweep finished correctly, the 'metafile.json' file contains all of the metadata in a javascript object notation (JSON)
file. the 'metafile.raw' is an intermediary storage file used during measurements and can be ignored.

#. Calibrate the Data

   Any required post-calibration should be performed at this point in time. Before usage, the data should also be run through any post processing algorithms.
   For example, the NIST SAMURAI system includes uncertainties in measurements through the use of the microwave uncertainty framework (MUF) for calibration.
   This calibration is performed after measurements have been taken.

#. Beamform the Data 

    In this example we will be creating a 3D interactive plot to view beamformed data. 

    .. code-block:: python 

        #import numpy
        import numpy as np

        #import the beamforming class
        from samurai.analysis.support.SamuraiBeamform import SamuraiBeamform

        #provide a path to the metafile
        metafile_path = "./metafile.json"

        #create our beamforming class
        my_samurai_beamform = SamuraiBeamform(metafile_path,verbose=True)

        #add a hamming window to reduce sidelobes
        my_samurai_beamform.set_cosine_sum_window_by_name('hamming')

        #perform beamforming
        calc_synthetic_aperture = my_samurai_beamform.beamforming_farfield_azel(
                                        np.arange(-90,90,1),np.arange(-90,90,1),freq_list=[40e9])

        #plot our data in 3D
        myplot = calc_synthetic_aperture.plot_3d()

        #show the plot in a browser
        myplot.show(renderer='browser')

More information on the steps used in post processing and available code can be found in :ref:`SAMURAI Data Analysis`

