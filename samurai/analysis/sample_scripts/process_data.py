
#%% Lets first import the required libraries
# Libraries in the samurai package
from samurai.base.TouchstoneEditor import TouchstoneEditor
from samurai.analysis.support.MetafileController import MetafileController
from samurai.base.generic import ProgressCounter

# External Libraries
import numpy as np
import plotly.graph_objs as go

#%% Now lets load in all of our data
# Path to the measurement Metafile (*.json file)
metafile_path = r'path/to/metafile.json'

# Load in 'metafile.json'
mymetafile = MetafileController(metafile_path)

# Measurement files and their corresponding positions
fnames    = mymetafile.filenames
positions = mymetafile.positions #in mm

# Now lets load in all the measurement data
# These are stored as matlab tables
meas_data = []
pc = ProgressCounter(len(fnames),'Loading the data...')
for fname in fnames:
    meas_data.append(TouchstoneEditor(fname))
    pc.update()
    
pc.finalize()

#%% Now process data from a single element
# Get S21 from a single element position
single_S21 = meas_data[0].S21 # Pandas Series type
freqs      = meas_data[0].freqs #in Hz
fd_fig = go.Figure()
fd_fig.add_trace(go.Scatter(
    x=freqs/1e9,
    y=20*np.log10(np.abs(single_S21.to_numpy()))
    ));
fd_fig.update_layout(
    xaxis_title='Frequency (GHz)',
    yaxis_title='Magnitude (dB)')
fd_fig.show(renderer='svg')

# Now we can generate the time domain version of this
td_S21 = np.fft.ifft(single_S21)
max_time = 1/np.mean(np.diff(freqs))
time_step = 1/(max(freqs)-min(freqs))
times_ns = np.arange(0,max_time,time_step)*1e9
td_fig = go.Figure()
td_fig.add_trace(go.Scatter(
    x=times_ns,
    y=20*np.log10(np.abs(td_S21))
    ));
td_fig.update_layout(
    xaxis_title='Time (ns)',
    yaxis_title='Magnitude (dB)')
td_fig.show(renderer='svg')

#%% We can now perform a basic beamforming example
# extract position components (to meters)
x_pos = positions[:,0]/1e3
y_pos = positions[:,1]/1e3
z_pos = positions[:,2]/1e3
# and S21 data for each element
S21_data = np.array([meas.S21.to_numpy() for meas in meas_data])

# Beamform at our first frequency
beamform_frequency_idx = 0
lam = 299792458/(freqs[beamform_frequency_idx])
k = (2*np.pi)/lam

# Azimuth and elevation angles to calculate
az = np.linspace(-90,90,181)
el = np.zeros(az.shape)

# Convert to azel to uv. This assumes no change
# in z_pos between elements
u = np.cos(np.deg2rad(el))*np.sin(np.deg2rad(az))
v = np.sin(np.deg2rad(el))

# And beamform
beamformed_values = (
    (1/len(x_pos))*np.sum(
        S21_data[:,beamform_frequency_idx][...,np.newaxis]
        *np.exp(-1j*k*(
            (x_pos[...,np.newaxis]*u[np.newaxis])+
            (y_pos[...,np.newaxis]*v[np.newaxis])
            )
        )
    ,axis=0));

# Finally, Plot
bf_fig = go.Figure()
bf_fig.add_trace(go.Scatter(
    x=az,
    y=20*np.log10(np.abs(beamformed_values))
    ));
bf_fig.update_layout(
    xaxis_title='Azimuth (degrees)',
    yaxis_title='Magnitude (dB)')
bf_fig.show(renderer='svg')

#%% This can then be repeated for all frequencies in a single angle
# Calculate all frequencies at boresight
az1 = 16; el1 = 0;

# Convert to azel to uv. This assumes no change
# in z_pos between elements
u1 = np.cos(np.deg2rad(el1))*np.sin(np.deg2rad(az1))
v1 = np.sin(np.deg2rad(el1))

# And beamform
beamformed_1angle = (
    (1/len(x_pos))*np.sum(
        S21_data
        *np.exp(-1j*k*(
            (x_pos[...,np.newaxis]*u1)+
            (y_pos[...,np.newaxis]*v1)
            )
        )
    ,axis=0));

# Finally, Plot
bf1fd_fig = go.Figure();
bf1fd_fig.add_trace(go.Scatter(
    x=freqs/1e9,
    y=20*np.log10(np.abs(beamformed_1angle))
    ));
bf1fd_fig.update_layout(
    xaxis_title='Frequency (GHz)',
    yaxis_title='Magnitude (dB)')
bf1fd_fig.show(renderer='svg')

# And plot the time domain
bf1td = np.fft.ifft(beamformed_1angle)
max_time = 1/np.mean(np.diff(freqs))
time_step = 1/(max(freqs)-min(freqs))
times_ns = np.arange(0,max_time,time_step)*1e9
bf1td_fig = go.Figure();
bf1td_fig.add_trace(go.Scatter(
    x=times_ns,
    y=20*np.log10(np.abs(bf1td))
    ));
bf1td_fig.update_layout(
    xaxis_title='Frequency (GHz)',
    yaxis_title='Magnitude (dB)')
bf1td_fig.show(renderer='svg')





