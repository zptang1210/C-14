import sys
import os
import shutil

current_folder_path = os.path.split(os.path.realpath(__file__))[0] + '/'
sys.path.append(current_folder_path + '../../videoProcessing')
from videoCompressor_absRes import videoCompressor
sys.path.append('../../PWCNET_ORIEXTRACTOR')
from PWCNET_ORIEXTRACTOR_FOCALLEN import PWCNET_ORIEXTRACTOR_FOCALLEN

needCompress = True
path = '../../PWCNET_ORIEXTRACTOR/videos/'

if __name__=='__main__':
    folderName = sys.argv[1]
    folderPath = './videos/' + folderName + '/'

    # compress
    if needCompress:
        newFolderPath = './videos/' + folderName + '_resized' + '/'
        if not os.path.exists(newFolderPath):
            os.mkdir(newFolderPath)
            
        files = os.listdir(folderPath)
        for file in files:
            videoName = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[-1]
            os.rename(folderPath+file, folderPath+videoName+extension.upper())

            compressor = videoCompressor(videoName, inputPath=folderPath)
            videoName = compressor.process((144, 256), outputPath=newFolderPath)
        
        folderPath = newFolderPath

    # copy to PWCNET_ORIEXTRACTOR
    files = os.listdir(folderPath)
    for file in files:
        videoName = os.path.splitext(file)[0]
        extension = os.path.splitext(file)[-1]
        shutil.copyfile(folderPath+videoName+extension, path+videoName+extension.upper())
    
    # PWC-NET and cameraMotion
    files = os.listdir(folderPath)

    path_backup = os.getcwd() # backup the current working directory, and will restore by the end of the program
    os.chdir(current_folder_path + '../../PWCNET_ORIEXTRACTOR/')
    for file in files:
        videoName = os.path.splitext(file)[0]
        extension = os.path.splitext(file)[-1]

        cap = cv2.VideoCapture('./videos/' + videoName + '.MP4')
        frameStart = 0
        frameEnd = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 2 # Notice: we need to minus 1 to guaranttee the last frame exists. See the comment above the function for detail!
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        PWCNET_ORIEXTRACTOR_FOCALLEN(videoName, frameStart, frameEnd, height, width)     

    os.chdir(path_backup)