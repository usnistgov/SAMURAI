%first make sure SamuraiMetafile directory is in our path
addpath("./path/to/SamuraiMetafile/directory/");

%set our metafile path
metafile_path = "./path/to/metafile.json";

%load the metafile into our class
my_metafile = SamuraiMetafile(metafile_path);

%get our relative file paths
rel_paths = my_metafile.get_meas_path_list();

%get our absolute file paths
abs_paths = abs_paths = my_metafile.get_meas_abs_path_list();

%get the pose (position/rotation) of the robot for each file
positions = my_metafile.get_location_list();

%print the first file and its corresponding position
fprintf('FILE: \n    %s\n',abs_paths(1));
fprintf(['POSITION: \n',...
         '   x=%f, y=%5.3f, z=%5.3f\n',...
         'ROTATION: \n',...
         '   alpha=%5.3f, beta=%5.3f, gamma=%5.3f\n'],...
         positions(1,:)); 
