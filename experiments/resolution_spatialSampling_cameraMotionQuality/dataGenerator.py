import os
import sys
import shutil
import time
import cv2
sys.path.append('../../videoProcessing/')
from videoCompressor import videoCompressor
sys.path.append('../../PWCNET_ORIEXTRACTOR/')
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
    if outputName==None:
        outputName = videoName

    os.makedirs('./extracted/' + outputName, exist_ok=True)
    time_start = time.time()
    PWC_NET(arguments_strVideo = './videos/' + videoName + '.MP4',
            arguments_strOut_path = './extracted/' + outputName + '/',
            arguments_strStart_Frame = str(startFrame),
            arguments_strFrame_Num = str(endFrame-startFrame+1)
        )
    time_end = time.time()

    return time_end - time_start

def callCameraMotion(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param=0.82):
    time_start = time.time()
    cameraMotion_spatialSampling(outputName, startFrame, endFrame, height, width, spatialSamplingRate, focallen_param)    
    time_end = time.time()

    return time_end - time_start

if __name__=='__main__':
    os.chdir('../../PWCNET_ORIEXTRACTOR/')

    videoName = 'DJI_0179'
    videoPath = './videos/' + videoName + '.MP4'
    height, width, frameTotalNum = getVideoInfo(videoPath)
    frameTotalNum -= 1
    fullVideo = True

    if fullVideo:
        startFrame, endFrame = 0, frameTotalNum-1
    else:
        startFrame, endFrame = 2800, 2899        

    resizeRateList = [12]
    spatialSamplingRateList = [3, 5]

    for resizeRate in resizeRateList:
        print('Processing resize rate of', resizeRate)
        # resize the video
        print('---Resizing the video ...')
        compressor = videoCompressor(videoName, inputPath='./videos/')
        newVideoName = compressor.process(resizeRate, outputPath='./videos/')
        newHeight, newWidth, _ = getVideoInfo('./videos/' + newVideoName + '.MP4')
        outputName = 'res_cm_' + newVideoName
        of_time = callPWC_NET(newVideoName, startFrame, endFrame, newHeight, newWidth, outputName=outputName)

        for spatialSamplingRate in spatialSamplingRateList:
            newOutputName = outputName + '__spatialSampling_' + str(spatialSamplingRate)
            if not fullVideo: newOutputName += ('_' + str(startFrame) + '_' + str(endFrame))
            shutil.move('./extracted/'+outputName, './extracted/'+newOutputName)
            print('------Processing spatial sampling of', spatialSamplingRate)
            # call camera motion
            print('---------Computing motion ...')
            cm_time = callCameraMotion(newOutputName, startFrame, endFrame, newHeight, newWidth, spatialSamplingRate) 
            # copy out the result
            # write the running time
            with open('./output/' + newOutputName + '_timing.txt', 'w') as fout:
                fout.write('PWC_NET:' + str(of_time) + '\n')
                fout.write('CameraMotion:' + str(cm_time) + '\n')
            print('---------Copy result to final destination...')
            shutil.copy('./output/' + newOutputName + '.txt', '../experiments/resolution_spatialSampling_cameraMotionQuality/result/')
            shutil.copy('./output/' + newOutputName + '_timing.txt', '../experiments/resolution_spatialSampling_cameraMotionQuality/result/')
            
            shutil.move('./extracted/'+newOutputName, './extracted/'+outputName)
            print('------Done spatial sampling of', spatialSamplingRate)

        
        # delete temp files to save space
        print('---------Delete temp files...')
        shutil.rmtree('./extracted/' + outputName)

        print('---Done resizeRate of', resizeRate)

        
