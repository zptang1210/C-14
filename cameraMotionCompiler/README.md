# cameraMotionCompiler

This folder has the source code of various versions of cameraMotion. To use cameraMotion, you need to compile the MATLAB code and copy the compiled program to *PWCNET_ORIEXTRACTOR*.



## How to use?

There are three versions of cameraMotion in total. The compilation steps are similar. We use cameraMotion_focallen as an example. The steps are:

1. Go to *cameraMotion_focallen* folder
2. Create a folder named *compiled*
3. ./compile.sh

Notice: You may need to change the PATH argument in *compile.sh* to the MATLAB runtime library path in your computer.

After compilation, you need to copy *compiled* folder to PWCNET_ORIEXTRACTOR, and change the folder to its corresponding name, say *cameraMotion_focallen*.