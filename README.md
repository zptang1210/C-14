# C-14

This repository is the source code for **C-14: Assured Timestamps for Drone Videos**. C-14 is a system for instructing a drone to take videos in a particular pattern that helps establish the earliest time the video could have been created.



## Environment Configuration

1. Clone the source code to your device.
2. Create four folders named *videos*, *output*, *extracted*, and *batchInfo* in *PWCNET_ORIEXTRACTOR*. In the newly added *output* folder, create an empty folder named *metadata*.

3. Create a cuda environment with the packages listed in *balabal.yml*.
4. You may need to recompile all the MATLAB code. Refer to the *README.md* in *cameraMotionCompiler* for details.

5. You may need to recompile *flow-code* in *PWCNET_ORIEXTRACTOR*. Refer to *README.txt* in that folder for details.



## Structure

| Folder Name           | Function                                              |
| --------------------- | ----------------------------------------------------- |
| PWCNET_ORIEXTRACTOR   | The module for computing PWC-NET and cameraMotion.    |
| cameraMotionCompiller | All source code of cameraMotion                       |
| utils                 | Utilities for the verifier                            |
| verifier              | The code for the verifier                             |
| videoProcessing       | Utilities for compressing the videos                  |
| experiments           | Code for testing the verifier and plotting the figure |
| docs                  | Documents for explaining the details of the project   |



## Acknowledgement

This project uses the pytorch implementation of PWC-NET from https://github.com/sniklaus/pytorch-pwc.