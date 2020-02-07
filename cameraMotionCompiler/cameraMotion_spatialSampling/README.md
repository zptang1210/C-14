# How to compile?

1. Create a folder named *compiled*

2. ./compile.sh



# How to use

1. After getting the compiled folder.
2. Make two empty folders, named *extracted* and *output*
3. Put optical flow files into ./extracted/0179/, where 0179 is a folder storing optical flows for a certain video, e.g. DJI_0179.MP4.
4. Use the folder name 0179 as the first argument in the command. The following four arguments are startFrame, endFrame, height, width, focallength parameter respectively.



For example:

./run_extractOrientation.sh /cm/shared/apps/MATLAB/MATLAB_Runtime/v901 0179 0 3 2160 3840 7 0.82



matlab -r "extractOrientation('hotpoint_1', '0', '3', '720', '1280', '7', '0.7895')"