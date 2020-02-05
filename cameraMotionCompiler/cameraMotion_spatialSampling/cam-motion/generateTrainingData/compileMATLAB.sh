#! /bin/bash

export PATH=/exp/comm/matlab-R2016a/bin:$PATH 
mcc -mv generateTAFlowFT3D.m \
    -d ./compiled \
    -o convertFlowFT3D_synthetic_unitVec