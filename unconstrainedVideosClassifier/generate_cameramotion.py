import os
import sys
import shutil
import time
import cv2

import json

from classifer import classifier
from fps_converter import *

sys.path.append('../videoProcessing/')
from videoCompressorUnconstrainedVideos import videoCompressor

sys.path.append('../PWCNET_ORIEXTRACTOR/')
from PWC_NET import PWC_NET
from cameraMotion import cameraMotion_spatialSampling


def getVideoInfo(videoPath):
    cap = cv2.VideoCapture(videoPath)
    frameTotalNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()
    return height, width, frameTotalNum


def callPWC_NET(videoName, startFrame, endFrame, height, width, outputName=None):
    if outputName == None:
        outputName = videoName

    os.makedirs('./extracted/' + outputName, exist_ok=True)
    time_start = time.time()
    PWC_NET(arguments_strVideo='./videos/' + videoName + '.MP4',
            arguments_strOut_path='./extracted/' + outputName + '/',
            arguments_strStart_Frame=str(startFrame),
            arguments_strFrame_Num=str(endFrame - startFrame + 1)
            )
    time_end = time.time()

    return time_end - time_start


def callCameraMotion(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param=0.82):
    time_start = time.time()
    cameraMotion_spatialSampling(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param)
    time_end = time.time()

    return time_end - time_start


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Wrong number of argument')
        exit()

    os.chdir('../PWCNET_ORIEXTRACTOR/')

    RESIZE_RATE = 12
    SPATIALSAMPLING_RATE = 7
    SKIPFRAMES_RATE = 14

    videoName = sys.argv[1]
    print('videoName: {}'.format(videoName))

    ###
    # COMPRESSED VIDEO
    ###
    print(f'---Resizing the video with a resize rate of {RESIZE_RATE}...')
    time_start = time.time()
    compressor = videoCompressor(videoName, inputPath='./videos/')
    newVideoName = compressor.process(RESIZE_RATE, SKIPFRAMES_RATE, outputPath='./videos/')
    time_end = time.time()
    compression_time = time_end - time_start


    ###
    #   GET COMPRESSED VIDEO INFOS
    ###
    height, width, frameTotalNum = getVideoInfo('./videos/' + newVideoName + '.MP4')
    frameTotalNum -= 2
    startFrame = 0
    endFrame = frameTotalNum - 1
    outputName = 'res_cm_' + newVideoName

    of_time = callPWC_NET(newVideoName, startFrame, endFrame, height, width, outputName=outputName)
    newOutputName = outputName + '__spatialSampling_' + str(SPATIALSAMPLING_RATE)
    shutil.move('./extracted/' + outputName, './extracted/' + newOutputName)
    print('------Processing spatial sampling of', SPATIALSAMPLING_RATE)
    # call camera motion
    print('---------Computing motion ...')


    cm_time = callCameraMotion(newOutputName, startFrame, endFrame, height, width, SPATIALSAMPLING_RATE)
    # copy out the result
    # write the running time

    print('---------Copy result to final destination...')
    shutil.copy('./output/' + newOutputName + '.txt',
                '../unconstrainedVideosClassifier/results/')
    shutil.copy('./output/' + newOutputName + '_timing.txt',
                '../unconstrainedVideosClassifier/results/')

    shutil.move('./extracted/' + newOutputName, './extracted/' + outputName)
    print('------Done spatial sampling of', SPATIALSAMPLING_RATE)

    # delete temp files to save space
    print('---------Delete temp files...')
    shutil.rmtree('./extracted/' + outputName)


    with open('./output/' + newOutputName + '_timing.txt', 'w') as fout:
        fout.write('Compression: ' + str(compression_time) + '\n')
        fout.write('PWC_NET:' + str(of_time) + '\n')
        fout.write('CameraMotion:' + str(cm_time) + '\n')

