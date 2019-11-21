
addpath(genpath('C:\Users\bfj\Projects\ChannelModeling\maria\MATLAB_CODE_REPOSITORY\CURRENT\'))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load the data from the debug.mat file
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
origData = load('C:\Users\bfj\Code\channelData\TestPostProcessor\debugMatlab\debug.mat');
newData = load('jonesReverb.mat');  

% Down sample frequency
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Frequency range doesn't match 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Naive
%fBegin = 1;
%fStep = 200;
%newS21 = complex(newData.measS21(:,fBegin:fStep:end,4) + 1i*newData.measS21(:,fBegin:fStep:end,5));
%newFreqs = newData.freqs(fBegin:fStep:end)';
%newFreqs = newFreqs/(10^9);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Low end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fBegin = 1;
fStep = 134;
fEnd = 2802;
newS21 = complex(newData.measS21(:,fBegin:fStep:fEnd,4) + 1i*newData.measS21(:,fBegin:fStep:fEnd,5));
newFreqs = newData.freqs(fBegin:fStep:fEnd)';
newFreqs = newFreqs/(10^9);

color = {[0 0.4470 0.7410], [0.8500 0.3250 0.0980],[0.4660 0.6740 0.1880], [0.9290 0.6940 0.1250], [0.4940 0.1840 0.5560]...
          [0.3010 0.7450 0.9330], [0.6350 0.0780 0.1840]};

numFreqs  = length(origData.freqs);
      
turn = -18*pi/180;  % acounts for offset between recorded turntable position and definition of zero angle at x axis of chamber
turnd = -18;

timeCutoff = 30e-9; % 30 nano seconds

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Set up some angle data
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
dEl = 4.0; % Needs to be a divisor of 90
dAz = 4.0; % in degrees

dElr = dEl*pi/180; 
dAzr = dAz*pi/180;

elVals = linspace(-pi/2, pi/2, pi/dElr + 1);
azVals = linspace(0,2*pi - dAzr, (2*pi)/dAzr);
[el, az] = ndgrid(elVals, azVals);

angles = zeros(size(elVals,2)*size(azVals,2), 2);
angles(:,1) = reshape(el, [], 1);
angles(:,2) = reshape(az, [], 1);

azS = (0:dAz:360-dAz).'*pi/180;
elS = (-90:dEl:90).'*pi/180;

phi = azS;
theta = elS;
[p,t] = meshgrid(phi, theta);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Setup time grid
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
dt = 1.0/(origData.freqs(end) - origData.freqs(1));
cutoffTime = 30*10^(-9);
timeCutoffIndex = ceil(cutoffTime/dt) + 1;
delayTimes = (0:timeCutoffIndex - 1)*dt;      

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Now Rays from Maria's Ray Tracing Simulation
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
numAngles = 2;
specificAngles = zeros(numAngles,2);

specificAngles(1,1) = -20;
specificAngles(1,2) = 90.8; %72.8 - turnd;
specificAngles(2,1) = -10.0;
specificAngles(2,2) = 171.1; %153.1 - turnd;
specificAngles = specificAngles*pi/180.0;


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Orig. Data
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[hThetaF1, hThetaTau1, pdap1, azPdap1, hThetaFS1, hThetaTauS1] = ...
    beamforming3D(origData.s21, origData.freqs, origData.coords, ...
                  angles, el, az, specificAngles);



azPdap_plot1 = squeeze(azPdap1(:,:)./max(max(abs(azPdap1(:,:)))));

plotAzPap(delayTimes*1E9, azPdap_plot1(:,1:timeCutoffIndex), azS*180.0/pi, '')

plotAnglePdp(delayTimes*1E9, hThetaTauS1(:,1:timeCutoffIndex))

plotFishPlot(pdap1, p, t, turn, 'Prev. Data w/ Beamforming')

hThetaFr1 = reshape(hThetaF1, length(elVals) ,length(azVals), 21);
figure
contourf(azVals, elVals, abs(hThetaFr1(:,:,1)).^2)
figure
contourf(azVals, elVals, abs(hThetaFr1(:,:,end)).^2)

[hThetaF2, hThetaTau2, pdap2, azPdap2, hThetaFS2, hThetaTauS2] = ...
    beamforming3D(newS21, newFreqs, newData.measPos, ...
                  angles, el, az, specificAngles);

azPdap_plot2 = squeeze(azPdap2(:,:)./max(max(abs(azPdap2(:,:)))));

plotAzPap(delayTimes*1E9, azPdap_plot2(:,1:timeCutoffIndex), azS*180.0/pi, '')

plotAnglePdp(delayTimes*1E9, hThetaTauS2(:,1:timeCutoffIndex))

plotFishPlot(pdap2, p, t, turn, 'New Data w/ Beamforming')

hThetaFr2 = reshape(hThetaF2, length(elVals) ,length(azVals), 21);
figure
contourf(azVals, elVals, abs(hThetaFr2(:,:,1)).^2)
figure
contourf(azVals, elVals, abs(hThetaFr2(:,:,end)).^2)
