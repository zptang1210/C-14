#! /bin/bash

export PATH=/local_scratch/pbideau/install/matlab2016b/bin:$PATH 
mcc -mv run_estimateCameraRotation_davis.m \
    -a /local_scratch/pbideau/data/Sintel/sdk/matlab \
    -a /local_scratch/pbideau/data/Sintel/flow_code \
    -d /local_scratch/pbideau/compiled_swarm \
    -o estimateCameraMotion_swarm
