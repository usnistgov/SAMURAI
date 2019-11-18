
addpath(genpath('C:\Users\bfj\Projects\ChannelModeling\maria\MATLAB_CODE_REPOSITORY\CURRENT\'))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load the data from the debug.mat file
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
origData = load('C:\Users\bfj\Code\channelData\TestPostProcessor\debugMatlab\debug.mat');
newData = load('jonesReverb.mat');    
% Down sample frequency
fBegin = 1;
fStep = 200;
newS21 = complex(newData.measS21(:,fBegin:fStep:end,4) + 1i*newData.measS21(:,fBegin:fStep:end,5));
newFreqs = newData.freqs(fBegin:fStep:end)';
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
% 
% % Calculate the mask
% mask = atan2(origData.coords(:,2), origData.coords(:,1))*180./pi > -155.0;
% % appy mask
% s21 = origData.s21(mask,:);
% coords = origData.coords(mask,:);
% 
% % % Calculation
% [pap1, pdap1, azimuthVals1, elevationVals1, pdapAngles1, delayTimes1, kx, ky, kz] = ...
%     process3dSyntheticAperture(origData.s21, origData.coords, ...
%         origData.freqs, origData.deltaElAngle, origData.deltaAzAngle, ...
%         origData.angles, origData.timeCutoff, origData.dkResFactor, ...
%         origData.kPadFactor);
% 
% plotFishPlot(pdap1, p, t, turn, 'Prev. Data w/ FFT')
% 
% plotAnglePdp(delayTimes*1E9, pdapAngles1(:,1:timeCutoffIndex))
% 
% azPdap = calcAzPdap(pdap1, el, numFreqs);
% 
% plotAzPap(delayTimes*1E9, azPdap(:,1:timeCutoffIndex), azS*180.0/pi, '')
%     
%  
% [pap1, pdap1, azimuthVals1, elevationVals1, pdapAngles1, delayTimes1, kx, ky, kz] = ...
%     process3dSyntheticAperture(s21, coords, ...
%         origData.freqs, origData.deltaElAngle, origData.deltaAzAngle, ...
%         origData.angles, origData.timeCutoff, origData.dkResFactor, ...
%         origData.kPadFactor);
%     
%     
% plotFishPlot(pdap1, p, t, turn, 'Prev. Data w/ FFT')
% 
% plotAnglePdp(delayTimes*1E9, pdapAngles1(:,1:timeCutoffIndex))
% 
% azPdap = calcAzPdap(pdap1, el, numFreqs);
% 
% plotAzPap(delayTimes*1E9, azPdap(:,1:timeCutoffIndex), azS*180.0/pi, '')
% 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Now Beamforming
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

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Orig. Data
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% [hThetaF1, hThetaTau1, pdap1, azPdap1, hThetaFS1, hThetaTauS1] = ...
%     beamforming3D(s21, origData.freqs, coords, ...
%                   angles, el, az, specificAngles);
% 
% azPdap_plot1 = squeeze(azPdap1(:,:)./max(max(abs(azPdap1(:,:)))));
% 
% plotAzPap(delayTimes*1E9, azPdap_plot1(:,1:timeCutoffIndex), azS*180.0/pi, '')
% 
% plotAnglePdp(delayTimes*1E9, hThetaTauS1(:,1:timeCutoffIndex))
% 
% plotFishPlot(pdap1, p, t, turn, 'Prev. Data w/ Beamforming')

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% New Data
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 
% fBegin = 1;
% fStep = 200;
% newS21 = complex(newData.measS21(:,fBegin:fStep:end,4) + 1i*newData.measS21(:,fBegin:fStep:end,5));
% newFreqs = newData.freqs(fBegin:fStep:end)';
% newFreqs = newFreqs/(10^9);
% [pap2, pdap2, azimuthVals2, elevationVals2, pdapAngles2, delayTimes2, kx, ky, kz] = ...
%    process3dSyntheticAperture(newS21, newData.measPos, ...
%        newFreqs, origData.deltaElAngle, origData.deltaAzAngle, ...
%        origData.angles, origData.timeCutoff, origData.dkResFactor, ...
%        origData.kPadFactor);
% 
%    
% plotFishPlot(pdap2, p, t, turn, 'New Data w/ FFT')
% 
% plotAnglePdp(delayTimes*1E9, pdapAngles2(:,1:timeCutoffIndex))
% 
% azPdap2 = calcAzPdap(pdap2, el, numFreqs);
% 
% plotAzPap(delayTimes*1E9, azPdap2(:,1:timeCutoffIndex), azS*180.0/pi, '')
% 
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % Now Beamforming
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% numAngles = 2;
% specificAngles = zeros(numAngles,2);
% 
% specificAngles(1,1) = -20;
% specificAngles(1,2) = 90.8; %72.8 - turnd;
% specificAngles(2,1) = -10.0;
% specificAngles(2,2) = 171.1; %153.1 - turnd;
% specificAngles = specificAngles*pi/180.0;
% 
% 
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % Orig. Data
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% [hThetaF1, hThetaTau1, pdap1, azPdap1, hThetaFS1, hThetaTauS1] = ...
%     beamforming3D(origData.s21, origData.freqs, origData.coords, ...
%                   angles, el, az, specificAngles);
% 
% 
% 
% azPdap_plot1 = squeeze(azPdap1(:,:)./max(max(abs(azPdap1(:,:)))));
% 
% plotAzPap(delayTimes*1E9, azPdap_plot1(:,1:timeCutoffIndex), azS*180.0/pi, '')
% 
% plotAnglePdp(delayTimes*1E9, hThetaTauS1(:,1:timeCutoffIndex))
% 
% plotFishPlot(pdap1, p, t, turn, 'Prev. Data w/ Beamforming')


[hThetaF2, hThetaTau2, pdap2, azPdap2, hThetaFS2, hThetaTauS2] = ...
    beamforming3D(newS21, newFreqs, newData.measPos, ...
                  angles, el, az, specificAngles);

azPdap_plot2 = squeeze(azPdap2(:,:)./max(max(abs(azPdap2(:,:)))));

plotAzPap(delayTimes*1E9, azPdap_plot2(:,1:timeCutoffIndex), azS*180.0/pi, '')

plotAnglePdp(delayTimes*1E9, hThetaTauS2(:,1:timeCutoffIndex))

plotFishPlot(pdap2, p, t, turn, 'New Data w/ Beamforming')
% 
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % With new angles
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% numAngles = 2;
% specificAngles = zeros(numAngles,2);
% % Indices from plot...
% specificAngles(1,1) = el(20,28);
% specificAngles(1,2) = az(20,28) + turn;
% specificAngles(2,1) = el(21,41);
% specificAngles(2,2) = az(21,41) + turn;
% %specificAngles = specificAngles*pi/180.0;
% 
% [hThetaF2, hThetaTau2, pdap2, azPdap2, hThetaFS2, hThetaTauS2] = ...
%     beamforming3D(newS21, newFreqs, newData.measPos, ...
%                   angles, el, az, specificAngles);
% 
% azPdap_plot2 = squeeze(azPdap2(:,:)./max(max(abs(azPdap2(:,:)))));
% 
% plotAzPap(delayTimes*1E9, azPdap_plot2(:,1:timeCutoffIndex), azS*180.0/pi, '')
% 
% plotAnglePdp(delayTimes*1E9, hThetaTauS2(:,1:timeCutoffIndex))
% 
% plotFishPlot(pdap2, p, t, turn, 'New Data w/ Beamforming', specificAngles*180.0/pi)
% 
% 
% return
%    