import math
import numpy as np
# import matplotlib.pyplot as plt

class convertCameraCoordFrameToDrone(object):

    def __init__(self, ori, translation):
        self.rotationABC = ori
        self.translationXYZ = translation
    

    def convert(self, droneCameraAngle, plot=False):
        # From camera FR to drone FR (rotationABC)
        EA_camera_drone = np.array([math.radians(droneCameraAngle), 0, 0]) # Euler angle
        R_camera_drone = self.__convertEulerAngleToRotationMatrix(EA_camera_drone)
        
        convertedRotationABCInDroneFR = np.zeros(self.rotationABC.shape)
        frameNum = 0
        endFrameNum = self.rotationABC.shape[0]
        while frameNum < endFrameNum:
            EA_camera1_camera2 = self.rotationABC[frameNum]
            R_camera1_camera2 = self.__convertEulerAngleToRotationMatrix(EA_camera1_camera2)

            R_drone1_drone2 = np.linalg.inv(R_camera_drone) @ R_camera1_camera2 @ R_camera_drone
            EA_drone1_drone2 = self.__convertRotationMatrixToEulerAngle(R_drone1_drone2)

            convertedRotationABCInDroneFR[frameNum] = EA_drone1_drone2

            frameNum += 1

        # From camera FR to drone FR (translationXYZ)
        R_drone_camera = R_camera_drone.T
        droneTranslation = (R_drone_camera @ (self.translationXYZ).T).T
        
        if plot==True:
            plt.figure('Relative Rotation in Drone Frame of Reference')
            plt.subplot(211)
            plt.plot(convertedRotationABCInDroneFR[:, 0], label='A-pitch')
            plt.plot(convertedRotationABCInDroneFR[:, 1], label='B-yaw')
            plt.plot(convertedRotationABCInDroneFR[:, 2], label='C-roll')
            plt.legend()
            plt.xlabel('time')
            plt.ylabel('rotation')
            # plt.show()   

            # plt.figure('Relative Translation in Drone Frame of Reference')
            plt.subplot(212)
            plt.plot(droneTranslation[:, 2], label='X')
            plt.plot(droneTranslation[:, 0], label='Y')
            plt.plot(droneTranslation[:, 1], label='Z')
            plt.legend()
            plt.xlabel('time')
            plt.ylabel('translation')
            plt.show()           
        
        return convertedRotationABCInDroneFR, droneTranslation


    def __convertEulerAngleToRotationMatrix(self, ea): # in radins
        alpha, beta, gamma  = ea
        R_x = np.array([[1, 0, 0], 
                        [0, np.cos(alpha), -np.sin(alpha)],
                        [0, np.sin(alpha), np.cos(alpha)]])
        R_y = np.array([[np.cos(beta), 0, np.sin(beta)], 
                        [0, 1, 0],
                        [-np.sin(beta), 0, np.cos(beta)]])
        R_z = np.array([[np.cos(gamma), -np.sin(gamma), 0], 
                        [np.sin(gamma), np.cos(gamma), 0],
                        [0, 0, 1]])
        return R_z @ R_y @ R_x


    def __convertRotationMatrixToEulerAngle(self, R):
        beta = np.arcsin(-R[2, 0])
        alpha = np.arcsin(R[2, 1] / np.cos(beta))
        gamma = np.arcsin(R[1, 0] / np.cos(beta))
        return np.array([alpha, beta, gamma])


if __name__=='__main__':
    droneCameraAngle = 50  #degrees

    from parseComputedMotion import *
    parser = parseComputedMotion('DJI_0179-0.82.txt')
    ori, translation = parser.parse()  

    converter = convertCameraCoordFrameToDrone(ori, translation)
    droneOri, droneTranslation = converter.convert(droneCameraAngle, plot=True)

    print(droneOri)
    print(droneTranslation)