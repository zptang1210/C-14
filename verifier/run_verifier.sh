#! /bin/bash

#SBATCH --job-name=droneCAPTCHA_verifier
#SBATCH --nodes=1
#SBATCH --gres=gpu:8
#SBATCH --ntasks=24
#SBATCH --partition=1080ti-short
#SBATCH --mem-per-cpu=8192

module add cuda90
source activate drone

python ./verifier.py
