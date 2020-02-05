import os
import sys
import time
import math
import json
import re
import cv2
import numpy as np
# import matplotlib.pyplot as plt
from verifierBase import verifierBase
from metadataCorrector import metadataCorrector

current_folder_path = os.path.split(os.path.realpath(__file__))[0] + '/'
sys.path.append(current_folder_path + '../utils')
from program import program
from parseMetadata_new import parseMetadata
from parseComputedMotion import parseComputedMotion
from convertCameraCoordFrameToDrone import convertCameraCoordFrameToDrone
sys.path.append(current_folder_path + '../videoProcessing')
from skipFrames import skipFrames
from videoCompressor import videoCompressor
sys.path.append(current_folder_path + '../PWCNET_ORIEXTRACTOR')
from PWC_NET import PWC_NET

almostAllThreshold = 0.6

# Test mode
# mode[0]==True means this is test mode
# mode[1] specifies the file name of cameraMotion
# mode = (True, 'DJI_0179__compressed_5')
mode = (False, None)

# Machine-dependent parameters
# on Gypsum server
MATLAB_RUNTIME_PATH = '/cm/shared/apps/MATLAB/MATLAB_Runtime/v901'

# # on Fisher server
# MATLAB_RUNTIME_PATH = '/exp/comm/matlab-R2016a'



class verifier(verifierBase):

    def __init__(self, rawVideoName, metadataName, droneProgram, threshold, sampleParam, compressParam=None):
        super().__init__(rawVideoName, metadataName, droneProgram)
        self.videoName = None # the name of the video after processing
        self.threshold = threshold
        self.hpSampleLength = sampleParam['hotpointSampleLength']
        self.hpSampleRate = sampleParam['hotpointSampleRate']
        self.wpSampleLength = sampleParam['waypointSampleLength']
        self.wpMaxSampleNum = sampleParam['waypointMaxSampleNum']
        if compressParam == None:
            self.resizeNum = 1
            self.skipFrameNum = 1
        else:
            self.resizeNum = compressParam['resize']
            self.skipFrameNum = compressParam['skipFrames']

        self.compression_time = None
        self.opticalFlow_time = None
        self.cameraMotion_time = None
        self.hpSampleNum = None
        self.wpSampleNum = None


    def verify(self, disableAutoCompression=True):
        path_backup = os.getcwd() # backup the current working directory, and will restore by the end of the program
        os.chdir(current_folder_path + '../PWCNET_ORIEXTRACTOR/')

        self.compression_time = time.time()
        self.videoName = self.__compressVideo(disabled=disableAutoCompression)
        self.compression_time = time.time() - self.compression_time
        print(self.videoName)

        # get video info
        self.__getVideoInfo()
        print('videoName:', self.videoName)

        # parse metadata and correct it
        __hotpointTimeList, waypointTimeList_forward, waypointTimeList_backward, hotpointTimeLengthList = self.__parseMetadataWithCorrection()

        # convert timestamp to framestamp for corrected hotpoint and waypoint list
        # __hotpointFrameList_deprecated = self.__getMotionFrameListWithSkip(__hotpointTimeList)
        waypointFrameList_forward = self.__getMotionFrameListWithSkip(waypointTimeList_forward)
        waypointFrameList_backward = self.__getMotionFrameListWithSkip(waypointTimeList_backward)
        waypointFrameList_forward, waypointFrameList_backward = self.__cleanGapBetweenForwardAndBackward(waypointFrameList_forward, waypointFrameList_backward)
        hotpointFrameList = self.__getHotpointFrameListFromWaypointGap(waypointFrameList_forward, waypointFrameList_backward)
        print('hp&wp frameList:', hotpointFrameList, waypointFrameList_forward, waypointFrameList_backward)

        hpSampleDict, wpForwardSampleDict, wpBackwardSampleDict, allSamples = self.__drawAllSamples(hotpointFrameList, waypointFrameList_forward, waypointFrameList_backward)

        # Start to check the consistency between the output of cameraMotion and program.
        # For each hotpoint and each waypoint, sample and compute via cameraMotion, and then use some rules to check if it matches up.
        # draw samples from hotpoint and waypoint, and send to cuda to compute optical flow
        self.opticalFlow_time = time.time()
        outputNameDict = dict()
        for i, (startFrame, endFrame) in enumerate(allSamples):
            outputName = self.videoName + '_' + str(startFrame) + '_' + str(endFrame)
            outputNameDict[(startFrame, endFrame)] = outputName
            self.computeOpticalFlow(startFrame, endFrame, outputName)  
        self.opticalFlow_time = time.time() - self.opticalFlow_time

        # compute cameraMotion     
        self.cameraMotion_time = time.time()
        sample_batch = allSamples
        outputNameList = []
        for startFrame, endFrame in sample_batch:
            outputName = outputNameDict[(startFrame, endFrame)]
            outputNameList.append(outputName)
        batchInfoFileName = 'batch_info_' + self.videoName + '_' + str(i)        
        self.computeCameraMotion_batch(sample_batch, outputNameList, batchInfoFileName)
        self.cameraMotion_time = time.time() - self.cameraMotion_time


        print('VERIFYING:', self.videoName, self.droneProgram)
        flag = None
        if self.__checkHotpoint(hotpointFrameList, hpSampleDict, outputNameDict):
            if self.__checkWaypoint_forward(waypointFrameList_forward, wpForwardSampleDict, outputNameDict) and \
               self.__checkWaypoint_backward(waypointFrameList_backward, wpBackwardSampleDict, outputNameDict):
                flag = True
            else:
                flag = False
        else:
            flag = False
        
        os.chdir(path_backup)
        return flag


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


    def __drawAllSamples(self, hotpointFrameList, waypointFrameList_forward, waypointFrameList_backward):
        print('Sample from Hotpoint')
        hotpointSampleDict = dict() #第i个hotpoint有哪些sample
        hotpointSampleList = list()
        numHotpoint = len(hotpointFrameList)
        # assert numHotpoint == self.droneProgram.numAngles #判断数目是否相等
        for i in range(numHotpoint):
            print('#%d' % i)
            sampleRange = (hotpointFrameList[i][0], hotpointFrameList[i][1]-1)
            assert hotpointFrameList[i][1] - hotpointFrameList[i][0] >= 2
            sampleNum = max(2, int(self.hpSampleRate * (hotpointFrameList[i][1] - hotpointFrameList[i][0])))
            sampleIntervals = self.__getSampleIntervals(sampleRange, sampleNum=sampleNum, sampleLength=self.hpSampleLength, includeEndPoints=True)
            print('sampling:', sampleIntervals)
            hotpointSampleDict[i] = sampleIntervals
            hotpointSampleList.extend(sampleIntervals)
        
        self.hpSampleNum = len(hotpointSampleList)


        print('Sample from Waypoint(forward)')
        waypointForwardSampleDict = dict()
        waypointForwardSampleList = list()
        numWaypoint = len(waypointFrameList_forward)
        for i in range(numWaypoint):
            print('#%d' % i)
            sampleRange = (waypointFrameList_forward[i][0], waypointFrameList_forward[i][1]-1)
            sampleIntervals = self.__getSampleIntervals(sampleRange, sampleNum=self.wpMaxSampleNum, sampleLength=self.wpSampleLength)
            print('sampling:', sampleIntervals)
            waypointForwardSampleDict[i] = sampleIntervals
            waypointForwardSampleList.extend(sampleIntervals)

        wpSampleNum_forward = len(waypointForwardSampleList)


        print('Sample from Waypoint(backward)')
        waypointBackwardSampleDict = dict()
        waypointBackwardSampleList = list()
        numWaypoint = len(waypointFrameList_backward)
        for i in range(numWaypoint):
            print('#%d' % i)
            sampleRange = (waypointFrameList_backward[i][0], waypointFrameList_backward[i][1]-1)
            sampleIntervals = self.__getSampleIntervals(sampleRange, sampleNum=self.wpMaxSampleNum, sampleLength=self.wpSampleLength)
            print('sampling:', sampleIntervals)
            waypointBackwardSampleDict[i] = sampleIntervals
            waypointBackwardSampleList.extend(sampleIntervals)

        wpSampleNum_backward = len(waypointBackwardSampleList)
        self.wpSampleNum = wpSampleNum_forward + wpSampleNum_backward

        allSamples = hotpointSampleList + waypointForwardSampleList + waypointBackwardSampleList

        return hotpointSampleDict, waypointForwardSampleDict, waypointBackwardSampleDict, allSamples



    def __checkHotpoint(self, hotpointFrameList, hotpointSampleDict, outputNameDict):
        print('CHECK hotpoint')
        numHotpoint = len(hotpointFrameList)
        if numHotpoint != self.droneProgram.numAngles: #判断数目是否相等
            print('number of hotpoints doesn\'t match')
            return False

        for i in range(numHotpoint):
            print('#%d' % i)
            print(hotpointFrameList[i])
            sampleIntervals = hotpointSampleDict[i]
            print('sampling:', sampleIntervals)

            droneRotList = []
            droneTransList = []
            frameList = []
            yawList = []
            for sStartFrame, sEndFrame in sampleIntervals:
                # read rot and trans in camera FR
                parser = parseComputedMotion('./output/' + outputNameDict[(sStartFrame, sEndFrame)] + '.txt')
                sampleMotion = parser.parse()
                sampleDroneMotion = self.__convertMotionToDroneFR(sampleMotion)

                # save all motion for further computation
                droneRot, droneTrans = sampleDroneMotion
                droneRotList.append(droneRot)
                droneTransList.append(droneTrans)
                frameList.append(np.arange(sStartFrame, sEndFrame+1))
                yawList.append(droneRot[:, 1])

            droneRotList = np.concatenate(droneRotList)
            droneTransList = np.concatenate(droneTransList)
            frameList = np.concatenate(frameList)
            yawList = np.concatenate(yawList)

            if not self.__isHotpoint((droneRotList, droneTransList), self.droneProgram.isClockwise[i], verbose=True):
                print('hotpoint test fails!')
                return False

            # check angle difference
            estHotpointAngle = 0
            for k in range(len(frameList)-1):
                area = (yawList[k] + yawList[k+1]) * (frameList[k+1] - frameList[k]) / 2
                estHotpointAngle += area
            estHotpointAngle = np.rad2deg(estHotpointAngle)

            print('estimatedHotpointAngle', estHotpointAngle)
            print('idealHotpointAngle', self.droneProgram.travelledAngles[i])

            if abs(abs(estHotpointAngle) - self.droneProgram.travelledAngles[i]) > self.threshold['angleDiff']:
                print('angleDiff test fails', '(est=%f, target=%f)' % (estHotpointAngle, self.droneProgram.travelledAngles[i]))
                return False
            
            print('pass!')

        return True      


    def __checkWaypoint_forward(self, waypointFrameList_forward, waypointForwardSampleDict, outputNameDict):
        print('CHECK waypoint (forward)')
        numWaypoint = len(waypointFrameList_forward)
        for i in range(numWaypoint):
            print('#%d' % i)
            print(waypointFrameList_forward[i])
            sampleIntervals = waypointForwardSampleDict[i]
            print('sampling:', sampleIntervals)

            frameList = []
            yawList = []
            for sStartFrame, sEndFrame in sampleIntervals:
                # read rot and trans in camera FR
                parser = parseComputedMotion('./output/' + outputNameDict[(sStartFrame, sEndFrame)] + '.txt')
                sampleMotion = parser.parse()
                sampleDroneMotion = self.__convertMotionToDroneFR(sampleMotion)
                droneRot, droneTrans = sampleDroneMotion

                frameList.append(np.arange(sStartFrame, sEndFrame+1))
                yawList.append(droneRot[:, 1])

            frameList = np.concatenate(frameList)
            yawList = np.concatenate(yawList)

            estHotpointAngle = 0
            for k in range(len(frameList)-1):
                area = (yawList[k] + yawList[k+1]) * (frameList[k+1] - frameList[k]) / 2
                estHotpointAngle += area
            estHotpointAngle = np.rad2deg(estHotpointAngle) 
            print('estAngle', estHotpointAngle)        

            if abs(estHotpointAngle) > self.threshold['waypointAngleTolerance']:
                print('angle too large', 'est=', estHotpointAngle)
                return False   
            
            print('pass!')  

        return True 


    def __checkWaypoint_backward(self, waypointFrameList_backward, waypointBackwardSampleDict, outputNameDict):
        print('CHECK waypoint (backward)')
        numWaypoint = len(waypointFrameList_backward)
        for i in range(numWaypoint):
            print('#%d' % i)
            print(waypointFrameList_backward[i])
            sampleIntervals = waypointBackwardSampleDict[i]
            print('sampling:', sampleIntervals)

            frameList = []
            yawList = []
            for sStartFrame, sEndFrame in sampleIntervals:
                # read rot and trans in camera FR
                parser = parseComputedMotion('./output/' + outputNameDict[(sStartFrame, sEndFrame)] + '.txt')
                sampleMotion = parser.parse()
                sampleDroneMotion = self.__convertMotionToDroneFR(sampleMotion)
                droneRot, droneTrans = sampleDroneMotion

                frameList.append(np.arange(sStartFrame, sEndFrame+1))
                yawList.append(droneRot[:, 1])

            frameList = np.concatenate(frameList)
            yawList = np.concatenate(yawList)
            
            estHotpointAngle = 0
            for k in range(len(frameList)-1):
                area = (yawList[k] + yawList[k+1]) * (frameList[k+1] - frameList[k]) / 2
                estHotpointAngle += area
            estHotpointAngle = np.rad2deg(estHotpointAngle)  
            print('estAngle', estHotpointAngle)       

            if abs(estHotpointAngle) > self.threshold['waypointAngleTolerance']:
                print('angle too large', 'est=', estHotpointAngle)
                return False        
   
            print('pass!')

        return True


    def __getVideoInfo(self):
        cap = cv2.VideoCapture('./videos/' + self.videoName + '.MP4') # MP4 format by default
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.FPS = cap.get(cv2.CAP_PROP_FPS)
        self.totalFrame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
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

            # guarantee we don't go to the timestamp after the video.
            endFramestamp = min(endFramestamp, self.totalFrame-1) # minus 1 because the frame range from 0 to totalFrame-1

            motionFrameList.append((startFramestamp, endFramestamp))
            
            if verbose: print('motion start end framestamp', startFramestamp, endFramestamp)  
        
        return motionFrameList

    
    def __cleanGapBetweenForwardAndBackward(self, waypointFrameList_forward, waypointFrameList_backward):
        assert len(waypointFrameList_forward) == len(waypointFrameList_backward)
        new_wp_forward, new_wp_backward = [], []
        for i in range(len(waypointFrameList_forward)):
            f_start, f_end = waypointFrameList_forward[i]
            b_start, b_end = waypointFrameList_backward[i]
            
            new_wp_forward.append((f_start, max(f_end, b_start-1)))
            new_wp_backward.append((b_start, b_end))
        
        return new_wp_forward, new_wp_backward


    # only consider the hotpoint prior to the last waypoint as the last
    def __getHotpointFrameListFromWaypointGap(self, waypointFrameList_forward, waypointFrameList_backward):
        hpFrameList = []
        hpFrameList_start, hpFrameList_end = [], []
        for wp_backward in waypointFrameList_backward[:-1]:
            _, end = wp_backward
            hpFrameList_start.append(end)

        for wp_forward in waypointFrameList_forward[1:]:
            start, _ = wp_forward
            hpFrameList_end.append(start)

        for start, end in zip(hpFrameList_start, hpFrameList_end):
            hpFrameList.append((start, end))

        return hpFrameList


    def __toFramestampWithSkip(self, timestamp):
        framestamp = ((timestamp - self.actualStartRecTime) / 1000 * self.FPS) / self.skipFrameNum
        return framestamp


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


    def __getSampleIntervals(self, interval, sampleNum, sampleLength=None, includeEndPoints=False):
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


    def __isHotpoint(self, droneMotion, isClockwise, verbose=False):
        rot, trans = droneMotion
        pitch, yaw, roll = rot[:, 0], rot[:, 1], rot[:, 2]
        X, Y, Z = trans[:, 2], trans[:, 0], trans[:, 1]

        # filter those samples with Y being unstable while yaw is close to 0
        Y_filtered = []
        for s_yaw, s_Y in zip(yaw, Y):
            if np.absolute(s_yaw) >= self.threshold['hotpointYaw'] * self.skipFrameNum:
                Y_filtered.append(s_Y)
        assert len(Y_filtered) > 0
        Y = np.array(Y_filtered)
        
        if not verifier.almostAll(np.absolute(Y) > self.threshold['hotpointY']):
            if verbose:  print('Y not satisfies threshold')
            return False

        if isClockwise == True:
            if not (verifier.almostAll(yaw > 0) and verifier.almostAll(Y < 0)):
                if verbose: print('+- not conforms to clockwise', verifier.almostAll(yaw > 0, threshold=0.6), verifier.almostAll(Y < 0, threshold=0.6))
                print(yaw)
                print(Y)
                return False
        else:
            if not (verifier.almostAll(yaw < 0) and verifier.almostAll(Y > 0)):
                if verbose: print('+- not conforms to clockwise', verifier.almostAll(yaw < 0, threshold=0.6), verifier.almostAll(Y > 0, threshold=0.6))
                return False

        return True


    def getRunningTime(self):
        return self.compression_time, self.opticalFlow_time, self.cameraMotion_time, (self.hpSampleNum, self.wpSampleNum)


    @staticmethod
    def almostAll(array, threshold=almostAllThreshold):
        # assume array is all True/False
        if np.sum(array) / len(array) >= threshold:
            return True
        else:
            return False



if __name__=='__main__':
    with open('threshold.json', 'r') as fin:
        threshold = json.load(fin)
    sampleParam = {'hotpointSampleLength': 1, 'hotpointSampleRate': 0.6, 'waypointSampleLength': 1, 'waypointMaxSampleNum': 5}
    compressParam_720p = {'resize': 4, 'skipFrames': 15}
    compressParam_4k = {'resize': 12, 'skipFrames': 15}

    # 720p
    data0403 = ('yawError2_DJI_0403__reduce_15__compressed_4', 'DJI_0403_corrected', program(((214, None), (57, False), (248, False))))
    data0410 = ('yawError2_DJI_0410__reduce_15__compressed_4', 'DJI_0410', program(((214, None), (57, False), (248, False))))
    data0411 = ('DJI_0411', 'DJI_0411', program(((173, None), (65, False), (205, True))))
    data0412 = ('DJI_0412', 'DJI_0412_corrected', program(((173, None), (65, False), (205, True))))

    data0404 = ('DJI_0404', 'DJI_0404_corrected', program(((43, None), (10, False), (179, False))))

    data0400 = ('DJI_0400', 'DJI_0400', program(((125, None), (39, False), (344, True))))
    data0402 = ('DJI_0402', 'DJI_0402', program(((56, None), (347, True), (183, False))))

    # 4k
    data0460 = ('yawError2_DJI_0460__reduce_15__compressed_12', 'DJI_0460_corrected', program(((333, None), (182, True), (22, True))))
    data0459 = ('yawError2_DJI_0459__reduce_15__compressed_12', 'DJI_0459_corrected', program(((50, None), (142, True), (249, False))))
    
    data0443 = ('yawError2_DJI_0443__reduce_15__compressed_12', 'DJI_0443', program(((63, None), (346, False), (128, False))))
    data0439 = ('yawError2_DJI_0439__reduce_15__compressed_12', 'DJI_0439', program(((125, None), (177, True), (114, False))))

    data0447 = ('DJI_0447', 'DJI_0447_corrected', program(((7, None), (217, True), (327, True))))

    data0494 = ('yawError2_DJI_0494__reduce_15__compressed_12', 'DJI_0494', program(((93, None), (321, True), (337, False), (228, True), (288, True))))
    data0495 = ('yawError2_DJI_0495__reduce_15__compressed_12', 'DJI_0495', program(((244, None), (173, False), (221, True), (311, True), (277, True))))
    data0496 = ('yawError2_DJI_0496__reduce_15__compressed_12', 'DJI_0496', program(((186, None), (53, False), (80, False), (137, False), (305, False))))

    data0488 = ('DJI_0488', 'DJI_0488', program(((286, None), (215, True), (310, True), (184, True), (59, False))))
    data0489 = ('yawError2_DJI_0489__reduce_15__compressed_12', 'DJI_0489', program(((78, None), (194, True), (272, True), (135, True), (315, False))))
    data0490 = ('yawError2_DJI_0490__reduce_15__compressed_12', 'DJI_0490', program(((307, None), (147, True), (77, False), (28, False), (220, False))))
    data0491 = ('yawError2_DJI_0491__reduce_15__compressed_12', 'DJI_0491', program(((267, None), (89, True), (143, True), (41, True), (301, True))))

    data0508 = ('DJI_0508', 'DJI_0508', program(((104, None), (289, True), (292, False), (114, False), (23, True))))
    data0504 = ('yawError2_DJI_0504__reduce_15__compressed_12', 'DJI_0504', program(((161, None), (29, True), (122, False), (249, True), (328, False))))

    # data0499 = ('DJI_0499', 'DJI_0499', program(((116, None), (153, False), (55, True), (330, True), (211, True)))) # 有问题
    data0498 = ('DJI_0498', 'DJI_0498', program(((176, None), (216, True), (240, False), (77, False), (4, True))))
    data0497 = ('DJI_0497', 'DJI_0497', program(((346, None), (80, True), (176, True), (196, False), (171, True))))

    data0502 = ('DJI_0502', 'DJI_0502', program(((174, None), (48, False), (94, True), (240, False), (34, False))))
    data0501 = ('DJI_0501', 'DJI_0501', program(((85, None), (53, False), (24, False), (56, False), (209, False))))
    data0500 = ('DJI_0500', 'DJI_0500', program(((32, None), (13, True), (197, False), (258, True), (42, False))))

    videoName, metadataName, plan = data0411
    compressParam = compressParam_720p
    matcher = verifier(videoName, metadataName, plan, threshold, sampleParam, compressParam)

    time_start=time.time()
    flag = matcher.verify(disableAutoCompression=False)   
    time_end=time.time()

    print('Final result:', flag)
    print('total time consumed:',time_end-time_start)   
    print('detailed running time:', matcher.getRunningTime()) 