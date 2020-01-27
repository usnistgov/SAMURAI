classdef SamuraiMetafile < handle
    %@brief This is a class to handle some functionality
    %   of the metafiles from the SAMURAI system using MATLAB
    %@param[in] metafile_path - on constructor a metafile path
    %   can be passed in to immediatly load
    
    properties
        %Just store all of the json files. Getters will decode
        json_data; %direct data structure from json
    end
    
    methods
        
        function obj = SamuraiMetafile(varargin)
            %@brief Constructor for the class
            if(nargin == 0)
                obj.json_data = 'No data loaded';
            else
                obj.load(varargin{1});
            end
        end
        
        function load(obj,fpath)
            %@brief Load in the json metafile from a path
            %@param[in] fpath - path to metafile to load
            %@note this is loaded into self.json_data
            metaPath = fpath;
            %now load in
            mfid = fopen(metaPath);
            raw  = fread(mfid);
            fclose(mfid);
            str  = char(raw');
            metaStruct = jsondecode(str);
            %now unpack
            obj.json_data = metaStruct;
        end
        
        function num_meas = get_num_meas(obj)
            %@brief Get the number of measurements in the metafile
            %@return The number of measurements in self.json_data
            %@note this does not count measurements, it uses the
            %   property self.json_data.total_measurements
            num_meas = obj.json_data.total_measurements;
        end
        
        function meas_path_list = get_meas_path_list(obj)
            %@brief Get a list of relative paths to each measurement
            %@note this returns stored relative file paths
            %   from self.json_data.measurements(i).filename
            %@return An array of strings with relative file paths
            num_meas = obj.get_num_meas();
            meas_path_list = strings(1,num_meas);
            for i=1:num_meas
                meas_path_list(i) = strip(obj.json_data.measurements(i).filename);
            end
        end
        
        function meas_abs_path_list = get_meas_abs_path_list(obj)
            %@brief Get a list of absolute paths of each measurement
            %@note This uses the self.get_working_directory() as the
            %   base directory to append relative directories to
            %@return A list of strings with absolute file paths
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
            %@brief Get the working directory as specified
            %   in the metafile
            %@return Character array of the working directory
            wdir = obj.json_data.working_directory;
        end
        
        function loc_list = get_location_list(obj)
            %@brief Get a list of locations from the metafile 
            %   corresponding to each measurement in
            %   self.get_meas_path_list
            %@return Array with x,y,z,alpha,beta,gamma position/rotations
            num_meas = obj.get_num_meas();
            num_pos  = length(obj.json_data.measurements(1).position);
            loc_list = zeros(num_meas,num_pos);
            for i=1:num_meas
                loc_list(i,:) = reshape(obj.json_data.measurements(i).position,1,[]);
            end
        end
    end
end

