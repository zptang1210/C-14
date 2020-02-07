# PWCNET_ORIEXTRACTOR

This is a combination of PWC-NET and cameraMotion. PWC-NET is used to convert drone videos to optical flows, and cameraMotion is used to extract the drone motion.



## File Description

* PWC_NET.py

  This script is used to compute optical flow via the PWC-NET algorithm.

  **USAGE:**

  * ```PWC_NET(arguments_strVideo, arguments_strModel, arguments_strOut_path, arguments_strStart_Frame, arguments_strFrame_Num)```

    *Notice:*

    * arguments_strVideo is the path of the video, e.g. ./videos/example.MP4

    * arguments_strStart_Frame and arguments_strFrame_Num are string type, not integer

  * ```Python ./PWC_NET.py  --video ./videos/example.MP4  --out ./extracted/example/```

* cameraMotion.py

  This python script wraps cameraMotion MATLAB program with python functions.

* PWCNET_ORIEXTRACTOR_FOCALLEN.py

  This script will call PWC_NET.py and cameraMotion to extract optical flow from the specified video in the *videos* folder, and output the motion of drone in the *output* folder. We can specify the focal length parameter here.

  **USAGE:**

  - ```PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, frameStart, frameEnd, height, width, focallen_param, outputName)```
  
    *Notice:*
  
    - videoName is the name of the video in the *videos* folder, e.g. 'DJI_0179' *(without .MP4)*. The default folder is *../PWCNET_ORIEXTRACTOR/videos/*
    - [frameStart, frameEnd] is the interval of frames that will be computed
    - height and width are the resolution of the video
    - focallen_param is a float value which specify the ratio of focal length to sensor size in the camera
    - outputName is the name of folder and file with which the optical flow files and drone motion store, For example, if outputName is 'DJI_0179_50_100'. The optical flow files and the camera motion will be stored in *../PWCNET_ORIEXTRACTOR/extracted/DJI_0179_50_100/* and *../PWCNET_ORIEXTRACTOR/output/DJI_0179_50_100.txt*, respectively.
  
  - ```python ./PWCNET_ORIEXTRACTOR_FOCALLEN.py  DJI_0179_patch_74_reduced_4  [50] [100] [0.82] [DJI_0179_patch_74_reduced_4_50_100] ```
  
* PWCNET_ORIEXTRACTOR_FOCALLEN_spatialSampling.py

  This script does the same job as PWCNET_ORIEXTRACTOR_FOCALLEN.py with an additional option for spatial sampling parameter for cameraMotion.

  **USAGE:**

  - ```PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, frameStart, frameEnd, height, width, spatialSamplingRate, focallen_param, outputName)```

    *Notice:*

    - This function can also record the time consumptions for PWC-NET and cameraMotion to *outputName_timing.txt*.

      

## Folder Description

| Folder name     | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| videos          | Put the videos ready for computing into this folder          |
| output          | Output of cameraMotion is placed into this folder            |
| output/metadata | Put the metadata of the videos into this folder              |
| extracted       | Output of PWC-NET is placed into this folder                 |
| cameraMotion*   | Compiled cameraMotion MATLAB program for PWCNET_ORIEXTRACTOR |
| Other folders   | Code related to PWC-NET                                      |



## How to use

Initialization:

1. Create four empty folders named *videos*, *extracted*, *output*, and *output/metadata*

2. Compile flow code according to *flow-code/README.txt*

3. Compile cameraMotion MATLAB code according to *README.md* in *cameraMotionCompiler*, and copy them to corresponding folders

   

Usage:

1. Put the video into the *videos* folder
2. Put the metadata into the *output/metadata* folder
3. python ./PWCNET_ORIEXTRACTOR_FOCALLEN.py videoName



## Acknowledgement

* PWC-NET is  a result from the following paper:

  [1]  @inproceedings{Sun_CVPR_2018,
           author = {Deqing Sun and Xiaodong Yang and Ming-Yu Liu and Jan Kautz},
           title = {{PWC-Net}: {CNNs} for Optical Flow Using Pyramid, Warping, and Cost Volume},
           booktitle = {IEEE Conference on Computer Vision and Pattern Recognition},
           year = {2018}
       }

* We use the implementation of PWC-NET from this github repository: https://github.com/sniklaus/pytorch-pwc

* cameraMotion is coded by Dr. Pia Bideau (https://people.cs.umass.edu/~pbideau/)
