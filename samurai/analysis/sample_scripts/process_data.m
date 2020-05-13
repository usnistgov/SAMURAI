
%% Lets first add in the locations of our required functions
% Root directory of code
samurai_root = 'path/to/samurai/root/';

% MetafileController
addpath(fullfile(samurai_root,'analysis/support/'));

% TouchstoneEditor
addpath(fullfile(samurai_root,'base/'));

%% Now lets load in all of our data
% Path to the measurement Metafile (*.json file)
metafile_path = 'path/to/metafile.json';

% Load in 'metafile.json'
mymetafile = MetafileController(metafile_path);

% Measurement files and their corresponding positions
fnames    = mymetafile.filenames;
positions = mymetafile.positions; %in mm

% Now lets load in all the measurement data
% These are stored as matlab tables
meas_data = cell(1,length(fnames));
wb = waitbar(0,'Loading the data...');
for m=1:length(fnames)
    waitbar(m/length(fnames),wb,'Loading the data...');
    meas_data{m} = TouchstoneEditor(fnames{m});
end
close(wb)

%% Now process data from a single element
% Get S21 from a single element position
single_S21 = meas_data{1}.S21;       
freqs_ghz  = meas_data{1}.frequency; %in GHz
fd_fig = figure();
plot(freqs_ghz,20*log10(abs(single_S21)));
xlabel('Frequency (GHz)'); ylabel('Magnitude (dB)');

% Now we can generate the time domain version of this
td_S21 = ifft(single_S21);
max_time = 1/mean(diff(freqs_ghz));
time_step = 1/(max(freqs_ghz)-min(freqs_ghz));
times_ns = 0:time_step:max_time;
td_fig = figure();
plot(times_ns,20*log10(abs(td_S21)));
xlabel('Time (ns)'); ylabel('Magnitude (dB)');

%% We can now perform a basic beamforming example
% extract position components (to meters)
x_pos = positions(1,:)./1e3;
y_pos = positions(2,:)./1e3;
z_pos = positions(3,:)./1e3;

% and S21 data for each element
S21_data = cell2mat(cellfun(@(c) c.S21,meas_data ...
    ,'UniformOutput',false));

% Beamform at our first frequency
beamform_frequency_idx = 1;
lambda = 299792458/(freqs_ghz(beamform_frequency_idx)*1e9);
k = (2*pi)/lambda;

% Azimuth and elevation angles to calculate
az = linspace(-90,90,181);
el = zeros(size(az));

% Convert to azel to uv. This assumes no change
% in z_pos between elements
u = cos(deg2rad(el)).*sin(deg2rad(az));
v = sin(deg2rad(el));

% And beamform
beamformed_values = 1/length(x_pos).*sum(...
    S21_data(beamform_frequency_idx,:)...
    .*exp(-1i.*k.*((x_pos.*u.')+(y_pos.*v.')))...
    ,2);

% Finally, Plot
bf_fig = figure();
plot(az,20*log10(abs(beamformed_values)));
xlabel('Azimuth (degrees)'); ylabel('Magnitude (dB)');

%% This can then be repeated for all frequencies in a single angle
% Calculate all frequencies at boresight
az1 = -28; el1 = 0;

% Convert to azel to uv. This assumes no change
% in z_pos between elements
u1 = cos(deg2rad(el1)).*sin(deg2rad(az1));
v1 = sin(deg2rad(el1));

% Calculate K for all frequencies
lambda_all = 299792458./(freqs_ghz*1e9);
k_all = (2*pi)./lambda_all;

% And beamform
beamformed_1angle = 1/length(x_pos).*sum(...
    S21_data...
    .*exp(-1i.*k_all.*((x_pos.*u1)+(y_pos.*v1)))...
    ,2);

% Finally, Plot
bf1fd_fig = figure();
plot(freqs_ghz,20*log10(abs(beamformed_1angle)));
xlabel('Frequency (GHz)'); ylabel('Magnitude (dB)');

% And plot the time domain
bf1td = ifft(beamformed_1angle);
max_time = 1/mean(diff(freqs_ghz));
time_step = 1/(max(freqs_ghz)-min(freqs_ghz));
times_ns = 0:time_step:max_time;
bf1td_fig = figure();
plot(times_ns,20*log10(abs(bf1td)));

