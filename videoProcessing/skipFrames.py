from videoProcessor import videoProcessor
import sys
import cv2

class skipFrames(videoProcessor):
    
    def process(self, params, outputPath='./'):
        secspan = params

        newFileName = self.fileName + '__reduce_' + str(secspan)

        fourcc = cv2.VideoWriter_fourcc(*'MP4V') 
        out = cv2.VideoWriter(outputPath + newFileName + '.MP4', fourcc, self.fps, (self.width, self.height))

        frameNum = 0
        while(self.cap.isOpened()):
            # print('Processing Frame #' + str(frameNum))
            ret, frame = self.cap.read()
            if ret == False:
                break
            
            if frameNum % secspan == 0:
                out.write(frame)
                # print('ok') 
            else:
                # print('ignored')
                pass
            frameNum += 1

        out.release()

        return newFileName


if __name__ == '__main__':
    if len(sys.argv)==3:
        fileName = sys.argv[1]
        secspan = int(sys.argv[2])
        reducedVideo = skipFrames(fileName)
        reducedVideo.process(secspan)
    else:
        print('Command Formatting:\nskipFrames.py DJI_0179 3')