%% DEPRECATED USE MetafileController.m


classdef SamuraiMetafile < handle
    %@brief This is a class to handle some functionality
    %   of the metafiles (\*.json files) from the SAMURAI system using MATLAB
    %@param[in] metafile_path - on constructor a metafile path
    %   can be passed in to immediatly load
    %@note Any string value should probably be case as char(val) to prevent
    %   returning a string(). 
    %@example
    %    % Add the path to this class
    %    addpath('<class_directory'>)
    %
    %    % Read the file
    %    mymetafile = SamuraiMetafile('path/to/metafile.json')
    %
    %    % Get measurement filenames
    %    filenames = mymetafile.get_meas_path_list()
    %
    %@return An object of type SamuraiMetafile to extract data from the metafile.
    %
    %@note --- DEPRECATED --- This file has been deprecated. Please use
    % MetafileController.m 
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
            %@return An cell array of character arrays with the file names
            num_meas = obj.get_num_meas();
            meas_path_list = cell(1,num_meas);
            for i=1:num_meas
                meas_path_list{i} = char(strip(obj.json_data.measurements(i).filename));
            end
        end
        
        function meas_abs_path_list = get_meas_abs_path_list(obj)
            %@brief Get a list of absolute paths of each measurement
            %@note This uses the self.get_working_directory() as the
            %   base directory to append relative directories to
            %@note This only works if the working directory is absolute
            %@return cell array of character arrays with each path.
            rel_paths = obj.get_meas_path_list();
            wdir = obj.get_working_directory();
            meas_abs_path_list = cell(size(rel_paths));
            %now return list of absolute paths (inlcuding working
            %directory)
            for i=1:length(rel_paths)
                meas_abs_path_list{i} = fullfile(wdir,char(rel_paths{i}));
            end
        end
        
        function wdir = get_working_directory(obj)
            %@brief Get the working directory as specified
            %   in the metafile
            %@return Character array of the working directory
            wdir = char(obj.json_data.working_directory);
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
        
        function ext_pos = get_external_positions(obj,label,meas_num)
            %@brief Get an external position from a given measurement
            %@param[in] label - marker label to get
            %@param[in] meas_num - number of measurement to get position
            %@return Structure containing the data from 'label'
            ext_pos = obj.json_data.measurements(meas_num).external_position_measurements.(label);
        end
        function ext_pos_labels = get_external_position_labels(obj)
            %@brief Get a list of labels from the first measurement
            %@return CellArray of character arrays with labels
            meas_num = 1;
            ext_pos_struct = obj.json_data.measurements(meas_num).external_position_measurements; 
            ext_pos_labels = fieldnames(ext_pos_struct);
        end
   end
end

%{

%% Information on extracting positions from optitrack system
fpath = '\\cfs2w\67_ctl\67Internal\DivisionProjects\Channel Model Uncertainty\Measurements\Synthetic_Aperture\calibrated\2020\2-5-2020\aperture_vertical\metafile.json';
mysm = SamuraiMetafile(fpath); %load the metafile
mylabels = mysm.get_external_position_labels();
%for rigid body
ext_pos_meca = mysm.get_external_positions('meca_head',1) %get the 'meca_head' rigid body
ext_pos_meca.position.mean %mean of x,y,z positions
ext_pos_meca.rotation.mean %mean of alpha,beta,gamma rotations
%for rigid body markers
ext_pos_cyl = mysm.get_external_positions('cylinders_markers',1)
ext_pos_cyl.data(1).position.mean %mean of 1st marker in rigid body
%}



