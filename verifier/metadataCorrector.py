import sys
import math
import numpy as np
import pwlf
# import matplotlib.pyplot as plt
sys.path.append('../utils')
from command import command
from parseMetadata import parseMetadata

almostAllThreshold = 1

class metadataCorrector(object):

    def __init__(self, rawInfo):
        self.motionClass, self.recordVideoTime, self.hotpointActionTimeList, self.waypointActionTimeList, cmdList = rawInfo
        self.hotpointCmdList, self.waypointCmdList = cmdList


    def correctTimestamp(self):
        startVideoTime, endVideoTime = self.recordVideoTime
        actualStartRecTime = endVideoTime

        # 读取metadata在开始时间之后的数据
        # 转换成ideal drone coordinate system
        # 一个一个的纠正

        numHotpoint = len(self.hotpointActionTimeList)
        correctedHotpointTimeList = []
        correctedHotpointTimeLengthList = []
        for i in range(numHotpoint):
            realMotion_NED = self.__extractRealMotionInWorldFR(self.hotpointCmdList[i])
            realMotion_drone = self.__convertMotionToDroneFR(realMotion_NED)
            correctedHotpointTime = self.__getCorrectedHotpointTimeLabel(realMotion_drone, self.hotpointActionTimeList[i], verbose=False)
            correctedHotpointTimeLength = self.__getCorrectedHotpointTimeLength(realMotion_drone, self.hotpointActionTimeList[i])
            correctedHotpointTimeList.append(correctedHotpointTime)
            correctedHotpointTimeLengthList.append(correctedHotpointTimeLength)

        numWaypoint = len(self.waypointActionTimeList)
        waypointTimeList_forward, waypointTimeList_backward = [], []
        for i in range(numWaypoint):
            realMotion_NED = self.__extractRealMotionInWorldFR(self.waypointCmdList[i])
            realMotion_drone = self.__convertMotionToDroneFR(realMotion_NED)
            waypointTime_forward, waypointTime_backward = self.__getCorrectedWaypointTimeLabel(realMotion_drone, self.waypointActionTimeList[i], verbose=False)
            waypointTimeList_forward.append(waypointTime_forward)
            waypointTimeList_backward.append(waypointTime_backward)
        
        return correctedHotpointTimeList, (waypointTimeList_forward, waypointTimeList_backward), correctedHotpointTimeLengthList

    
    # def __extractRealMotionInWorldFR(self, cmd):
    #     rawMotion = cmd.interStatus
    #     oldInfo = [''] * 9
    #     timestamp_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list = [], [], [], [], [], [], []
    #     for rawStr in rawMotion:
    #         splittedStr = rawStr.split(' ')
    #         timestamp = int(splittedStr[0])
    #         info = splittedStr[1].split(',')
    #         [lat_str, lon_str, alt_str, pit_str, rol_str, yaw_str,
    #          vx_str, vy_str, vz_str] = info

    #         if info != oldInfo: # delete repeated terms
    #             timestamp_list.append(timestamp)
    #             roll_NED_list.append(self.__convertToStandardAngleMeasurement(float(rol_str)))
    #             pitch_NED_list.append(self.__convertToStandardAngleMeasurement(float(pit_str)))
    #             yaw_NED_list.append(self.__convertToStandardAngleMeasurement(float(yaw_str)))
    #             vx_NED_list.append(float(vx_str))
    #             vy_NED_list.append(float(vy_str))
    #             vz_NED_list.append(float(vz_str))
    #             oldInfo = info 

    #     realMotion_NED = timestamp_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list
    #     return realMotion_NED


    def __extractRealMotionInWorldFR(self, cmd):
        rawMotion = cmd.interStatus
        timestamp_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list = [], [], [], [], [], [], []
        for rawStr in rawMotion:
            splittedStr = rawStr.split(' ')
            timestamp = int(splittedStr[0])
            info = splittedStr[1].split(',')

            [lat_str, lon_str, alt_str, pit_str, rol_str, yaw_str,
             vx_str, vy_str, vz_str] = info

            timestamp_list.append(timestamp)
            roll_NED_list.append(self.__convertToStandardAngleMeasurement(float(rol_str)))
            pitch_NED_list.append(self.__convertToStandardAngleMeasurement(float(pit_str)))
            yaw_NED_list.append(self.__convertToStandardAngleMeasurement(float(yaw_str)))
            vx_NED_list.append(float(vx_str))
            vy_NED_list.append(float(vy_str))
            vz_NED_list.append(float(vz_str))

        realMotion_NED = timestamp_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list
        return realMotion_NED
    
    
    def __convertMotionToDroneFR(self, realMotion_NED):
        # XYZ
        v_drone_norm_tuple, droneFR_axes_info = self.__convertXYZToDroneFR(realMotion_NED, plot=False)
        vx_drone_norm_list, vy_drone_norm_list, vz_drone_norm_list = v_drone_norm_tuple

        # RPY
        roll_drone_list, pitch_drone_list, yaw_drone_list = self.__convertRPYToDroneFR(realMotion_NED, droneFR_axes_info, plot=False)

        timestamp_list, _, _, _, _, _, _ = realMotion_NED
        realMotion_drone = timestamp_list, roll_drone_list, pitch_drone_list, yaw_drone_list, vx_drone_norm_list, vy_drone_norm_list, vz_drone_norm_list
        return realMotion_drone


    def __convertXYZToDroneFR(self, realMotion_NED, plot=False):
        timestamp, pitch, roll, yaw, vx, vy, vz = realMotion_NED

        listLen = len(timestamp)
        v_drone_norm_list, x_axis_drone_list, y_axis_drone_list, z_axis_drone_list = [], [], [], []
        for i in range(listLen):
            # R is R_NED_drone
            R = metadataCorrector.convertEulerAngleToRotationMatrix(roll[i], pitch[i], yaw[i])

            # velocity in the world FR
            v_NED = np.array([vx[i], vy[i], vz[i]])          

            # x, y, and z-axis of NED in the world (NED) FR before rotation
            x_axis_NED = np.array([1, 0, 0])
            y_axis_NED = np.array([0, 1, 0])
            z_axis_NED = np.array([0, 0, 1])

            # x, y, and z-axis of drone in the world (NED) FR after rotation
            x_axis_drone = R @ x_axis_NED
            y_axis_drone = R @ y_axis_NED
            z_axis_drone = R @ z_axis_NED

            # velocity in the drone FR
            v_drone = R.T @ v_NED
            v_drone_norm = metadataCorrector.normalizeVector(v_drone)

            v_drone_norm_list.append(v_drone_norm)
            x_axis_drone_list.append(x_axis_drone)
            y_axis_drone_list.append(y_axis_drone)
            z_axis_drone_list.append(z_axis_drone)

        # convert to numpy array
        v_drone_norm_list = np.array(v_drone_norm_list)
        vx_drone_norm_list, vy_drone_norm_list, vz_drone_norm_list = v_drone_norm_list[:, 0], v_drone_norm_list[:, 1], v_drone_norm_list[:, 2]
        x_axis_drone_list = np.array(x_axis_drone_list)
        y_axis_drone_list = np.array(y_axis_drone_list)
        z_axis_drone_list = np.array(z_axis_drone_list)
        droneFR_axes_info = (x_axis_drone_list, y_axis_drone_list, z_axis_drone_list)

        if plot==True:
            framestamp = [self.toFrame(time) for time in timestamp]
            # plt.figure('vx, vy, vz in camera frame with normalization from metadata')
            # plt.plot(framestamp, v_drone_norm_list[:, 0], label='x')
            # plt.plot(framestamp, v_drone_norm_list[:, 1], label='y')
            # plt.plot(framestamp, v_drone_norm_list[:, 2], label='z')
            # plt.legend()
            # plt.show()   
 
        return (vx_drone_norm_list, vy_drone_norm_list, vz_drone_norm_list), droneFR_axes_info       


    def __convertRPYToDroneFR(self, realMotion_NED, droneFR_axes_info, plot=False):
        timestamp, _, _, _, _, _, _ = realMotion_NED
        x_axis_drone_list, y_axis_drone_list, z_axis_drone_list = droneFR_axes_info

        listLen = len(x_axis_drone_list)
        roll_drone_list, pitch_drone_list, yaw_drone_list = [], [], []
        for i in range(listLen-1):
            x1_axis_drone = x_axis_drone_list[i]
            y1_axis_drone = y_axis_drone_list[i]
            z1_axis_drone = z_axis_drone_list[i]
            R_w_d1 = np.vstack((x1_axis_drone, y1_axis_drone, z1_axis_drone)).T

            x2_axis_drone = x_axis_drone_list[i+1]
            y2_axis_drone = y_axis_drone_list[i+1]
            z2_axis_drone = z_axis_drone_list[i+1]
            R_w_d2 = np.vstack((x2_axis_drone, y2_axis_drone, z2_axis_drone)).T   

            R_d1_d2 = np.linalg.inv(R_w_d1) @ R_w_d2

            roll, pitch, yaw = metadataCorrector.convertRotationMatrixToEulerAngle(R_d1_d2)
            roll_drone_list.append(roll)
            pitch_drone_list.append(pitch)
            yaw_drone_list.append(yaw)

        if plot==True:
            framestamp = [self.toFrame(time) for time in timestamp]
            yaw_rate_drone_list = [yaw_drone_list[i]/(framestamp[i+1] - framestamp[i]) for i in range(listLen-1)]
            pitch_rate_drone_list = [pitch_drone_list[i]/(framestamp[i+1] - framestamp[i]) for i in range(listLen-1)]
            roll_rate_drone_list = [roll_drone_list[i]/(framestamp[i+1] - framestamp[i]) for i in range(listLen-1)]
            yaw_rate_drone_list = np.array(yaw_rate_drone_list)
            pitch_rate_drone_list = np.array(pitch_rate_drone_list)
            roll_rate_drone_list = np.array(roll_rate_drone_list)

            # plt.figure('rpy rate in camera frame from metadata')
            # plt.plot(framestamp[:-1], pitch_rate_drone_list, label='pitch rate')
            # plt.plot(framestamp[:-1], yaw_rate_drone_list, label='yaw rate')
            # plt.plot(framestamp[:-1], roll_rate_drone_list, label='roll rate')
            # plt.legend()
            # plt.show()

        return roll_drone_list, pitch_drone_list, yaw_drone_list


    def __getCorrectedHotpointTimeLength(self, realMotion_drone, hotpointTimeLabel):
        # 找出hotpoint开始从0增长的时间戳，到hotpoint开始下降的时间长度
        timestamp, roll, pitch, yaw, vx, vy, vz = realMotion_drone 
        
        idx = metadataCorrector.findFirstStableStatus(vy, (lambda x: x>0.1 or x<-0.1), windowSize=10)
        # print(idx, self.toFrame(timestamp[idx]))
        if idx==None: raise Exception('Invalid Hotpoint data!')

        return hotpointTimeLabel[1] - timestamp[idx]        


    def __getCorrectedHotpointTimeLabel(self, realMotion_drone, hotpointTimeLabel, verbose=False):
        # 先将Y变得接近1的时间点提出来
        # 然后将yaw的信号平滑并拟合，并找到数据开始稳定的时间点
        timestamp, roll, pitch, yaw, vx, vy, vz = realMotion_drone

        idx = metadataCorrector.findFirstStableStatus(vy, (lambda x: x>0.9 or x<-0.9), windowSize=10)
        # print(idx, self.toFrame(timestamp[idx]))
        if idx==None: raise Exception('Invalid Hotpoint data!')

        oriSlopes, fitBreaks = self.__fitArray(timestamp[idx:-1], yaw[idx:], lineNum=2, visualize=False) # timestamp's length is larger than rpy by 1!
        flatAreaSlope = oriSlopes[1]
        flatAreaStartTimestamp = math.ceil(fitBreaks[1])

        correctedHotpointTimeLabel = (flatAreaStartTimestamp, hotpointTimeLabel[1])
        if verbose: print(self.toFrame(flatAreaStartTimestamp), self.toFrame(hotpointTimeLabel[1]))

        return correctedHotpointTimeLabel
        
    
    def __fitArray(self, timestamp, array, lineNum=2, visualize=True):
        my_pwlf = pwlf.PiecewiseLinFit(timestamp, array)        
        fit_breaks = my_pwlf.fit(lineNum)
        slopes = my_pwlf.calc_slopes()

        if visualize:
            print('fit_breaks', fit_breaks)
            print('slopes', slopes)

            xHat = np.linspace(min(timestamp), max(timestamp), num=10000)
            yHat = my_pwlf.predict(xHat)

            # # plot the results
            # plt.figure()
            # plt.plot([self.toFrame(x) for x in timestamp], array, 'black')
            # plt.plot([self.toFrame(x) for x in xHat], yHat, 'red', linewidth=3)
            # plt.show()                   

        return slopes, fit_breaks    


    def __getCorrectedWaypointTimeLabel(self, realMotion_drone, waypointTimeLabel, verbose=False):
        timestamp, roll, pitch, yaw, vx, vy, vz = realMotion_drone

        startForwardIdx = metadataCorrector.findFirstStableStatus(vx, (lambda x: x>0.8), windowSize=9)
        if verbose: print('startForward', startForwardIdx, self.toFrame(timestamp[startForwardIdx]))

        startBackwardIdx = metadataCorrector.findFirstStableStatus(vx, (lambda x: x<-0.8), windowSize=9)
        if verbose: print('startBackward', startBackwardIdx, self.toFrame(timestamp[startBackwardIdx]))

        endBackwardIdx_reversed = metadataCorrector.findFirstStableStatus(np.flip(vx), (lambda x: x<-0.8), windowSize=9)
        endBackwardIdx = len(vx) - endBackwardIdx_reversed - 1 
        if verbose: print('endBackward', endBackwardIdx, self.toFrame(timestamp[endBackwardIdx]))

        endForwardIdx_reversed = metadataCorrector.findFirstStableStatus(np.flip(vx[:startBackwardIdx]), (lambda x: x>0.8), windowSize=9)
        endForwardIdx = startBackwardIdx - endForwardIdx_reversed - 1
        if verbose: print('endForwardIdx', endForwardIdx, self.toFrame(timestamp[endForwardIdx]))

        waypointTimeLabel_forward = (timestamp[startForwardIdx], timestamp[endForwardIdx])
        waypointTimeLabel_backward = (timestamp[startBackwardIdx], timestamp[endBackwardIdx])

        return waypointTimeLabel_forward, waypointTimeLabel_backward

    
    def __convertToStandardAngleMeasurement(self, angle):
        return math.radians(360+angle if angle<0 else angle)

    
    def toFrame(self, time, FPS=30):
        startVideoTime, endVideoTime = self.recordVideoTime
        actualStartRecTime = endVideoTime

        frame = (time - actualStartRecTime) / 1000 * FPS
        return frame   


    @staticmethod
    def normalizeVector(v):
        v_length = np.linalg.norm(v)
        if v_length>0:
            v_norm = v / v_length
        else:
            v_norm = np.array([0, 0, 0])     

        return v_norm

    
    @staticmethod
    def findFirstStableStatus(array, compareFunc, windowSize=10):
        i = 0
        while i+windowSize<=len(array):
            window = array[i:i+windowSize]
            windowBoolean = [compareFunc(k) for k in window]
            if metadataCorrector.almostAll(windowBoolean):
                return i
            i+=1
        
        return None


    @staticmethod
    def convertRotationMatrixToEulerAngle(R):
        beta = np.arcsin(-R[2, 0])
        gamma = np.arcsin(R[2, 1] / np.cos(beta))
        alpha = np.arcsin(R[1, 0] / np.cos(beta))
        return np.array([gamma, beta, alpha])  


    @staticmethod
    def convertEulerAngleToRotationMatrix(roll, pitch, yaw):
        cos, sin = np.cos, np.sin
        alpha, beta, gamma = yaw, pitch, roll
        Rx = np.array([[1, 0, 0], [0, cos(gamma), -sin(gamma)], [0, sin(gamma), cos(gamma)]])
        Ry = np.array([[cos(beta), 0, sin(beta)], [0, 1, 0], [-sin(beta), 0, cos(beta)]])
        Rz = np.array([[cos(alpha), -sin(alpha), 0], [sin(alpha), cos(alpha), 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        return R       


    @staticmethod
    def almostAll(array, threshold=almostAllThreshold):
        # assume array is all True/False
        if np.sum(array) / len(array) >= threshold:
            return True
        else:
            return False


if __name__ == '__main__':
    # parse metadata
    metadataFilePath = '0172.metadata'
    metadataParser = parseMetadata(metadataFilePath)
    rawInfo = metadataParser.parse()

    corrector = metadataCorrector(rawInfo)
    result = corrector.correctTimestamp()

    print(result)
    
