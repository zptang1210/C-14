#!/bin/bash
#SBATCH --job-name=skip_cameramotion
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --ntasks=2
#SBATCH --partition=titanx-long

module add cuda90
source activate drone
export CUDA_VISIBLE_DEVICES=0,1,2,3

python dataGenerator.py

