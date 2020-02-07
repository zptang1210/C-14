# How to compile?

1. Create a folder named *compiled*

2. ./compile.sh

   

# How to use

1. After getting the compiled folder.
2. Make three empty folders, named *batchInfo*, *extracted* and *output*.
3. Put optical flow files into ./extracted/0179/, where 0179 is a folder storing optical flows for a certain video, e.g. DJI_0179.MP4.
4. Create a text file recording all the camera motion needed to compute (see the format below) and put it into *batchInfo* folder.



For example:

./run_extractOrientation.sh MATLAB_RUNTIME_PATH batchInfoFile.txt 2160 3840 0.82



matlab -r "extractOrientation('batchInfoFile.txt', '2160', '3840', '0.82')"



## Batch Information Format

The first line is the number of batches *n*. In the following *n* lines, each line is "frameStart, frameEnd, outputName".

For example:

3
29,29,DJI_0404\_\__reduce_15\_\_compressed_4_29_29
30,30,DJI_0404\_\_reduce_15\_\_compressed_4_30_30
31,31,DJI_0404\_\_reduce_15\_\_compressed_4_31_31