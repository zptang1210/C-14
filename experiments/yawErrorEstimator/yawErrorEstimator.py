import os
import sys
import shutil
import time
import math
import json
import re
from torch import multiprocessing
import cv2
import numpy as np
# import matplotlib.pyplot as plt
from metadataCorrector import metadataCorrector

current_folder_path = os.path.split(os.path.realpath(__file__))[0] + '/'
sys.path.append(current_folder_path + '../../utils')
from program import program
from parseMetadata_new import parseMetadata
from parseComputedMotion import parseComputedMotion
from convertCameraCoordFrameToDrone import convertCameraCoordFrameToDrone
sys.path.append(current_folder_path + '../../videoProcessing')
from skipFrames import skipFrames
from videoCompressor import videoCompressor
sys.path.append('../../PWCNET_ORIEXTRACTOR')
from PWC_NET import PWC_NET


# Machine-dependent parameters
# on Gypsum server
MATLAB_RUNTIME_PATH = '/cm/shared/apps/MATLAB/MATLAB_Runtime/v901'

# # on Fisher server
# MATLAB_RUNTIME_PATH = '/exp/comm/matlab-R2016a'



class yawErrorEstimator(object):

    def __init__(self, rawVideoName, metadataName, droneProgram, sampleParam, compressParam=None):
        self.rawVideoName = rawVideoName
        self.metadataName = metadataName
        self.droneProgram = droneProgram
        self.videoName = None # the name of the video after processing
        self.hpSampleLength = sampleParam['hotpointSampleLength']
        self.hpSampleRate = sampleParam['hotpointSampleRate']
        if compressParam == None:
            self.resizeNum = 1
            self.skipFrameNum = 1
        else:
            self.resizeNum = compressParam['resize']
            self.skipFrameNum = compressParam['skipFrames']

        self.compression_time = None
        self.opticalFlow_time = None
        self.cameraMotion_time = None
        self.sampleNum = None


    def estimateYawErrorList(self, disableAutoCompression=True):
        path_backup = os.getcwd() # backup the current working directory, and will restore by the end of the program
        os.chdir(current_folder_path + '../../PWCNET_ORIEXTRACTOR/')

        self.compression_time = time.time()
        self.videoName = self.__compressVideo(disabled=disableAutoCompression)
        self.compression_time = time.time() - self.compression_time
        print(self.videoName)

        # get video info
        self.__getVideoInfo()

        # parse metadata and correct it
        _, waypointTimeList_forward, waypointTimeList_backward, _ = self.__parseMetadataWithCorrection()

        # convert timestamp to framestamp for corrected hotpoint and waypoint list
        waypointFrameList_forward = self.__getMotionFrameListWithSkip(waypointTimeList_forward)
        waypointFrameList_backward = self.__getMotionFrameListWithSkip(waypointTimeList_backward)
        hotpointFrameList = self.__getHotpointFrameList(waypointFrameList_forward, waypointFrameList_backward)
        # print(hotpointFrameList, waypointFrameList_forward, waypointFrameList_backward)

        # Start to check the consistency between the output of cameraMotion and program.
        # For each hotpoint and each waypoint, sample and compute via cameraMotion, and then use some rules to check if it matches up.

        # draw samples from hotpoint and waypoint, and send to cuda to compute optical flow
        hpSampleDict, allSamples = self.__drawAllSamples(hotpointFrameList)
        print(allSamples, self.sampleNum)

        self.opticalFlow_time = time.time()
        outputNameDict = dict()
        for i, (startFrame, endFrame) in enumerate(allSamples):
            outputName = self.videoName + '_' + str(startFrame) + '_' + str(endFrame)
            outputNameDict[(startFrame, endFrame)] = outputName
            self.computeOpticalFlow(startFrame, endFrame, outputName)  
        self.opticalFlow_time = time.time() - self.opticalFlow_time
        

        self.cameraMotion_time = time.time()
        sample_batch = allSamples
        outputNameList = []
        for startFrame, endFrame in sample_batch:
            outputName = outputNameDict[(startFrame, endFrame)]
            outputNameList.append(outputName)
        batchInfoFileName = 'batch_info_' + self.videoName + '_' + str(i)        
        self.computeCameraMotion_batch(sample_batch, outputNameList, batchInfoFileName)
        self.cameraMotion_time = time.time() - self.cameraMotion_time


        print('VERIFYING:', self.videoName)
        yawEstimationList = self.__checkHotpoint(hotpointFrameList, hpSampleDict, outputNameDict)
        
        os.chdir(path_backup)

        return yawEstimationList


    def __compressVideo(self, disabled=False):
        if disabled:
            return self.rawVideoName
        else:
            # compress the video according to compressParam
            if self.resizeNum == 1 and self.skipFrameNum == 1:
                videoName = self.rawVideoName
            else:
                tempVideoName = self.rawVideoName
                if self.skipFrameNum != 1:
                    compressor = skipFrames(tempVideoName, inputPath='./videos/')
                    tempVideoName = compressor.process(self.skipFrameNum, outputPath='./videos/') 
                if self.resizeNum != 1:
                    compressor = videoCompressor(tempVideoName, inputPath='./videos/')
                    tempVideoName = compressor.process(self.resizeNum, outputPath='./videos/')
                videoName = tempVideoName   
            return videoName


    def computeOpticalFlow(self, startFrame, endFrame, outputName):
        os.makedirs('./extracted/' + outputName, exist_ok=True)
        PWC_NET(arguments_strVideo = './videos/' + self.videoName + '.MP4',
                arguments_strOut_path = './extracted/' + outputName + '/',
                arguments_strStart_Frame = str(startFrame),
                arguments_strFrame_Num = str(endFrame-startFrame+1)
            )

    
    def computeCameraMotion_batch(self, sample_batch, outputNameList, batchInfoFileName):
        with open('./batchInfo/' + batchInfoFileName + '.txt', 'w') as fout:
            fout.write('%d\n' % len(sample_batch))
            for sample, outputName in zip(sample_batch, outputNameList):
                startFrame, endFrame = sample
                fout.write('%d,%d,%s\n' % (startFrame, endFrame, outputName))      

        focallen_param = 0.82
        command_ori = './cameraMotion_parallelized_batch/run_extractOrientation.sh' + ' ' +\
            MATLAB_RUNTIME_PATH + ' ' + (batchInfoFileName+'.txt') + ' ' +\
            str(self.height) + ' ' + str(self.width) + ' ' + str(focallen_param)   
        # print(command_ori)
        os.system(command_ori)  


    def __drawAllSamples(self, hotpointFrameList):
        print('Sample from Hotpoint')
        hotpointSampleDict = dict() #第i个hotpoint有哪些sample
        hotpointSampleList = list()
        numHotpoint = len(hotpointFrameList)
        for i in range(numHotpoint):
            print('#%d' % i)
            sampleRange = (hotpointFrameList[i][0], hotpointFrameList[i][1]-1)
            assert hotpointFrameList[i][1] - hotpointFrameList[i][0] >= 2
            sampleNum = max(2, int(self.hpSampleRate * (hotpointFrameList[i][1] - hotpointFrameList[i][0])))
            sampleIntervals = self.getSampleIntervals(sampleRange, sampleNum=sampleNum, sampleLength=self.hpSampleLength, includeEndPoints=True)
            print('sampling:', sampleIntervals)
            hotpointSampleDict[i] = sampleIntervals
            hotpointSampleList.extend(sampleIntervals)

        self.sampleNum = len(hotpointSampleList)
        return hotpointSampleDict, hotpointSampleList


    def __checkHotpoint(self, hotpointFrameList, hotpointSampleDict, outputNameDict):
        print('CHECK hotpoint')
        yawEstimationList = []
        numHotpoint = len(hotpointFrameList)
        for i in range(numHotpoint):
            print('#%d' % i)
            print(hotpointFrameList[i])
            sampleIntervals = hotpointSampleDict[i]
            print('sampling:', sampleIntervals)

            frameList = []
            yawList = []
            for sStartFrame, sEndFrame in sampleIntervals:
                # read rot and trans in camera FR
                parser = parseComputedMotion('./output/' + outputNameDict[(sStartFrame, sEndFrame)] + '.txt')
                sampleMotion = parser.parse()
                sampleDroneMotion = self.__convertMotionToDroneFR(sampleMotion)

                # save all motion for further computation
                droneRot, droneTrans = sampleDroneMotion
                yawList.append(droneRot[:, 1])
                frameList.append(np.arange(sStartFrame, sEndFrame+1))

            # check angle difference
            yawList = np.concatenate(yawList)
            frameList = np.concatenate(frameList)

            estHotpointAngle = 0
            for k in range(len(frameList)-1):
                area = (yawList[k] + yawList[k+1]) * (frameList[k+1] - frameList[k]) / 2
                estHotpointAngle += area
            estHotpointAngle = np.rad2deg(estHotpointAngle)

            print('estimatedHotpointAngle', estHotpointAngle)
            print('idealHotpointAngle', self.droneProgram.travelledAngles[i])
            
            yawEstimationList.append((self.droneProgram.travelledAngles[i], estHotpointAngle))

        return yawEstimationList     


    def __getVideoInfo(self):
        cap = cv2.VideoCapture('./videos/' + self.videoName + '.MP4') # MP4 format by default
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.FPS = cap.get(cv2.CAP_PROP_FPS)
        self.totalFrameNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()          

    
    def __parseMetadataWithCorrection(self):
        # parse metadata
        metadataParser = parseMetadata('./output/metadata/' + self.metadataName + '.metadata')
        rawInfo = metadataParser.parse()

        motionClass, recordVideoTime, hotpointTimeList, waypointTimeList, _ = rawInfo
        self.droneCameraAngle = motionClass.droneAngle
        self.actualStartRecTime = recordVideoTime[1]  # actual timestamp starting recording is the end timestamp label of recordVideoTime

        # correct metadata      
        corrector = metadataCorrector(rawInfo)
        hotpointTimeList_corr, waypointTimeList_corr, hotpointTimeLength_corr = corrector.correctTimestamp()        
        waypointTimeList_forward, waypointTimeList_backward = waypointTimeList_corr

        return hotpointTimeList_corr, waypointTimeList_forward, waypointTimeList_backward, hotpointTimeLength_corr

    
    def __getMotionFrameListWithSkip(self, motionTimeList, verbose=False):
        motionFrameList = []

        for (startTimestamp, endTimestamp) in motionTimeList:
            startFramestamp = math.ceil(self.__toFramestampWithSkip(startTimestamp))
            endFramestamp = math.floor(self.__toFramestampWithSkip(endTimestamp))
            motionFrameList.append((startFramestamp, endFramestamp))
            
            if verbose: print('motion start end framestamp', startFramestamp, endFramestamp)  
        
        return motionFrameList


    # def __getHotpointFrameList(self, waypointFrameList_forward, waypointFrameList_backward):
    #     hpFrameList_start, hpFrameList_end = [], []
    #     for wp_backward in waypointFrameList_backward:
    #         _, end = wp_backward
    #         hpFrameList_start.append(end)

    #     for wp_forward in waypointFrameList_forward[1:]:
    #         start, _ = wp_forward
    #         hpFrameList_end.append(start)
    #     hpFrameList_end.append(self.totalFrameNum - 2)  # -2 because videos have 0 - totalFrameNum-1 frames, but camera motion has 0 - totalFrameNum-2

    #     hpFrameList = []
    #     for start, end in zip(hpFrameList_start, hpFrameList_end):
    #         hpFrameList.append((start, end))

    #     return hpFrameList


    # new version to accomodate the case fly in/out is the last motion
    def __getHotpointFrameList(self, waypointFrameList_forward, waypointFrameList_backward):
        hpFrameList = []
        if self.droneProgram.numAngles < len(waypointFrameList_forward):
            waypointAtLast = True
        elif self.droneProgram.numAngles == len(waypointFrameList_forward):
            waypointAtLast = False
        else:
            raise Exception('Wrong number of hotpoints or waypoints')

        if waypointAtLast:
            hpFrameList_start, hpFrameList_end = [], []
            for wp_backward in waypointFrameList_backward[:-1]:
                _, end = wp_backward
                hpFrameList_start.append(end)

            for wp_forward in waypointFrameList_forward[1:]:
                start, _ = wp_forward
                hpFrameList_end.append(start)

            for start, end in zip(hpFrameList_start, hpFrameList_end):
                hpFrameList.append((start, end))

        else:
            hpFrameList_start, hpFrameList_end = [], []
            for wp_backward in waypointFrameList_backward:
                _, end = wp_backward
                hpFrameList_start.append(end)

            for wp_forward in waypointFrameList_forward[1:]:
                start, _ = wp_forward
                hpFrameList_end.append(start)
            hpFrameList_end.append(self.totalFrameNum - 2)  # -2 because videos have 0 - totalFrameNum-1 frames, but camera motion has 0 - totalFrameNum-2

            for start, end in zip(hpFrameList_start, hpFrameList_end):
                hpFrameList.append((start, end))


        return hpFrameList


    def __toFramestampWithSkip(self, timestamp):
        framestamp = ((timestamp - self.actualStartRecTime) / 1000 * self.FPS) / self.skipFrameNum
        return framestamp


    def __toFrameUnitWithoutSkip(self, minisec):
        return minisec / 1000 * self.FPS


    def __getMotionInSampleInterval(self, startFrame, endFrame, cudaID=None, isTest=False, cameraMotionOutputName=None):
        if isTest==False:
            outputName = self.videoName + '_' + str(startFrame) + '_' + str(endFrame)
            PWCNET_ORIEXTRACTOR_FOCALLEN(self.videoName, startFrame, endFrame, self.height, self.width, cudaID, outputName=outputName) 
            parser = parseComputedMotion('./output/' + outputName + '.txt')
            rot, trans = parser.parse()
        elif isTest==True and cameraMotionOutputName!=None:
            # Acquire the output of camera motion directly from the computed file
            parser = parseComputedMotion('./output/' + cameraMotionOutputName + '.txt')
            rot_all, trans_all = parser.parse()
            rot = rot_all[startFrame:endFrame+1, :]
            trans = trans_all[startFrame:endFrame+1, :]
        else:
            raise Exception('Wrong usage of getSampledEstMotion.')

        return rot, trans

    
    def __convertMotionToDroneFR(self, motion):
        rot, trans = motion
        converter = convertCameraCoordFrameToDrone(rot, trans)
        droneRot, droneTrans = converter.convert(self.droneCameraAngle)
        return droneRot, droneTrans   


    def getRunningTime(self):
        return self.compression_time, self.opticalFlow_time, self.cameraMotion_time, self.sampleNum


    # def getSampleIntervals(self, interval, sampleNum, sampleLength, includeEndPoints=False):
    #     start, end = interval
    #     samples = []

    #     if includeEndPoints:
    #         assert end-start+1 >= 2 # start and end should be different
    #         samples = [(end, end), (start, start)]
    #         start += 1
    #         end -= 1
    #         sampleNum -= 2

    #     i=0
    #     while i<sampleNum:
    #         if end-start+1 == sampleLength:
    #             samples.append((start, end))
    #             break
    #         elif end-start+1 < sampleLength:
    #             break
            
    #         k = (end - start) / (sampleNum - i)
    #         sEnd = np.random.randint(max(start+sampleLength-1, end-k), end)
    #         sStart = sEnd - sampleLength + 1
    #         if sStart < start:
    #             break
    #         else:
    #             samples.append((sStart, sEnd))
    #             end = sStart - 1
    #             i+=1
        
    #     samples.sort(key=lambda x:x[1])
        
    #     return samples

    
    def getSampleIntervals(self, interval, sampleNum, sampleLength=None, includeEndPoints=False):
        start, end = interval
        assert end - start + 1 >= sampleNum

        samples = []
        
        if includeEndPoints:
            assert end-start+1 >= 2 # start and end should be different
            samples = [(start, start), (end, end)]
            start += 1
            end -= 1
            sampleNum -= 2
        
        xx = np.random.choice(np.arange(start, end+1), sampleNum, replace=False)
        for x in xx:
            samples.append((x, x))

        samples.sort(key=lambda x:x[1])

        return samples





# def main():
#     sampleParam = {'hotpointSampleLength': 3, 'hotpointMaxSampleNum': 30}
#     compressParam = {'resize': 5, 'skipFrames': 25}

#     plan0412 = program(((173, None), (65, False), (205, True), (139, False)))
#     estimator = yawErrorEstimator('DJI_0412', 'DJI_0412_corrected', plan0412, sampleParam, compressParam)

#     time_start=time.time()
#     estYawList = estimator.estimateYawErrorList(disableAutoCompression=False)  
#     time_end=time.time()

#     print(estYawList)
#     print('total time consumed:',time_end-time_start)    

#     print(estimator.getRunningTime())



if __name__=='__main__':
    dataset_720p = [
        # ('DJI_0404', 'DJI_0404_corrected', program(((43, None), (10, False), (179, False), (281, False)))),

        ('DJI_0411', 'DJI_0411', program(((173, None), (65, False), (205, True), (139, False)))),
        # ('DJI_0403', 'DJI_0403_corrected', program(((214, None), (57, False), (248, False), (126, True)))),
        # ('DJI_0412', 'DJI_0412_corrected', program(((173, None), (65, False), (205, True), (139, False)))),
        # ('DJI_0410', 'DJI_0410', program(((214, None), (57, False), (248, False), (126, True)))),

        # ('DJI_0400', 'DJI_0400', program(((125, None), (39, False), (344, True), (65, True)))),
        # ('DJI_0402', 'DJI_0402', program(((56, None), (347, True), (183, False), (357, True))))
    ]

    dataset_4k = [
        # ('DJI_0447', 'DJI_0447_corrected', program(((7, None), (217, True), (327, True), (14, True))))
        # ('DJI_0488', 'DJI_0488', program(((286, None), (215, True), (310, True), (184, True), (59, False))))

        # ('DJI_0443', 'DJI_0443', program(((63, None), (346, False), (128, False), (7, False)))),
        # ('DJI_0439', 'DJI_0439', program(((125, None), (177, True), (114, False), (260, True)))),

        # ('DJI_0460', 'DJI_0460_corrected', program(((333, None), (182, True), (22, True), (159, True)))),
        # ('DJI_0459', 'DJI_0459_corrected', program(((50, None), (142, True), (249, False), (2, False))))

        # ('DJI_0494', 'DJI_0494', program(((93, None), (321, True), (337, False), (228, True), (288, True)))),
        # ('DJI_0495', 'DJI_0495', program(((244, None), (173, False), (221, True), (311, True), (277, True)))),
        # ('DJI_0496', 'DJI_0496', program(((186, None), (53, False), (80, False), (137, False), (305, False)))),
        # ('DJI_0489', 'DJI_0489', program(((78, None), (194, True), (272, True), (135, True), (315, False)))),

        # ('DJI_0490', 'DJI_0490', program(((307, None), (147, True), (77, False), (28, False), (220, False)))),
        # ('DJI_0491', 'DJI_0491', program(((267, None), (89, True), (143, True), (41, True), (301, True))))

        ('DJI_0504_copy', 'DJI_0504', program(((161, None), (29, True), (122, False), (249, True), (328, False))))
    ]

    resizeRateList_4k = [12]  
    resizeRateList_720p = [4] 

    #720p
    dataset = dataset_720p
    resizeRateList = resizeRateList_720p

    # #4k
    # dataset = dataset_4k
    # resizeRateList = resizeRateList_4k


    repeatNum = 2 
    skipRateList = [15]  
    sampleRateList = [1.0]
    sampleLength = 1

    path = '../../PWCNET_ORIEXTRACTOR/videos/'
    for sampleRate in sampleRateList:
        for skipRate in skipRateList:
            for resizeRate in resizeRateList:
                fout1 = open('log_{}_{}_{}.txt'.format(str(sampleRate), str(skipRate), str(resizeRate)), 'w')
                fout2 = open('time_{}_{}_{}.txt'.format(str(sampleRate), str(skipRate), str(resizeRate)), 'w')
                for data in dataset:
                    for i in range(repeatNum):
                        videoName, metadataName, droneProgram = data
                        newVideoName = 'yawError2_' + videoName
                        sampleParam = {'hotpointSampleLength': sampleLength, 'hotpointSampleRate': sampleRate}
                        compressParam = {'resize': resizeRate, 'skipFrames': skipRate}
                        shutil.copyfile(path+videoName+'.MP4', path+newVideoName+'.MP4')

                        estimator = yawErrorEstimator(newVideoName, metadataName, droneProgram, sampleParam, compressParam)
                        
                        time_start = time.time()
                        estYawList = estimator.estimateYawErrorList(disableAutoCompression=False)
                        time_end = time.time()
                        print(estYawList)

                        for idealAngle, estAngle in estYawList:
                            print('#', i, file=fout1)
                            print('video', videoName, file=fout1)
                            print('sampleRate', sampleRate, file=fout1)
                            print('skipRate', skipRate, file=fout1)
                            print('resizeRate', resizeRate, file=fout1)
                            print('estYaw', estAngle, file=fout1)
                            print('realYaw', idealAngle, file=fout1)
                            print('diff', abs(estAngle) - idealAngle, '\n', file=fout1)

                        print('#', i, file=fout2)
                        print('video', videoName, file=fout2)
                        print('sampleRate', sampleRate, file=fout2)
                        print('skipRate', skipRate, file=fout2)
                        print('resizeRate', resizeRate, file=fout2)
                        print('totalTime', time_end-time_start, file=fout2)
                        print('detailedRunningTime', estimator.getRunningTime(), '\n', file=fout2)

                        os.remove(path+newVideoName+'.MP4')

                fout1.close()
                fout2.close()
