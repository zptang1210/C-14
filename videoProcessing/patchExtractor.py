from videoProcessor import videoProcessor
import sys
import cv2

class patchExtractor(videoProcessor):
    
    def process(self, params, outputPath='./'):
        patchWidth, patchHeight = params

        newFileName = self.fileName + '__patch_' + str(patchWidth) + '_' + str(patchHeight)

        fourcc = cv2.VideoWriter_fourcc(*'MP4V') 
        out = cv2.VideoWriter(outputPath + newFileName + '.MP4', fourcc, self.fps, (patchWidth, patchHeight))

        heightLeftBound = self.height//2-patchHeight//2
        heightRightBound = heightLeftBound + patchHeight
        widthLeftBound = self.width//2-patchWidth//2
        widthRightBound = widthLeftBound + patchWidth

        frameNum = 0
        while(self.cap.isOpened()):
            # print('Saving Frame #' + str(frameNum))
            ret, frame = self.cap.read()
            if ret == False:
                break
            
            frame_patch = frame[heightLeftBound : heightRightBound,\
                                widthLeftBound : widthRightBound]
            # print(frame_patch.shape)

            out.write(frame_patch)
            # print('ok') 
            frameNum += 1

        out.release()

        return newFileName


if __name__ == '__main__':
    if len(sys.argv)==4:
        fileName = sys.argv[1]
        patchWidth = int(sys.argv[2])
        patchHeight = int(sys.argv[3])
        if patchWidth%2==0 and patchHeight%2==0:
            extractor = patchExtractor(fileName)
            extractor.process((patchWidth, patchHeight))
        else:
            print('Must be even number!')
    else:
        print('Command Formatting:\npatchExtractor.py DJI_0179 100 100')