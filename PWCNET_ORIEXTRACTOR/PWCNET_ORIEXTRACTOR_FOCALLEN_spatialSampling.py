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


if __name__ == '__main__':
     if len(sys.argv) == 2 or len(sys.argv) == 4 or len(sys.argv) == 5 or len(sys.argv) == 6:
          videoName = sys.argv[1]
          cap = cv2.VideoCapture('./videos/' + videoName + '.MP4') # MP4 format by default
          
          if len(sys.argv) == 2:
               frameStart = 0
               frameEnd = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
               focallen_param = DEFAULT_FOCALLEN
               outputName = None
          elif len(sys.argv) == 4:
               frameStart = int(sys.argv[2])
               frameEnd = int(sys.argv[3])
               focallen_param = DEFAULT_FOCALLEN
               outputName = None
          elif len(sys.argv) == 5:
               frameStart = int(sys.argv[2])
               frameEnd = int(sys.argv[3])
               focallen_param = float(sys.argv[4])
               outputName = None               
          elif len(sys.argv) == 6:
               frameStart = int(sys.argv[2])
               frameEnd = int(sys.argv[3])
               focallen_param = float(sys.argv[4])
               outputName = sys.argv[5]

          height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
          width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

          PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, frameStart, frameEnd, height, width, focallen_param=focallen_param, outputName=outputName)

          cap.release()
     else:
          print('Command Formatting:\nscript.py videoName\nscript.py videoName frameStart frameEnd\nscript.py videoName frameStart frameEnd focallen_param\nscript.py videoName frameStart frameEnd focallen_param outputName\n')

     
     
