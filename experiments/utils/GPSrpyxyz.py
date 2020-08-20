import math
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import animation

sys.path.append('../../utils/')
from parseMetadata import parseMetadata
from parseComputedMotion import *
from convertCameraCoordFrameToDrone import *


def extractGPSInfo(metadataFilePath):
    with open(metadataFilePath, 'r') as fid:
        txt = fid.readlines()

    # direcrtly print the lines not starting with numerical character
    # print(txt[0])
    i = 1
    while txt[i][0].isdigit() == False:
        # print(txt[i])
        i += 1

    # process record
    info = []
    while i < len(txt):
        splittedTxt = txt[i].split(' ')
        timestamp = int(splittedTxt[0])
        data_str = "".join(splittedTxt[1:])

        data_list = data_str.split(',')
        if data_list[0][0].isalpha():
            # print(i, '-', txt[i])
            pass
        else:
            [lat_str, lon_str, alt_str, pit_str, rol_str, yaw_str,
             vx_str, vy_str, vz_str] = data_str.split(',')
            latitude = float(lat_str)
            longitude = float(lon_str)
            altitude = float(alt_str)
            pitch = float(pit_str)
            roll = float(rol_str)
            yaw = float(yaw_str)
            vx = float(vx_str)
            vy = float(vy_str)
            vz = float(vz_str)
            info.append((timestamp, None, latitude, longitude, altitude,
                         pitch, roll, yaw, vx, vy, vz))

        i += 1

    return info


def extractPitchRollYawXYZ(info):
    timestamp_list, pitch_list, roll_list, yaw_list, vx_list, vy_list, vz_list = [], [], [], [], [], [], []
    for item in info:
        time, pitch, roll, yaw, vx, vy, vz = item[0], item[5], item[6], item[7], item[8], item[9], item[10]
        timestamp_list.append(time)
        pitch_list.append(pitch)
        roll_list.append(roll)
        yaw_list.append(yaw)
        vx_list.append(vx)
        vy_list.append(vy)
        vz_list.append(vz)

    return timestamp_list, pitch_list, roll_list, yaw_list, vx_list, vy_list, vz_list


def plotRollPitchYaw(framestamp, timeFrameDict, pitch_diff, roll_diff, yaw_diff):
    plt.figure()
    horizontal_axis = framestamp[1:]
    for i in range(len(horizontal_axis)):
        if horizontal_axis[i] >= 0:
            start = i
            break

    pitch_diff_rate = [pitch_diff[i] / (framestamp[i + 1] - framestamp[i]) for i in range(len(pitch_diff))]
    yaw_diff_rate = [yaw_diff[i] / (framestamp[i + 1] - framestamp[i]) for i in range(len(yaw_diff))]
    roll_diff_rate = [roll_diff[i] / (framestamp[i + 1] - framestamp[i]) for i in range(len(roll_diff))]

    angle_diff = pitch_diff
    angle_diff_rate = pitch_diff_rate
    frameTimeDict = {value: key for key, value in timeFrameDict.items()}
    for i in range(start, len(framestamp)):
        print(framestamp[i], frameTimeDict[framestamp[i]], angle_diff_rate[i - 1], angle_diff[i - 1])

    # plt.plot(horizontal_axis[start:], pitch_diff_rate[start:], label='pitch')
    # plt.plot(horizontal_axis[start:], yaw_diff_rate[start:], label='yaw')
    plt.plot(horizontal_axis[start:], roll_diff_rate[start:], label='roll')
    plt.legend()
    plt.xlabel('time')
    plt.ylabel('angle')
    plt.show()


def toFrame(recordVideoTime, time):
    startVideoTime, endVideoTime = recordVideoTime
    estStartRecordingTime = endVideoTime
    correction = 0
    FPS = 30

    return (time - estStartRecordingTime) / 1000 * FPS + correction


def timestampToFramestamp(metadataFilePath, timestamp):
    parser = parseMetadata(metadataFilePath)
    motionClass, recordVideoTime, hotPointActionTimeList, waypointActionTimeList, _ = parser.parse()

    framestamp = []
    timeFrameDict = dict()
    for t in timestamp:
        frameNo = toFrame(recordVideoTime, t)
        framestamp.append(frameNo)
        timeFrameDict[t] = frameNo

    return framestamp, timeFrameDict


def extractLatLong(info):
    x, y = [], []
    for item in info:
        latitude, longtitude = item[2], item[3]
        x.append(latitude)
        y.append(longtitude)
    return x, y


def plotTrace2D(info):
    x, y = extractLatLong(info)
    # plt.axis('equal')
    plt.figure(figsize=(9, 9))
    plt.plot(y, x, c='black')
    plt.show()


def plotTraceAnimation(info):
    x, y = extractLatLong(info)

    fig = plt.figure(figsize=(9, 9))
    line, = plt.plot(y, x, c='blue')
    point, = plt.plot([y[0], y[1]], [x[0], x[1]], c='red', linewidth=8)

    def update(timestamp):
        # print(timestamp)
        line.set_data((y[:timestamp + 1], x[:timestamp + 1]))
        point.set_data((y[timestamp:timestamp + 2], x[timestamp:timestamp + 2]))
        return line, point

    ani = animation.FuncAnimation(fig=fig, func=update, frames=len(x),
                                  interval=30, blit=True)
    plt.show()


def convertToStandardMeasurement(angles):
    std_angles = []
    for angle in angles:
        std_angles.append(360 + angle if angle < 0 else angle)

    return std_angles


def convertXYZToBodyFrame(framestamp, pitch, roll, yaw, vx, vy, vz, plot=False):
    std_pitch = convertToStandardMeasurement(pitch)
    std_roll = convertToStandardMeasurement(roll)
    std_yaw = convertToStandardMeasurement(yaw)
    # std_pitch, std_roll, std_yaw = pitch, roll, yaw

    cos = np.cos
    sin = np.sin

    # in world coord sys
    v_world_list = []
    v_world_norm_list = []
    x_axis_rotate_list = []
    y_axis_rotate_list = []
    z_axis_rotate_list = []
    # in body coord sys
    v_body_list = []

    for i in range(len(vx)):
        alpha = math.radians(std_yaw[i])
        beta = math.radians(std_pitch[i])
        gamma = math.radians(std_roll[i])

        Rx = np.array([[1, 0, 0], [0, cos(gamma), -sin(gamma)], [0, sin(gamma), cos(gamma)]])
        Ry = np.array([[cos(beta), 0, sin(beta)], [0, 1, 0], [-sin(beta), 0, cos(beta)]])
        Rz = np.array([[cos(alpha), -sin(alpha), 0], [sin(alpha), cos(alpha), 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        # R = Ry @ Rx @ Rz # not the order in the book, just for test

        v_world = np.array([vx[i], vy[i], vz[i]])
        length = np.linalg.norm(v_world)
        if length > 0:
            v_world_norm = v_world / length
        else:
            v_world_norm = np.array([0, 0, 0])

        x_axis_init = np.array([1, 0, 0])
        y_axis_init = np.array([0, 1, 0])
        z_axis_init = np.array([0, 0, 1])

        x_axis_rotate = R @ x_axis_init
        y_axis_rotate = R @ y_axis_init
        z_axis_rotate = R @ z_axis_init

        # # sanity check
        # print(R, x_axis_rotate, y_axis_rotate, z_axis_rotate)
        # print(R.T @ z_axis_rotate)

        v_body = R.T @ v_world
        # print(v_body)
        v_body_list.append(v_body)

        v_world_list.append(v_world)
        v_world_norm_list.append(v_world_norm)
        x_axis_rotate_list.append(x_axis_rotate)
        y_axis_rotate_list.append(y_axis_rotate)
        z_axis_rotate_list.append(z_axis_rotate)
        # print('v_world', v_world)
        # print('v_world_norm', v_world_norm)

        # # Used for dubug
        # if framestamp[i]>=760 and framestamp[i]<=820:
        #     print('check hotpoint', framestamp[i])
        #     print(' aircraft pose', std_yaw[i], std_pitch[i], std_roll[i])
        #     print(' aircraft pose axis')
        #     print(' ', x_axis_rotate)
        #     print(' ', y_axis_rotate)
        #     print(' ', z_axis_rotate)
        #     print(' v_world', v_world)
        #     print(' v_body', v_body)
        #     print(R)
        #     print(' transform back', R@ v_body)

    if plot == True:
        for i in range(len(framestamp)):
            if framestamp[i] >= 0:
                start = i
                break

        v_world_list = np.array(v_world_list)
        plt.figure('velocity based on world frame from metadata')
        plt.plot(framestamp[start:], v_world_list[start:, 0], label='x')
        plt.plot(framestamp[start:], v_world_list[start:, 1], label='y')
        plt.plot(framestamp[start:], v_world_list[start:, 2], label='z')
        plt.legend()
        # plt.show()

        v_world_norm_list = np.array(v_world_norm_list)
        plt.figure('velocity based on world frame with normalization from metadata')
        plt.plot(framestamp[start:], v_world_norm_list[start:, 0], label='x')
        plt.plot(framestamp[start:], v_world_norm_list[start:, 1], label='y')
        plt.plot(framestamp[start:], v_world_norm_list[start:, 2], label='z')
        plt.legend()
        # plt.show()

        x_axis_rotate_list = np.array(x_axis_rotate_list)
        plt.figure('x-axis of body frame from metadata')
        plt.plot(framestamp[start:], x_axis_rotate_list[start:, 0], label='x')
        plt.plot(framestamp[start:], x_axis_rotate_list[start:, 1], label='y')
        plt.plot(framestamp[start:], x_axis_rotate_list[start:, 2], label='z')
        plt.legend()
        # plt.show()

        v_body_list = np.array(v_body_list)
        plt.figure('velocity based on body frame from metadata')
        plt.plot(framestamp[start:], v_body_list[start:, 0], label='x')
        plt.plot(framestamp[start:], v_body_list[start:, 1], label='y')
        plt.plot(framestamp[start:], v_body_list[start:, 2], label='z')
        plt.legend()
        plt.show()

    return v_world_list, v_body_list, x_axis_rotate_list, y_axis_rotate_list, z_axis_rotate_list


def convertXYZFromBodyToCamera(framestamp, angle, v_world_list, x_axis_body_list, y_axis_body_list, z_axis_body_list,
                               plot=False, returnVelocity=False):
    v_camera_list = []
    v_camera_norm_list = []
    x_axis_camera_list = []
    y_axis_camera_list = []
    z_axis_camera_list = []

    for i in range(len(framestamp)):
        x_axis_body = x_axis_body_list[i]
        y_axis_body = y_axis_body_list[i]
        z_axis_body = z_axis_body_list[i]
        v_world = v_world_list[i]

        # first project x_axis_body to the ground, and then project it to the camera's forward direction
        x_axis_groundproj = np.array([x_axis_body[0], x_axis_body[1], 0])
        x_axis_camera = np.array([x_axis_groundproj[0], x_axis_groundproj[1],
                                  math.tan(math.radians(angle)) * np.linalg.norm(x_axis_groundproj)])
        x_axis_camera = x_axis_camera / np.linalg.norm(x_axis_camera)

        # y_axis_camera may have two solutions, we need to use cross product to eliminate one
        # Solve[{a x + b y == 0, a^2 + b^2 == 1}, {a, b}] in mathematica, where y = (a, b, 0) and x = (i, j, k)
        i = x_axis_camera[0]
        j = x_axis_camera[1]
        y_axis_camera_soln1 = np.array([-(j / math.sqrt(i * i + j * j)), i / math.sqrt(i * i + j * j), 0])
        y_axis_camera_soln2 = -y_axis_camera_soln1

        if np.cross(x_axis_camera, y_axis_camera_soln1)[2] > 0:
            y_axis_camera = y_axis_camera_soln1
        elif np.cross(x_axis_camera, y_axis_camera_soln2)[2] > 0:
            y_axis_camera = y_axis_camera_soln2
        else:
            assert 1 > 2

        z_axis_camera = np.cross(x_axis_camera, y_axis_camera)

        x_axis_camera_list.append(x_axis_camera)
        y_axis_camera_list.append(y_axis_camera)
        z_axis_camera_list.append(z_axis_camera)

        # sanity check
        # print(x_axis_camera, np.linalg.norm(x_axis_camera))
        # print(y_axis_camera, np.linalg.norm(y_axis_camera))
        # print(z_axis_camera, np.linalg.norm(z_axis_camera))
        # print('xydot', np.dot(x_axis_camera, y_axis_camera))
        # print('yzdot', np.dot(y_axis_camera, z_axis_camera))
        # print('xzdot', np.dot(x_axis_camera, z_axis_camera))

        R = np.vstack((x_axis_camera, y_axis_camera, z_axis_camera)).T
        # print(R)

        v_camera = R.T @ v_world
        v_camera_list.append(v_camera)
        # print(v_camera)

        length = np.linalg.norm(v_camera)
        if length > 0:
            v_camera_norm = v_camera / length
        else:
            v_camera_norm = np.array([0, 0, 0])
        v_camera_norm_list.append(v_camera_norm)

    for i in range(len(framestamp)):
        if framestamp[i] >= 0:
            start = i
            break

    if plot == True:
        v_camera_list = np.array(v_camera_list)
        plt.figure('xyz in camera frame from metadata')
        plt.plot(framestamp[start:], v_camera_list[start:, 0], label='x')
        plt.plot(framestamp[start:], v_camera_list[start:, 1], label='y')
        plt.plot(framestamp[start:], v_camera_list[start:, 2], label='z')
        plt.legend()
        plt.show()

        v_camera_norm_list = np.array(v_camera_norm_list)
        plt.figure('xyz in camera frame with normalization from metadata')
        plt.plot(framestamp[start:], v_camera_norm_list[start:, 0], label='x')
        plt.plot(framestamp[start:], v_camera_norm_list[start:, 1], label='y')
        plt.plot(framestamp[start:], v_camera_norm_list[start:, 2], label='z')
        plt.legend()
        plt.show()

    ##########

    # x_axis_camera_list_by_frame = []
    # y_axis_camera_list_by_frame = []
    # z_axis_camera_list_by_frame = []
    # j = 0
    # for i in range(start, len(framestamp)):
    #     normalized_x = x_axis_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #     normalized_y = y_axis_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #     normalized_z = z_axis_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #
    #     while j < framestamp[i]:
    #         x_axis_camera_list_by_frame.append(normalized_x)
    #         y_axis_camera_list_by_frame.append(normalized_y)
    #         z_axis_camera_list_by_frame.append(normalized_z)
    #         j += 1
    #
    # return x_axis_camera_list_by_frame, y_axis_camera_list_by_frame, z_axis_camera_list_by_frame

    ##########
    if not returnVelocity:
        return v_camera_list, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list
    else:
        v_camera_norm_list = np.array(v_camera_norm_list)
        print(len())
        return v_camera_norm_list[start:, 1], v_camera_norm_list[start:,0], v_camera_norm_list[start:, 2]


def convertRotationMatrixToEulerAngle(R):
    beta = np.arcsin(-R[2, 0])
    gamma = np.arcsin(R[2, 1] / np.cos(beta))
    alpha = np.arcsin(R[1, 0] / np.cos(beta))
    return np.array([alpha, beta, gamma])


def getRPYInCameraFrame(framestamp, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list, plot=False):
    yaw_camera_list = []
    pitch_camera_list = []
    roll_camera_list = []
    for i in range(len(framestamp) - 1):
        x1_axis_camera = x_axis_camera_list[i]
        y1_axis_camera = y_axis_camera_list[i]
        z1_axis_camera = z_axis_camera_list[i]
        R_w_c1 = np.vstack((x1_axis_camera, y1_axis_camera, z1_axis_camera)).T

        x2_axis_camera = x_axis_camera_list[i + 1]
        y2_axis_camera = y_axis_camera_list[i + 1]
        z2_axis_camera = z_axis_camera_list[i + 1]
        R_w_c2 = np.vstack((x2_axis_camera, y2_axis_camera, z2_axis_camera)).T

        R_c1_c2 = np.linalg.inv(R_w_c1) @ R_w_c2

        yaw, pitch, roll = convertRotationMatrixToEulerAngle(R_c1_c2)

        yaw_camera_list.append(yaw)
        pitch_camera_list.append(pitch)
        roll_camera_list.append(roll)

    for i in range(len(framestamp)):
        if framestamp[i] >= 0:
            start = i
            break
    if plot == True:

        # yaw_camera_list = np.array(yaw_camera_list)
        # pitch_camera_list = np.array(pitch_camera_list)
        # roll_camera_list = np.array(roll_camera_list)
        # plt.figure('rpy in camera frame from metadata')
        # plt.plot(framestamp[start:-1], pitch_camera_list[start:], label='pitch')
        # plt.plot(framestamp[start:-1], yaw_camera_list[start:], label='yaw')
        # plt.plot(framestamp[start:-1], roll_camera_list[start:], label='roll')
        # plt.legend()
        # plt.show()

        yaw_rate_camera_list = [yaw_camera_list[i] / (framestamp[i + 1] - framestamp[i]) for i in
                                range(len(yaw_camera_list))]
        pitch_rate_camera_list = [pitch_camera_list[i] / (framestamp[i + 1] - framestamp[i]) for i in
                                  range(len(pitch_camera_list))]
        roll_rate_camera_list = [roll_camera_list[i] / (framestamp[i + 1] - framestamp[i]) for i in
                                 range(len(roll_camera_list))]
        yaw_rate_camera_list = np.array(yaw_rate_camera_list)
        pitch_rate_camera_list = np.array(pitch_rate_camera_list)
        roll_rate_camera_list = np.array(roll_rate_camera_list)

        # sanity check
        for i in range(len(yaw_rate_camera_list)):
            print('pitch_rate, roll_rate, yaw_rate =', pitch_rate_camera_list[i], roll_rate_camera_list[i],
                  yaw_rate_camera_list[i])
            print('diff:', yaw_rate_camera_list[i] - roll_rate_camera_list[i])

        plt.figure('rpy rate in camera frame from metadata')
        plt.plot(framestamp[start:-1], pitch_rate_camera_list[start:], label='pitch rate')
        plt.plot(framestamp[start:-1], yaw_rate_camera_list[start:], label='yaw rate')
        plt.plot(framestamp[start:-1], roll_rate_camera_list[start:], label='roll rate')
        plt.legend()
        plt.show()

        # return framestamp[start:-1], roll_rate_camera_list, pitch_rate_camera_list, yaw_rate_camera_list

    ##########

    # yaw_camera_list_by_frame = []
    # pitch_camera_list_by_frame = []
    # roll_camera_list_by_frame = []
    # j = 0
    # for i in range(start, len(framestamp)):
    #     normalized_yaw = yaw_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #     normalized_pitch = pitch_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #     normalized_roll = roll_camera_list[i - 1] / (framestamp[i] - framestamp[i - 1])
    #
    #     while j < framestamp[i]:
    #         yaw_camera_list_by_frame.append(normalized_yaw)
    #         pitch_camera_list_by_frame.append(normalized_pitch)
    #         roll_camera_list_by_frame.append(normalized_roll)
    #         j += 1

    return yaw_camera_list, pitch_camera_list, roll_camera_list

    ##########


if __name__ == '__main__':
    metadataFilePath = '/Users/fabien/Documents/amherst/fall19/cs696_paper/droneCAPTCHA/temp/metadata/DJI_0179.metadata'
    # oriFilePath = 'DJI_0179.txt'

    info = extractGPSInfo(metadataFilePath)
    timestamp, pitch, roll, yaw, vx, vy, vz = extractPitchRollYawXYZ(info)
    framestamp, timeFrameDict = timestampToFramestamp(metadataFilePath, timestamp)

    v_world_list, v_body_list, x_axis_body_list, y_axis_body_list, z_axis_body_list = convertXYZToBodyFrame(framestamp,
                                                                                                            pitch, roll,
                                                                                                            yaw, vx, vy,
                                                                                                            vz,
                                                                                                            plot=False)
    v_camera_list, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list = convertXYZFromBodyToCamera(framestamp,
                                                                                                           50.0,
                                                                                                           v_world_list,
                                                                                                           x_axis_body_list,
                                                                                                           y_axis_body_list,
                                                                                                           z_axis_body_list,
                                                                                                           plot=True)

    getRPYInCameraFrame([3800, 3900], framestamp, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list,
                        plot=False)

    # plotTrace2D(info)
    # plotTraceAnimation(info)
