import numpy as np

class parseComputedMotion(object):

    def __init__(self, oriFilePath):
        self.filePath = oriFilePath
    

    def parse(self):
        with open(self.filePath, 'r') as fid:
            orientationInfo = fid.readlines()

        endFrameNum = len(orientationInfo) // 3 - 1

        rotationABC, translationUVW = self.__readInfo(orientationInfo, endFrameNum)

        return rotationABC, translationUVW


    def __readInfo(self, orientationInfo, endFrameNum):
        rotationABC = []
        translationUVW = []
        frameNum = 0
        while frameNum <= endFrameNum:
            # print('Frame', frameNum)

            # rotation_ABC = [A, B, C]   camera rotation around x,y and z axis
            rotation = self.__getLineInfo('rotation:', orientationInfo[frameNum*3+1])
            # print('rotation:', rotation)
            rotationABC.append(rotation)

            # translation_UVW = [U, V, W]   translation in the current coord
            translation = self.__getLineInfo('translation:', orientationInfo[frameNum*3+2])
            # print('translation:', translation)
            translationUVW.append(translation)

            frameNum += 1
        
        return -np.array(rotationABC), np.array(translationUVW) # flip the sign of rotation


    def __getLineInfo(self, prompt, line):
        tmp = line[len(prompt)+2: -2].split(',')
        X, Y, Z = float(tmp[0]), float(tmp[1]), float(tmp[2])
        return (X, Y, Z)



if __name__=='__main__':
    parser = parseComputedMotion('DJI_0179_patch_74_reduced_4.txt')
    ori, _ = parser.parse()
    print(ori)