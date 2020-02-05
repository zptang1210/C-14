import numpy as np
import cv2

cap = cv2.VideoCapture('example.MP4')

frameNum = 0
while(cap.isOpened()):
    print('Saving Frame #' + str(frameNum))
    ret, frame = cap.read()
    if ret == False:
        break
    cv2.imwrite('Frame' + str(frameNum) + '.png', frame) 
    print('ok') 
    frameNum += 1

cap.release()