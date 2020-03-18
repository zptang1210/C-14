from videoProcessor import videoProcessor
import sys
import cv2

class videoCompressor(videoProcessor):
    
    def process(self, params, outputPath='./'):
        newHeight, newWidth = params

        newFileName = self.fileName + '__resized_' + str(newHeight) + '_' + str(newWidth)

        fourcc = cv2.VideoWriter_fourcc(*'MP4V') 
        out = cv2.VideoWriter(outputPath + newFileName + '.MP4', fourcc, self.fps, (newWidth, newHeight))

        frameNum = 0
        while(self.cap.isOpened()):
            # print('Saving Frame #' + str(frameNum))
            ret, frame = self.cap.read()
            if ret == False:
                break
            
            height, width, _ = frame.shape
            frame_compressed = cv2.resize(frame, (newWidth, newHeight), interpolation=cv2.INTER_AREA)

            out.write(frame_compressed)
            # print('ok') 
            frameNum += 1 

        out.release()
        
        return newFileName

if __name__ == '__main__':
    if len(sys.argv)==4:
        fileName = sys.argv[1]
        height = int(sys.argv[2])
        width = int(sys.argv[3])

        compressor = videoCompressor(fileName)
        compressor.process(scale)
    else:
        print('Command Formatting:\nvideoCompressor_absRes.py DJI_0179 144 256')

    # # Another way to use this video processor
    # compressor = videoCompressor('DJI_0156', inputPath='../')
    # compressor.process((144, 256), outputPath='../')
