#!/bin/bash
module add cuda90
source activate drone
export CUDA_VISIBLE_DEVICES=0,1,2,3

python ./PWCNET_ORIEXTRACTOR_FOCALLEN.py DJI_0411

