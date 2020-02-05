#!/bin/bash
#SBATCH --job-name=compress
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --partition=titanx-long
#SBATCH --mem-per-cpu=8192


module add cuda90
source activate drone
export CUDA_VISIBLE_DEVICES=0,1,2,3

python compressVideos.py

