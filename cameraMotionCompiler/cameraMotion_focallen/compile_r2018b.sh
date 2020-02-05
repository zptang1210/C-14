#!/bin/bash

export PATH=/cm/shared/apps/MATLAB/r2018b/bin:$PATH
mcc -mv ./extractOrientation.m \
    -a ./cam-motion/ \
    -d ./compiled \
    -o extractOrientation