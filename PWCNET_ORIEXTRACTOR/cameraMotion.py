import os

MATLAB_RUNTIME_PATH = '/cm/shared/apps/MATLAB/MATLAB_Runtime/v901'   # Gypsum


def cameraMotion_focallen(outputName, startFrame, endFrame, height, width, focallen_param=0.82):
    command_ori = './cameraMotion_focallen/run_extractOrientation.sh' + ' ' +\
        MATLAB_RUNTIME_PATH + ' ' +\
        outputName + ' ' + str(startFrame) + ' ' + str(endFrame) + ' ' +\
        str(height) + ' ' + str(width) + ' ' + str(focallen_param)   
    # print(command_ori)
    os.system(command_ori)


def cameraMotion_spatialSampling(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param=0.82):
    command_ori = './cameraMotion_spatialSampling/run_extractOrientation.sh' + ' ' +\
        MATLAB_RUNTIME_PATH + ' ' +\
        outputName + ' ' + str(startFrame) + ' ' + str(endFrame) + ' ' +\
        str(height) + ' ' + str(width) + ' ' + str(spatialSamplingRate) + ' ' + str(focallen_param)
    # print(command_ori)
    os.system(command_ori)


def cameraMotion_batch(samplingList, height, width):
    tempArgumentsFile = 'temp_arguments_for_camera_motion.txt'
    with open(tempArgumentsFile, 'w') as fout:
        fout.write('%d\n' % len(samplingList))
        for sample in samplingList:
            startFrame, endFrame, outputName = sample
            fout.write('%d,%d,%s\n' % (startFrame, endFrame, outputName))

    command_ori = './cameraMotion_batch/run_extractOrientation.sh' + ' ' +\
        MATLAB_RUNTIME_PATH + ' ' +\
        tempArgumentsFile + ' ' + str(height) + ' ' + str(width)
    # print(command_ori)
    os.system(command_ori)

    os.system('rm ' + tempArgumentsFile)