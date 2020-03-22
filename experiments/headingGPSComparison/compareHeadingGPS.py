import sys
import math
from geographiclib.geodesic import Geodesic
sys.path.append('./utils')
from parseMetadata_new_simplified import parseMetadata
from motion import motion
from program import program


class metadataAngleExtractor(object):

    def __init__(self, metadataFilePath):
        metadataParser = parseMetadata(metadataFilePath)
        motionClass, (centerLongitude, centerLatitude), self.hotpointCmdList = metadataParser.parse()
        self.centerPoint = (centerLatitude, centerLongitude)
        self.absoluteAngles = motionClass.motionAngle
        self.isClockwise = motionClass.clockwiseDirect
        self.plan = program(list(zip(motionClass.motionAngle, motionClass.clockwiseDirect)))


    def getAbsoluteAngles(self):
        return self.absoluteAngles

    def getIdeaAngles(self):
        return self.plan.travelledAngles

    
    def getHeadingAngles(self, verbose=False):
        headingAngles = []
        for i in range(self.plan.numAngles):
            _, _, _, _, yaw, _, _, _ = self.__extractMotionFromCmd(self.hotpointCmdList[i])
            startYaw = yaw[0]
            endYaw = yaw[-1]
            if verbose: print(startYaw, endYaw, self.plan.isClockwise[i])
            headingAngles.append(program.getTravelledAngles(startYaw, endYaw, self.plan.isClockwise[i]))
        
        if verbose: print(headingAngles)
        return headingAngles


    def getGPSAngles(self, verbose=False):
        GPSAngles = []
        for i in range(self.plan.numAngles):
            _, GPS, _, _, yaw, _, _, _ = self.__extractMotionFromCmd(self.hotpointCmdList[i])

            startGPS = GPS[0]
            geodict1 = Geodesic.WGS84.Inverse(startGPS[0], startGPS[1], self.centerPoint[0], self.centerPoint[1])
            if verbose: print('start', 'geodict1', geodict1)
            startAzimuth = self.__convertToStandardAngleMeasurement(geodict1['azi2'])

            endGPS = GPS[-1]
            geodict2 = Geodesic.WGS84.Inverse(endGPS[0], endGPS[1], self.centerPoint[0], self.centerPoint[1])
            if verbose: print('end', 'geodict1', geodict2)
            endAzimuth = self.__convertToStandardAngleMeasurement(geodict2['azi2'])

            if verbose:
                print('start')
                print(startAzimuth, yaw[0])

                print('end')
                print(endAzimuth, yaw[-1])

            GPSAngles.append(program.getTravelledAngles(startAzimuth, endAzimuth, self.plan.isClockwise[i]))

        if verbose: print(GPSAngles)
        return GPSAngles


    def __extractMotionFromCmd(self, cmd):
        rawMotion = cmd.interStatus
        timestamp_list, GPS_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list = [], [], [], [], [], [], [], []
        for rawStr in rawMotion:
            # print(rawStr)
            splittedStr = rawStr.split(' ')
            timestamp = int(splittedStr[0])
            info = splittedStr[1].split(',')

            [lat_str, lon_str, alt_str, pit_str, rol_str, yaw_str,
             vx_str, vy_str, vz_str] = info

            timestamp_list.append(timestamp)
            GPS_list.append((float(lat_str), float(lon_str)))
            roll_NED_list.append(self.__convertToStandardAngleMeasurement(float(rol_str)))
            pitch_NED_list.append(self.__convertToStandardAngleMeasurement(float(pit_str)))
            yaw_NED_list.append(self.__convertToStandardAngleMeasurement(float(yaw_str)))
            vx_NED_list.append(float(vx_str))
            vy_NED_list.append(float(vy_str))
            vz_NED_list.append(float(vz_str))

        realMotion_NED = timestamp_list, GPS_list, roll_NED_list, pitch_NED_list, yaw_NED_list, vx_NED_list, vy_NED_list, vz_NED_list
        return realMotion_NED


    def __convertToStandardAngleMeasurement(self, angle):
        return 360+angle if angle<0 else angle


def getAnglesForMetadata(metadataFile, folderPath='./metadata/', verbose=False):
    extractor = metadataAngleExtractor(folderPath + metadataFile)
    ideaAngles = extractor.getIdeaAngles()
    headingAngles = extractor.getHeadingAngles(verbose)
    GPSAngles = extractor.getGPSAngles(verbose)
    absoluteAngles = extractor.getAbsoluteAngles()

    if verbose:
        print('idea:', ideaAngles)
        print('heading', headingAngles)
        print('GPS', GPSAngles)

    return ideaAngles, headingAngles, GPSAngles, absoluteAngles


if __name__ == '__main__':
    # 720p
    data0403 = ('DJI_0403', 'DJI_0403_corrected', ((214, None), (57, False), (248, False)), '720p')
    data0410 = ('DJI_0410', 'DJI_0410', ((214, None), (57, False), (248, False)), '720p')
    data0411 = ('DJI_0411', 'DJI_0411', ((173, None), (65, False), (205, True)), '720p')
    data0412 = ('DJI_0412', 'DJI_0412_corrected', ((173, None), (65, False), (205, True)), '720p')

    data0404 = ('DJI_0404', 'DJI_0404_corrected', ((43, None), (10, False), (179, False)), '720p')

    data0400 = ('DJI_0400', 'DJI_0400', ((125, None), (39, False), (344, True)), '720p')
    data0402 = ('DJI_0402', 'DJI_0402', ((56, None), (347, True), (183, False)), '720p')

    # 4k
    data0460 = ('DJI_0460', 'DJI_0460_corrected', ((333, None), (182, True), (22, True)), '4k')
    data0459 = ('DJI_0459', 'DJI_0459_corrected', ((50, None), (142, True), (249, False)), '4k')

    data0443 = ('DJI_0443', 'DJI_0443', ((63, None), (346, False), (128, False)), '4k')
    data0439 = ('DJI_0439', 'DJI_0439', ((125, None), (177, True), (114, False)), '4k')

    data0447 = ('DJI_0447', 'DJI_0447_corrected', ((7, None), (217, True), (327, True)), '4k')

    data0494 = ('DJI_0494', 'DJI_0494', ((93, None), (321, True), (337, False), (228, True), (288, True)), '4k')
    data0495 = ('DJI_0495', 'DJI_0495', ((244, None), (173, False), (221, True), (311, True), (277, True)), '4k')
    data0496 = ('DJI_0496', 'DJI_0496', ((186, None), (53, False), (80, False), (137, False), (305, False)), '4k')

    data0488 = ('DJI_0488', 'DJI_0488', ((286, None), (215, True), (310, True), (184, True), (59, False)), '4k')
    data0489 = ('DJI_0489', 'DJI_0489', ((78, None), (194, True), (272, True), (135, True), (315, False)), '4k')
    data0490 = ('DJI_0490', 'DJI_0490', ((307, None), (147, True), (77, False), (28, False), (220, False)), '4k')
    data0491 = ('DJI_0491', 'DJI_0491', ((267, None), (89, True), (143, True), (41, True), (301, True)), '4k')

    data0508 = ('DJI_0508', 'DJI_0508', ((104, None), (289, True), (292, False), (114, False), (23, True)), '4k')
    data0504 = ('DJI_0504', 'DJI_0504', ((161, None), (29, True), (122, False), (249, True), (328, False)), '4k')

    data0498 = ('DJI_0498', 'DJI_0498', ((176, None), (216, True), (240, False), (77, False), (4, True)), '4k')
    data0497 = ('DJI_0497', 'DJI_0497', ((346, None), (80, True), (176, True), (196, False), (171, True)), '4k')

    data0502 = ('DJI_0502', 'DJI_0502', ((174, None), (48, False), (94, True), (240, False), (34, False)), '4k')
    data0501 = ('DJI_0501', 'DJI_0501', ((85, None), (53, False), (24, False), (56, False), (209, False)), '4k')
    data0500 = ('DJI_0500', 'DJI_0500', ((32, None), (13, True), (197, False), (258, True), (42, False)), '4k')

    dataset = [data0403, data0410, data0411, data0412, data0404, data0400, data0402, 
            data0460, data0459, data0443, data0439, data0447, data0494, data0495, data0496, 
            data0488, data0489, data0490, data0491, data0508, data0498, data0497, 
            data0502, data0501, data0500, data0504]

    fout = open('output.txt', 'w')

    for data in dataset:
        videoName, metadataName, plan, resolution = data
        ideaAngles, headingAngles, GPSAngles, absoluteAngles = getAnglesForMetadata(metadataName+'.metadata')

        numAngles = len(plan)-1
        print(videoName, numAngles, file=fout)
        print('ideaAngles', ideaAngles[:numAngles], file=fout)
        print('headingAngles', headingAngles[:numAngles], file=fout)
        print('GPSAngles', GPSAngles[:numAngles], file=fout)
        print(file=fout)

    fout.close()
