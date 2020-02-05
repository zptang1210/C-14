import os
import sys
import shutil
import time
import cv2
sys.path.append('../../videoProcessing/')
from skipFrames import skipFrames
sys.path.append('../../PWCNET_ORIEXTRACTOR/')
from PWCNET_ORIEXTRACTOR_FOCALLEN_spatialSampling import *

def getVideoInfo(videoPath):
    cap = cv2.VideoCapture(videoPath)
    frameTotalNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()
    return height, width, frameTotalNum

if __name__=='__main__':
    os.chdir('../../PWCNET_ORIEXTRACTOR/')

    videoName = 'DJI_0179__compressed_12'

    skipRateList = reversed([1, 2, 3, 5, 10, 15, 30, 60, 90])
    spatialSamplingRateList = [7]

    for skipRate in skipRateList:
        print('Processing skip rate of', skipRate)
        # resize the video
        print('---Processing the video ...')
        compressor = skipFrames(videoName, inputPath='./videos/')
        newVideoName = compressor.process(skipRate, outputPath='./videos/')

        for spatialSamplingRate in spatialSamplingRateList:
            outputName = 'skip_CM_' + newVideoName + '__spatialSampling_' + str(spatialSamplingRate)
            print('------Processing spatial sampling of', spatialSamplingRate)
            # call PWC_NET
            print('---------Computing motion ...')
            newHeight, newWidth, newFrameTotalNum = getVideoInfo('./videos/' + newVideoName + '.MP4')
            startFrame, endFrame = 0, newFrameTotalNum-2
            PWCNET_ORIEXTRACTOR_FOCALLEN(newVideoName, startFrame, endFrame, newHeight, newWidth, spatialSamplingRate, outputName=outputName) 
            # copy out the result
            print('---------Copy result to final destination...')
            shutil.copy('./output/' + outputName + '.txt', '../experiments/skipFrame_spatialSampling_cameraMotionQuality/result/')
            shutil.copy('./output/' + outputName + '_timing.txt', '../experiments/skipFrame_spatialSampling_cameraMotionQuality/result/')
            # delete temp files to save space
            print('---------Delete temp files...')
            shutil.rmtree('./extracted/' + outputName)

            print('------Done spatial sampling of', spatialSamplingRate)

        print('---Done skipRate of', skipRate)

        
