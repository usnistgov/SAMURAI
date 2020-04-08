function [ Barray ] = read_snp_binary( FileName )
    %@brief Read a binary snp file format (same as in NIST Microwave uncertainty framework)
    %@author bfj
    %@param[in] FileName - path to the file to load
    %@return A 2D matrix of floating point numbers as they would be in an
    %   ascii snp file (e.g. columns are (freqs,S11 real, S11, imag,...)
        %% read in size of array
        fid=fopen(FileName,'r');
        A=fread(fid,[1,2],'int32');
        nrows=A(1);
        ncols=A(2);
        %% now read in the array itself and close the file 
        [B,count]=fread(fid,'float64');
        fclose(fid);
    
        %% data is stored as a vector and needs to be parsed out into the array
        for n=1:ncols
            c=[n:ncols:(nrows)*ncols];
            Barray(:,n)=B(c);
        end
    
    end

%{
file_path = 'path/to/my/measurement.s2p_binary'
meas_data = read_snp_binary(file_path)
freqs = meas_data(:,1)
s11_vals = meas_data(:,2)+1i*meas_data(:,3)
%}  