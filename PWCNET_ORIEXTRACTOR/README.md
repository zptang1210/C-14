# PWCNET_ORIEXTRACTOR

This is a combination of PWC-NET and CameraMotion. PWC-NET is used to convert drone videos to optical flows, and CameraMotion is used to extract the translation and pose of the drone motion.

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

* PWCNET_ORIEXTRACTOR.py

  This script will call PWC_NET.py and cameraMotion to extract optical flow from the specified video in the *videos* folder, and output the motion of drone in the *output* folder.

  **USAGE:**

  * ```PWCNET_ORIEXTRACTOR(videoName, frameStart, frameEnd, height, width, outputName)```
  * videoName is the name of the video in the *videos* folder, e.g. 'DJI_0179' *(without .MP4)*
    
  * [frameStart, frameEnd] is the interval of frames that will be computed
  * height and width are the resolution of the video
  * outputName is the name of folder/file that the optical flow files and drone motion store, e.g. 'DJI_0179_50_100'.
  * ```python ./PWCNET_ORIEXTRACTOR.py  DJI_0179_patch_74_reduced_4  [50]  [100]  [DJI_0179_patch_74_reduced_4_50_100] ```
  
* PWCNET_ORIEXTRACTOR_BATCH.py

  This is a batch version of PWCNET_ORIEXTRACTOR.py. The difference is that it can process several intervals of frames at one time.

  **USAGE**

  * ```PWCNET_ORIEXTRACTOR_BATCH('DJI_0179_patch_74_reduced_4', [(100, 150, '100_150'), (200, 250, '200_250')], 74, 74)```

    *Notice* 

    * The second argument is a list including several tuples of frame intervals. The format of the tuple (frameStart, frameEnd, outputName)
* The third and fourth arguments are the height and width of the video, respectively.
  
* PWCNET_ORIEXTRACTOR_FOCALLEN.py

  This script will also call PWC_NET.py and cameraMotion to extract optical flow from the specified video in the *videos* folder, and output the motion of drone in the *output* folder. The difference from PWCNET_ORIEXTRACTOR is that we can specify the focal length parameter here.

  **USAGE:**

  - ```PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, frameStart, frameEnd, height, width, focallen_param, outputName)```
  - videoName is the name of the video in the *videos* folder, e.g. 'DJI_0179' *(without .MP4)*
  - [frameStart, frameEnd] is the interval of frames that will be computed
  - height and width are the resolution of the video
  - Focallen_param is a float value which specify the ratio of focal length to sensor size in the camera
  - outputName is the name of folder/file that the optical flow files and drone motion store, e.g. 'DJI_0179_50_100'.
  - ```python ./PWCNET_ORIEXTRACTOR_FOCALLEN.py  DJI_0179_patch_74_reduced_4  [50] [100] [0.82] [DJI_0179_patch_74_reduced_4_50_100] ```

## Folder Description

| Folder name        | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| videos             | Put the videos ready for computing into this folder          |
| output             | output of cameraMotion is placed into this folder            |
| cameraMotion       | compiled cameraMotion MATLAB program for PWCNET_ORIEXTRACTOR.py |
| cameraMotion_batch | compiled cameraMotion MATLAB program for PWCNET_ORIEXTRACTOR_BATCH.py |

## How to use

1. Put the video into the *videos* folder
2. Use this command to load the program on Gypsum
   sbatch -p titanx-long --gres=gpu:2 main.sh

## Acknowledgement

* PWC-NET is  a result from the following paper:

  [1]  @inproceedings{Sun_CVPR_2018,
           author = {Deqing Sun and Xiaodong Yang and Ming-Yu Liu and Jan Kautz},
           title = {{PWC-Net}: {CNNs} for Optical Flow Using Pyramid, Warping, and Cost Volume},
           booktitle = {IEEE Conference on Computer Vision and Pattern Recognition},
           year = {2018}
       }

* We use the implementation of PWC-NET from this github repository: https://github.com/sniklaus/pytorch-pwc

* cameraMotion is designed by Dr. Pia Bideau (https://people.cs.umass.edu/~pbideau/)
