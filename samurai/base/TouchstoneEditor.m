
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

function [ touchstone_data ] = TouchstoneEditor(file_path)
    %@brief Read a touchstone file (\*.snp,\*.wnp,\*.meas)
    %@author ajw
    %@param[in] file_path - path to the file to load
    %@example
    %    % Add the path to this function
    %    addpath('<function_directory'>)
    %
    %    % Read the file
    %    mysnp = read_touchstone('path/to/data.s2p')
    %
    %    % Get S21 data
    %    s21_data = mysnp.S21
    %@note This was renamed from samurai/analysis/support/read_touchstone.m
    %@return Table with the S or wave parameters
    [~,~,ext] = fileparts(file_path); %get the file parts
    if strcmp(ext,'.meas') %the get the nominal path and new extension
        [file_dir,~,~] = fileparts(file_path); %for relative values
        file_path = get_nominal_path_from_meas(file_path);
        if ~exist(file_path,'file') %then assume its a relative measurement
            file_path = fullfile(file_dir,file_path);
        end
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
    ext = char(ext);
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


%% Hopefully this will be in future matlab releases...     
%@cite https://www.mathworks.com/matlabcentral/fileexchange/28249-getfullpath
% This is required to utilize relative paths for metafile working
% directories
function File = GetFullPath(File, Style)
    % GetFullPath - Get absolute canonical path of a file or folder
    % Absolute path names are safer than relative paths, when e.g. a GUI or TIMER
    % callback changes the current directory. Only canonical paths without "." and
    % ".." can be recognized uniquely.
    % Long path names (>259 characters) require a magic initial key "\\?\" to be
    % handled by Windows API functions, e.g. for Matlab's FOPEN, DIR and EXIST.
    %
    % FullName = GetFullPath(Name, Style)
    % INPUT:
    %   Name:  String or cell string, absolute or relative name of a file or
    %          folder. The path need not exist. Unicode strings, UNC paths and long
    %          names are supported.
    %   Style: Style of the output as string, optional, default: 'auto'.
    %          'auto': Add '\\?\' or '\\?\UNC\' for long names on demand.
    %          'lean': Magic string is not added.
    %          'fat':  Magic string is added for short names also.
    %          The Style is ignored when not running under Windows.
    %
    % OUTPUT:
    %   FullName: Absolute canonical path name as string or cell string.
    %          For empty strings the current directory is replied.
    %          '\\?\' or '\\?\UNC' is added on demand.
    %
    % NOTE: The M- and the MEX-version create the same results, the faster MEX
    %   function works under Windows only.
    %   Some functions of the Windows-API still do not support long file names.
    %   E.g. the Recycler and the Windows Explorer fail even with the magic '\\?\'
    %   prefix. Some functions of Matlab accept 260 characters (value of MAX_PATH),
    %   some at 259 already. Don't blame me.
    %   The 'fat' style is useful e.g. when Matlab's DIR command is called for a
    %   folder with les than 260 characters, but together with the file name this
    %   limit is exceeded. Then "dir(GetFullPath([folder, '\*.*], 'fat'))" helps.
    %
    % EXAMPLES:
    %   cd(tempdir);                    % Assumed as 'C:\Temp' here
    %   GetFullPath('File.Ext')         % 'C:\Temp\File.Ext'
    %   GetFullPath('..\File.Ext')      % 'C:\File.Ext'
    %   GetFullPath('..\..\File.Ext')   % 'C:\File.Ext'
    %   GetFullPath('.\File.Ext')       % 'C:\Temp\File.Ext'
    %   GetFullPath('*.txt')            % 'C:\Temp\*.txt'
    %   GetFullPath('..')               % 'C:\'
    %   GetFullPath('..\..\..')         % 'C:\'
    %   GetFullPath('Folder\')          % 'C:\Temp\Folder\'
    %   GetFullPath('D:\A\..\B')        % 'D:\B'
    %   GetFullPath('\\Server\Folder\Sub\..\File.ext')
    %                                   % '\\Server\Folder\File.ext'
    %   GetFullPath({'..', 'new'})      % {'C:\', 'C:\Temp\new'}
    %   GetFullPath('.', 'fat')         % '\\?\C:\Temp\File.Ext'
    %
    % COMPILE:
    %   Automatic: InstallMex GetFullPath.c uTest_GetFullPath
    %   Manual:    mex -O GetFullPath.c
    %   Download:  http://www.n-simon.de/mex
    % Run the unit-test uTest_GetFullPath after compiling.
    %
    % Tested: Matlab 2009a, 2015b(32/64), 2016b, 2018b, Win7/10
    %         Compiler: LCC2.4/3.8, BCC5.5, OWC1.8, MSVC2008/2010
    % Assumed Compatibility: higher Matlab versions
    % Author: Jan Simon, Heidelberg, (C) 2009-2019 matlab.2010(a)n(MINUS)simon.de
    %
    % See also: CD, FULLFILE, FILEPARTS.
    % $JRev: R-M V:038 Sum:C/6JMzUYsYsc Date:19-May-2019 17:25:55 $
    % $License: BSD (use/copy/change/redistribute on own risk, mention the author) $
    % $UnitTest: uTest_GetFullPath $
    % $File: Tools\GLFile\GetFullPath.m $
    % History:
    % 001: 20-Apr-2010 22:28, Successor of Rel2AbsPath.
    % 010: 27-Jul-2008 21:59, Consider leading separator in M-version also.
    % 011: 24-Jan-2011 12:11, Cell strings, '~File' under linux.
    %      Check of input types in the M-version.
    % 015: 31-Mar-2011 10:48, BUGFIX: Accept [] as input as in the Mex version.
    %      Thanks to Jiro Doke, who found this bug by running the test function for
    %      the M-version.
    % 020: 18-Oct-2011 00:57, BUGFIX: Linux version created bad results.
    %      Thanks to Daniel.
    % 024: 10-Dec-2011 14:00, Care for long names under Windows in M-version.
    %      Improved the unittest function for Linux. Thanks to Paul Sexton.
    % 025: 09-Aug-2012 14:00, In MEX: Paths starting with "\\" can be non-UNC.
    %      The former version treated "\\?\C:\<longpath>\file" as UNC path and
    %      replied "\\?\UNC\?\C:\<longpath>\file".
    % 032: 12-Jan-2013 21:16, 'auto', 'lean' and 'fat' style.
    % 038: 19-May-2019 17:25, BUGFIX, Thanks HHang Li, "File(7:..." -> "File(8:..."
    % Initialize: ==================================================================
    % Do the work: =================================================================
    % #############################################
    % ### USE THE MUCH FASTER MEX ON WINDOWS!!! ###
    % #############################################
    % Difference between M- and Mex-version:
    % - Mex does not work under MacOS/Unix.
    % - Mex calls Windows API function GetFullPath.
    % - Mex is much faster.
    % Magic prefix for long Windows names:
    if nargin < 2
       Style = 'auto';
    end
    % Handle cell strings:
    % NOTE: It is faster to create a function @cell\GetFullPath.m under Linux, but
    % under Windows this would shadow the fast C-Mex.
    if isa(File, 'cell')
       for iC = 1:numel(File)
          File{iC} = GetFullPath(File{iC}, Style);
       end
       return;
    end
    % Check this once only:
    isWIN    = strncmpi(computer, 'PC', 2);
    MAX_PATH = 260;
    % Warn once per session (disable this under Linux/MacOS):
    persistent hasDataRead
    if isempty(hasDataRead)
       % Test this once only - there is no relation to the existence of DATAREAD!
       %if isWIN
       %   Show a warning, if the slower Matlab version is used - commented, because
       %   this is not a problem and it might be even useful when the MEX-folder is
       %   not inlcuded in the path yet.
       %   warning('JSimon:GetFullPath:NoMex', ...
       %      ['GetFullPath: Using slow Matlab-version instead of fast Mex.', ...
       %       char(10), 'Compile: InstallMex GetFullPath.c']);
       %end

       % DATAREAD is deprecated in 2011b, but still available. In Matlab 6.5, REGEXP
       % does not know the 'split' command, therefore DATAREAD is preferred:
       hasDataRead = ~isempty(which('dataread'));
    end
    if isempty(File)  % Accept empty matrix as input:
       if ischar(File) || isnumeric(File)
          File = cd;
          return;
       else
          error(['JSimon:', mfilename, ':BadTypeInput1'], ...
             '*** %s: Input must be a string or cell string', mfilename);
       end
    end
    if ischar(File) == 0  % Non-empty inputs must be strings
       error(['JSimon:', mfilename, ':BadTypeInput1'], ...
          '*** %s: Input must be a string or cell string', mfilename);
    end
    if isWIN  % Windows: --------------------------------------------------------
       FSep = '\';
       File = strrep(File, '/', FSep);

       % Remove the magic key on demand, it is appended finally again:
       if strncmp(File, '\\?\', 4)
          if strncmpi(File, '\\?\UNC\', 8)
             % [BUGFIX] 19-May-2019, Thanks HHang Li, "File(7:..." -> "File(8:..."
             File = ['\', File(8:length(File))];  % Two leading backslashes!
          else
             File = File(5:length(File));
          end
       end

       isUNC   = strncmp(File, '\\', 2);
       FileLen = length(File);
       if isUNC == 0                        % File is not a UNC path
          % Leading file separator means relative to current drive or base folder:
          ThePath = cd;
          if File(1) == FSep
             if strncmp(ThePath, '\\', 2)   % Current directory is a UNC path
                sepInd  = strfind(ThePath, '\');
                ThePath = ThePath(1:sepInd(4));
             else
                ThePath = ThePath(1:3);     % Drive letter only
             end
          end

          if FileLen < 2 || File(2) ~= ':'  % Does not start with drive letter
             if ThePath(length(ThePath)) ~= FSep
                if File(1) ~= FSep
                   File = [ThePath, FSep, File];
                else                        % File starts with separator:
                   File = [ThePath, File];
                end
             else                           % Current path ends with separator:
                if File(1) ~= FSep
                   File = [ThePath, File];
                else                        % File starts with separator:
                   ThePath(length(ThePath)) = [];
                   File = [ThePath, File];
                end
             end

          elseif FileLen == 2 && File(2) == ':'   % "C:" current directory on C!
             % "C:" is the current directory on the C-disk, even if the current
             % directory is on another disk! This was ignored in Matlab 6.5, but
             % modern versions considers this strange behaviour.
             if strncmpi(ThePath, File, 2)
                File = ThePath;
             else
                try
                   backCD = cd;
                   File   = cd(cd(File));
                   cd(backCD);
                catch ME
                   if exist(File, 'dir')  % No idea what could cause an error then!
                      rethrow(ME);
                   else  % Reply "K:\" for not existing disk:
                      File = [File, FSep];
                   end
                end
             end
          end
       end

    else         % Linux, MacOS: ---------------------------------------------------
       FSep = '/';
       File = strrep(File, '\', FSep);

       if strcmp(File, '~') || strncmp(File, '~/', 2)  % Home directory:
          HomeDir = getenv('HOME');
          if ~isempty(HomeDir)
             File(1) = [];
             File    = [HomeDir, File];
          end

       elseif strncmpi(File, FSep, 1) == 0
          % Append relative path to current folder:
          ThePath = cd;
          if ThePath(length(ThePath)) == FSep
             File = [ThePath, File];
          else
             File = [ThePath, FSep, File];
          end
       end
    end
    % Care for "\." and "\.." - no efficient algorithm, but the fast Mex is
    % recommended at all!
    if ~isempty(strfind(File, [FSep, '.']))
       if isWIN
          if strncmp(File, '\\', 2)  % UNC path
             index = strfind(File, '\');
             if length(index) < 4    % UNC path without separator after the folder:
                return;
             end
             Drive            = File(1:index(4));
             File(1:index(4)) = [];
          else
             Drive     = File(1:3);
             File(1:3) = [];
          end
       else  % Unix, MacOS:
          isUNC   = false;
          Drive   = FSep;
          File(1) = [];
       end

       hasTrailFSep = (File(length(File)) == FSep);
       if hasTrailFSep
          File(length(File)) = [];
       end

       if hasDataRead
          if isWIN  % Need "\\" as separator:
             C = dataread('string', File, '%s', 'delimiter', '\\');  %#ok<REMFF1>
          else
             C = dataread('string', File, '%s', 'delimiter', FSep);  %#ok<REMFF1>
          end
       else  % Use the slower REGEXP, when DATAREAD is not available anymore:
          C = regexp(File, FSep, 'split');
       end

       % Remove '\.\' directly without side effects:
       C(strcmp(C, '.')) = [];

       % Remove '\..' with the parent recursively:
       R = 1:length(C);
       for dd = reshape(find(strcmp(C, '..')), 1, [])
          index    = find(R == dd);
          R(index) = [];
          if index > 1
             R(index - 1) = [];
          end
       end

       if isempty(R)
          File = Drive;
          if isUNC && ~hasTrailFSep
             File(length(File)) = [];
          end

       elseif isWIN
          % If you have CStr2String, use the faster:
          %   File = CStr2String(C(R), FSep, hasTrailFSep);
          File = sprintf('%s\\', C{R});
          if hasTrailFSep
             File = [Drive, File];
          else
             File = [Drive, File(1:length(File) - 1)];
          end

       else  % Unix:
          File = [Drive, sprintf('%s/', C{R})];
          if ~hasTrailFSep
             File(length(File)) = [];
          end
       end
    end
    % "Very" long names under Windows:
    if isWIN
       if ~ischar(Style)
          error(['JSimon:', mfilename, ':BadTypeInput2'], ...
             '*** %s: Input must be a string or cell string', mfilename);
       end

       if (strncmpi(Style, 'a', 1) && length(File) >= MAX_PATH) || ...
             strncmpi(Style, 'f', 1)
          % Do not use [isUNC] here, because this concerns the input, which can
          % '.\File', while the current directory is an UNC path.
          if strncmp(File, '\\', 2)  % UNC path
             File = ['\\?\UNC', File(2:end)];
          else
             File = ['\\?\', File];
          end
       end
    end
    % return;
end
        
        

