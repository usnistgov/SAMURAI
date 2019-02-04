classdef SamuraiMetafile < handle
    %SAMURAIMETAFILE Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        %Just store all of the json files. Getters will decode
        json_data; %direct data structure from json
    end
    
    methods
        function obj = SamuraiMetafile(varargin)
            if(nargin == 0)
                obj.json_data = 'No data loaded';
            else
                obj.load(varargin{1});
            end
        end
        function load(obj,fpath)
            %first load in the JSON file
            %% first import our json metadata file
            metaPath = fpath;
            %now load in
            mfid = fopen(metaPath);
            raw  = fread(mfid);
            fclose(mfid);
            str  = char(raw');
            metaStruct = jsondecode(str);
            %now unpack
            obj.json_data = metaStruct;
            
            %and unpack our measurements
        end
        function num_meas = get_num_meas(obj)
            %num_meas = obj.json_data.total_measurements;
            num_meas = obj.json_data.total_measurements;
        end
        function meas_path_list = get_meas_path_list(obj)
            num_meas = obj.get_num_meas();
            meas_path_list = strings(1,num_meas);
            for i=1:num_meas
                meas_path_list(i) = strip(obj.json_data.measurements(i).filename);
            end
        end
            %get absolute path
        function meas_abs_path_list = get_meas_abs_path_list(obj)
            rel_paths = obj.get_meas_path_list();
            wdir = obj.get_working_directory();
            meas_abs_path_list = strings(size(rel_paths));
            %now return list of absolute paths (inlcuding working
            %directory)
            for i=1:length(rel_paths)
                meas_abs_path_list(i) = fullfile(wdir,char(rel_paths(i)));
            end
        end
        function wdir = get_working_directory(obj)
            wdir = obj.json_data.working_directory;
        end
        %get location list
        function loc_list = get_location_list(obj)
            num_meas = obj.get_num_meas();
            num_pos  = length(obj.json_data.measurements(1).position);
            loc_list = zeros(num_meas,num_pos);
            for i=1:num_meas
                loc_list(i,:) = reshape(obj.json_data.measurements(i).position,1,[]);
            end
        end
    end
end

