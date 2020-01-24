function [hThetaF, hThetaTau, pdap, azPdap, ...
    hThetaFS, hThetaTauS] = beamforming3D(s21, freqs, coords, ...
                                          angleGrid, el, az, specificAngles)


hThetaF = steeringVectors(coords, angleGrid, freqs, s21);

filtData = applywindow(hThetaF,@hamming,2);
hThetaTau = ifft(ifftshift(filtData,2),[],2);

pdap = abs(hThetaTau).^2;

numFreqs = length(freqs);

% Now calculate azimuthal pdap
pdap = reshape(pdap, size(el,1), size(el,2), numFreqs);
hThetaTau = reshape(hThetaTau, size(el,1), size(el,2), numFreqs);
azPdap = zeros(size(az,2), numFreqs);
for iT = 1:size(pdap,3)
    azPdap(:,iT) = sum((abs(hThetaTau(:,:,iT)).^2).*cos(el),1);
end


hThetaFS = steeringVectors(coords, specificAngles, freqs, s21); 

filtDataS = applywindow(hThetaFS,@hamming,2);
hThetaTauS = ifft(ifftshift(filtDataS,2),[],2);


end