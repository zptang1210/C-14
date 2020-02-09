import re
import numpy as np

class parseComputedMotion(object):

    def __init__(self, oriFilePath):
        self.filePath = oriFilePath
    

    def parse(self):
        with open(self.filePath, 'r') as fid:
            orientationInfo = fid.readlines()

        totalFrameNum = len(orientationInfo) // 3 - 1

        frame, rotationABC, translationUVW = self.__readInfo(orientationInfo, totalFrameNum)

        return frame, rotationABC, translationUVW


    def __readInfo(self, orientationInfo, totalFrameNum):
        frame = []
        rotationABC = []
        translationUVW = []
        i = 0
        while i <= totalFrameNum:
            # frame number
            frameNum = self.__getFrameNumInLine(orientationInfo[i*3+0])
            frame.append(frameNum)

            # rotation_ABC = [A, B, C]   camera rotation around x,y and z axis
            rotation = self.__getLineInfo('rotation:', orientationInfo[i*3+1])
            # print('rotation:', rotation)
            rotationABC.append(rotation)

            # translation_UVW = [U, V, W]   translation in the current coord
            translation = self.__getLineInfo('translation:', orientationInfo[i*3+2])
            # print('translation:', translation)
            translationUVW.append(translation)

            i += 1
        
        return np.array(frame), -np.array(rotationABC), np.array(translationUVW) # flip the sign of rotation


    def __getLineInfo(self, prompt, line):
        tmp = line[len(prompt)+2: -2].split(',')
        X, Y, Z = float(tmp[0]), float(tmp[1]), float(tmp[2])
        return (X, Y, Z)

    def __getFrameNumInLine(self, line):
        matchObj = re.match(r'frame (\d+):', line)
        return int(matchObj.group(1))


if __name__=='__main__':
    parser = parseComputedMotion('DJI_0179.txt')
    frame, ori, _ = parser.parse()
    print(frame)
    print(ori)