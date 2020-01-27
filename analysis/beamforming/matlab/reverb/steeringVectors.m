function [ hThetaF ] = steeringVectors( coords, angles, freqsInHz, s21data)

% coords assumed to have centroid 0
numFreqs = length(freqsInHz);
numPoints = size(coords,1);
numAngles = size(angles,1);

speedOfLight = 299792458.0;
lambdaVec = speedOfLight ./ (freqsInHz);
kVec = 2 * pi ./ lambdaVec;

%steeringVectors = zeros(numAngles, numPoints);

dirs = zeros(numAngles,3);
dirs(:,1) = cos(angles(:,1)).*cos(angles(:,2));
dirs(:,2) = cos(angles(:,1)).*sin(angles(:,2));
dirs(:,3) = sin(angles(:,1));

hThetaF = complex(zeros(numAngles, numFreqs));

% Could be much faster...
for iF = 1:numFreqs
    kDir = kVec(iF)*dirs;
    steeringVectors(:, :) = exp(-1j * kDir*coords');
    
    
    for iA = 1:numAngles
        num = reshape(s21data(:,iF), 1, [])*reshape(steeringVectors(iA,:), [], 1);
        denom = sum(conj(reshape(steeringVectors(iA,:), [], 1)).*reshape(steeringVectors(iA,:), [], 1),1);
        hThetaF(iA, iF) = num./sqrt(denom);
    end
    
    % The next line works well...
    %hThetaF(:,iF) = exp(1j*kVec(iF)*dirs*coords')*conj(s21data(:,iF)); %reshape(s21data(:,iF), [], 1)'*conj(reshape(steeringVectors(iA,:), [], 1));
    %denom = sum(abs(steeringVectors).^2,2); %    sum(conj(reshape(steeringVectors(iA,:), [], 1)).*reshape(steeringVectors(iA,:), [], 1),1);
    %hThetaF(:, iF) = num ; num./sqrt(denom);
end

%hThetaF = hThetaF/numPoints;
    
    %for iA = 1:numAngles
        %kDir = kVec(iF);
        %steeringVectors(iF, iA, :) = exp(-1j * coords*kDir');
        
        %for iP = 1:numPoints
        %    %coords(iP,:)
        %    %dir = coords(iP,:);
        %    steeringVectors(iF, iA, iP) = exp(1j * sum(coords(iP,:).*kDir));
        %end
    %end


return
%array_z = repmat( RxZ, Nelem, Nelem );

kx = k * xVals;
ky = k * yVals; 
%kz = k * array_z;

numUvPts = 2/duv + 1;
u1 = linspace(-1,1,numUvPts);
v1 = linspace(-1,1,numUvPts);

[uGrid, vGrid] = meshgrid(u1, v1);
steeringVectors = zeros(numUvPts, numUvPts, numPoints);
mask = ones(numUvPts, numUvPts);

for iU = 1 : numUvPts
    for iV = 1 : numUvPts
        if (uGrid(iV, iU)^2 + vGrid(iV, iU)^2) > 1
            steeringVectors(iV, iU, :) = NaN;
            mask(iV, iU) = 0;
            continue
        end
            
        k_az3 = kx * uGrid( iV, iU );
        k_el3 = ky * vGrid( iV, iU );
        steeringVectors(iV, iU, :) = exp( -1j * ( k_az3( : ) + k_el3( : ) ) );
        
     end
end



