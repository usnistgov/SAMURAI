
%{
%% Test code
text_snp_path = './test/test.s2p';
bin_snp_path  = './test/test.s2p_binary';
text_wnp_path = './test/test.w2p';
bin_wnp_path  = './test/test.w2p_binary';
meas_path     = './test/test.meas';

text_snp = read_touchstone(text_snp_path);
bin_snp = read_touchstone(bin_snp_path);
text_wnp = read_touchstone(text_wnp_path);
bin_wnp = read_touchstone(bin_wnp_path);
meas = read_touchstone(meas_path);
%}

function [ touchstone_data ] = read_touchstone(file_path)
    %@brief Read a touchstone file (\*.snp,\*.wnp,\*.meas)
    %@param[in] file_path - path to the file to load
    %@return Table with the S or wave parameters
    [~,~,ext] = fileparts(file_path); %get the file parts
    if strcmp(ext,'.meas') %the get the nominal path and new extension
        file_path = get_nominal_path_from_meas(file_path);
        [~,~,ext] = fileparts(file_path);
    end
    %get info about our measurement from the extension
    file_info = get_info_from_filepath(file_path);
    %now lets load our raw data
    if endsWith(file_path,'binary')
        raw_data = read_touchstone_binary(file_path);
    else %otherwise assume its a text file
        raw_data = read_touchstone_text(file_path);
    end
    freqs = raw_data(:,1);
    touchstone_data = array2table(freqs,'VariableNames',{'frequency'});
    % now lets split up the wave data
    complex_data = raw_data(:,2:2:end)+1i*raw_data(:,3:2:end); %remove the freqs and make complex
    data_list = {};
    for w=1:file_info.num_waves %split the wave data (e.g. into A,B)
        data_list{end+1} = complex_data(:,w:file_info.num_waves:end);
    end
    for w=1:file_info.num_waves
        complex_data = data_list{w};
        %lets now generate the names of the parameters
        param_names = cell(1,file_info.num_ports.^2);
        for i=1:file_info.num_ports
            for j=1:file_info.num_ports
                param_names{i+2*(j-1)} = num2str(i+(j*10));
            end
        end
        if file_info.num_ports==2 %specific case for 2 ports
            temp = param_names{2}; param_names{2} = param_names{3}; param_names{3} = temp;
        end
        %now add a letter to make a valid varname
        param_names = strcat(file_info.waves(w),param_names);
        data_table = array2table(complex_data,'VariableNames',param_names);
        touchstone_data = [touchstone_data,data_table];
    end
end


%% Functions for reading in the data
function [ nominal_path ] = get_nominal_path_from_meas(file_name)
    %@brief Get the nominal path from a \*.meas file
    %@param[in] file_name - path to \*.meas file
    %@return String of nominal path location
    dom = xmlread(file_name);
    cm = dom.getElementsByTagName('CorrectedMeasurement').item(0);
    cont = cm.getElementsByTagName('Controls').item(0);
    msp = cont.getElementsByTagName('MeasSParams').item(0);
    si = msp.getElementsByTagName('SubItem').item(1);
    nominal_path = char(si.getAttribute('Text')); %loads as java string. Doesnt play super nice with matlab
end

function [ raw_data ] = read_touchstone_text(file_name)
    %@brief read a text touchstone file format (e.g. s2p)
    %@author ajw
    %@param[in] file_name - path to file to load
    %@return A 2D matrix of floating point numbers as they would be in an
    %   ascii snp file (e.g. columns are (freqs,S11 real, S11, imag,...)
    %@note this currently will not work for s4p files as their data is
    %split across lines
    %open and skip past the comments
    fp = fopen(file_name);
    cur_byte = ftell(fp);
    cur_line = fgetl(fp);
    start_char = cur_line(1);
    com_line_count=0;
    while(start_char=='#'||start_char=='!'||isempty(strip(cur_line)))
        com_line_count=com_line_count+1;
        cur_byte = ftell(fp);
        comments{com_line_count} = cur_line;
        cur_line = fgetl(fp);
        start_char = cur_line(1);
    end
    %now lets calculate the number of columns well have
    info = get_info_from_filepath(file_name);
    num_cols = 1+(info.num_ports.^2).*2; %all parameters (real and imag) plus freqeuncy column
    if strcmp(info.type,'wnp') %then we have double the parameters
        num_cols = num_cols + (num_cols-1);
    end
    % and then lets load in the data
    fseek(fp,cur_byte,'bof');
    raw_data = textscan(fp,[repmat('%f',1,num_cols),'\r\n'],'Delimiter',' ','CollectOutput',1);
    raw_data = raw_data{1};
    fclose(fp);
end
    
function [ raw_data ] = read_touchstone_binary(file_name)
    %@brief Read a binary touchstone file format (same as in NIST Microwave uncertainty framework)
    %@author bfj
    %@param[in] file_name - path to the file to load
    %@return A 2D matrix of floating point numbers as they would be in an
    %   ascii snp file (e.g. columns are (freqs,S11 real, S11, imag,...)
    % read in size of array
    fid=fopen(file_name,'r');
    A=fread(fid,[1,2],'int32');
    nrows=A(1);
    ncols=A(2);
    % now read in the array itself and close the file 
    [B,count]=fread(fid,'float64');
    fclose(fid);

    % data is stored as a vector and needs to be parsed out into the array
    for n=1:ncols
        c=[n:ncols:(nrows)*ncols];
        raw_data(:,n)=B(c);
    end

end

function [info_struct] = get_info_from_filepath(file_path)
    %@brief get some useful info from the filepath. This includes the type
    %('snp' or 'wnp') and the num_ports
    %@param[in] file_path - path of the file to get info from
    %@return structure with fields 'type' (either 'snp' or 'wnp'),
    %num_waves (1 for 'snp' 2 for 'wnp'), and num_ports (e.g. 's2p' has 2)
    info_struct = struct();
    [~,~,ext] = fileparts(file_path);
    if length(regexp(ext,'s\d+p')) %then its s parameter
        info_struct.type='snp';
        info_struct.num_waves = 1;
        info_struct.waves = ['S'];
    elseif length(regexp(ext,'w\d+p')) % the its a wave parameter
        info_struct.type='wnp';
        info_struct.num_waves = 2;
        info_struct.waves = ['A','B'];
    end
    % Now lets get the number of ports
    port_num_idx = regexp(ext,'\d');
    info_struct.num_ports = str2double(ext(port_num_idx));
end
        
        

