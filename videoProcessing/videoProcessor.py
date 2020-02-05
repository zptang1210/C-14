from abc import abstractmethod
import math
import numpy as np
import cv2

class videoProcessor(object):

    def __init__(self, videoFileName, inputPath='./'):
        self.fileName = videoFileName
        self.inputPath = inputPath

        # open the video and extract some basic information
        self.cap = cv2.VideoCapture(self.inputPath + self.fileName + '.MP4') # MP4 format by default

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = round(self.cap.get(cv2.CAP_PROP_FPS))


    @abstractmethod
    def process(self, params, outputPath):
        pass
    

    def __del__(self):
        self.cap.release()

