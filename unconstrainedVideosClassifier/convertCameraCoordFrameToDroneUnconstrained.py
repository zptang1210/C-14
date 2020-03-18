import math
import numpy as np
import matplotlib.pyplot as plt


class convertCameraCoordFrameToDrone(object):

    def __init__(self, ori, translation):
        self.rotationABC = ori
        self.translationXYZ = translation

    def convert(self, droneCameraAngle, plot=False):
        # From camera FR to drone FR (rotationABC)
        # print('####')
        # print(droneCameraAngle)
        # print([a[0] for a in self.rotationABC])
        R_camera_drone = []
        for angle in droneCameraAngle:
            # EA_camera_drone = np.array([math.radians(angle), 0, 0])  # Euler angle
            EA_camera_drone = np.array([angle, 0, 0])  # Euler angle
            R_camera_drone.append(self.__convertEulerAngleToRotationMatrix(EA_camera_drone))

        convertedRotationABCInDroneFR = np.zeros(self.rotationABC.shape)
        frameNum = 0
        endFrameNum = self.rotationABC.shape[0]
        while frameNum < endFrameNum:
            EA_camera1_camera2 = self.rotationABC[frameNum]
            R_camera1_camera2 = self.__convertEulerAngleToRotationMatrix(EA_camera1_camera2)

            R_drone1_drone2 = np.linalg.inv(R_camera_drone[frameNum]) @ R_camera1_camera2 @ R_camera_drone[frameNum]
            #R_drone1_drone2 = np.linalg.inv(R_camera_drone[frameNum]) @ R_camera1_camera2 @ R_camera_drone[frameNum+1]
            #print(R_camera_drone[frameNum], R_camera_drone[frameNum+1])
            EA_drone1_drone2 = self.__convertRotationMatrixToEulerAngle(R_drone1_drone2)

            convertedRotationABCInDroneFR[frameNum] = EA_drone1_drone2

            frameNum += 1

        droneTranslation = []
        # From camera FR to drone FR (translationXYZ)
        #for i, R_camera in enumerate(R_camera_drone):
        for i, _ in enumerate(self.translationXYZ):
            R_camera_Transposed = R_camera_drone[i].T
            droneTranslation.append((R_camera_Transposed @ (self.translationXYZ[i]).T).T)
        droneTranslation = np.array(droneTranslation)
        # print(droneTranslation.shape)

        if plot == True:

            verts = [0, 585, 915, 1450, 1934, 2271, 2766, 2943, 3175, 3345, 3521, 3613, 4712, ]

            plt.figure('Relative Rotation in Drone Frame of Reference')
            plt.subplot(311)

            for vert in verts:
                plt.axvline(x=vert)
            plt.plot(convertedRotationABCInDroneFR[:, 0], label='A-pitch')
            plt.plot(convertedRotationABCInDroneFR[:, 1], label='B-yaw')
            plt.plot(convertedRotationABCInDroneFR[:, 2], label='C-roll')
            plt.ylim(-.006, .006)
            # plt.xlim(1270, 1300)
            plt.legend()
            plt.xlabel('time (in frames)')
            plt.ylabel('rotation (in grad/frames)')
            # plt.show()

            # plt.figure('Relative Translation in Drone Frame of Reference')
            plt.subplot(312)

            for vert in verts:
                plt.axvline(x=vert)
            # print(len(droneTranslation[:, 2]))
            plt.plot(droneTranslation[:, 2], label='X')
            plt.plot(droneTranslation[:, 0], label='Y')
            plt.plot(droneTranslation[:, 1], label='Z')
            plt.ylim(-1.1, 1.1)
            plt.legend()
            plt.xlabel('time')
            plt.ylabel('translation')
            # plt.show()

            plt.subplot(313)

            for vert in verts:
                plt.axvline(x=vert)

            plt.plot(droneCameraAngle, label='droneCameraAngle')
            plt.legend()
            plt.xlabel('time')
            plt.ylabel('droneCameraAngle')
            plt.show()

        return convertedRotationABCInDroneFR, droneTranslation

    def __convertEulerAngleToRotationMatrix(self, ea):  # in radins
        alpha, beta, gamma = ea
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
        # print(beta)
        alpha = np.arcsin(R[2, 1] / np.cos(beta))
        gamma = np.arcsin(R[1, 0] / np.cos(beta))
        return np.array([alpha, beta, gamma])


if __name__ == '__main__':
    from parseComputedMotion import *
    from convertKMLToCameraCoord import convertKMLToCameraCoord

    parser = parseComputedMotion(
        '/Users/fabien/Documents/amherst/fall19/cs696/code/droneCAPTCHA/temp/real_processed.txt')
    frame, ori, translation = parser.parse()

    plt.subplot(211)
    plt.plot(ori[:, 1], label="yaw")
    plt.ylabel('Yaw (in grad/frame)')
    plt.xlim(1280, 1290)

    plt.ylim(-.005, .0025)
    plt.legend()

    plt.subplot(212)
    plt.plot(translation[:, 0], label="y")
    plt.xlim(1280, 1290)
    plt.ylabel('y')
    # plt.ylim(-.4, .01)
    plt.xlabel('time (in frames)')
    plt.legend()
    plt.show()
    exit()

    n_frames = len(frame)

    _, _, droneCameraAngle = convertKMLToCameraCoord(
        '/Users/fabien/Documents/amherst/fall19/cs696/litchi_missions/Sunrise in Waterbury_65.kml')

    droneCameraAngle = droneCameraAngle[220:]
    droneCameraAngle = np.interp(
        np.arange(0, len(droneCameraAngle), len(droneCameraAngle) / n_frames),
        np.arange(0, len(droneCameraAngle)),
        droneCameraAngle).tolist()

    # for i in range(len(droneCameraAngle)):
    #    droneCameraAngle[i] = math.pi/2

    # droneCameraAngle = [10] * converter.rotationABC.shape[0]  # degrees

    # from convertKMLToCameraCoord import convertKMLToCameraCoord

    # print('Get camera coord ')
    # print(droneCameraAngle)
    # ori = np.array(ori).transpose((1, 0))
    # translation = np.array(translation).transpose((1, 0))

    converter = convertCameraCoordFrameToDrone(ori, translation)
    print('Camera to drone')

    droneOri, droneTranslation = converter.convert(droneCameraAngle, plot=True)
