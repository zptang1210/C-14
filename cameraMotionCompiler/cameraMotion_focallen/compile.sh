#!/bin/bash

export PATH=/cm/shared/apps/MATLAB/r2016a/bin:$PATH
mcc -mv ./extractOrientation.m \
    -a ./cam-motion/ \
    -d ./compiled \
    -o extractOrientation