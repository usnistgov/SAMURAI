function [ Barray ] = Read_MUF_Binary( FileName )
    %@brief Read a binary s2p file format (same as in NIST Microwave uncertainty framework)
    %@author bfj
    %@param[in] FileName - path to the file to load
    %@return A 2D matrix of floating point values where the first column should be the frequencies and the following
    %   columns will be the S parameters Real/Imaginary values just like how they are laid out in the ASCII file format.
    
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
    