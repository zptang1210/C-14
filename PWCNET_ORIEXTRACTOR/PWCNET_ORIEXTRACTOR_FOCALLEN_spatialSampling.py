import os
import sys
import time
import cv2
from PWC_NET import PWC_NET
from cameraMotion import cameraMotion_spatialSampling

DEFAULT_FOCALLEN = 0.82

def PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param=DEFAULT_FOCALLEN, outputName=None):
     if outputName==None:
          outputName = videoName

     fout = open('./output/' + outputName + '_timing.txt', 'w')

     os.makedirs('./extracted/' + outputName, exist_ok=True)
     time_start = time.time()
     PWC_NET(arguments_strVideo = './videos/' + videoName + '.MP4',
             arguments_strOut_path = './extracted/' + outputName + '/',
             arguments_strStart_Frame = str(startFrame),
             arguments_strFrame_Num = str(endFrame-startFrame+1)
          )
     time_end = time.time()
     fout.write('PWC_NET:' + str(time_end - time_start) + '\n')

     time_start = time.time()
     cameraMotion_spatialSampling(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param)
     time_end = time.time()
     fout.write('CameraMotion:' + str(time_end - time_start) + '\n')

     fout.close()


     
     
